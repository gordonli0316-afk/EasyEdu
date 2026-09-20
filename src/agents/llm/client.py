"""我们自己的 LLM 客户端：httpx 直连 OpenAI 兼容端点，不套 LangChain 的模型封装。"""
import json
import logging
import os
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar

import httpx
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from .config import LLMConfig, get_llm_config
from .json_utils import parse_and_validate

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMUnavailable(RuntimeError):
    """The configured model provider could not serve the request.

    Raised for connection failures, timeouts, rate limits and 5xx/4xx responses so
    that callers can fall back to EasyEdu's built-in reference answers without ever
    surfacing a raw provider error to the visitor.
    """


def _timeout(read_seconds: float) -> httpx.Timeout:
    """Bound the connect phase hard: a dead provider should fail fast, not hang."""
    return httpx.Timeout(
        connect=float(os.getenv("EASYEDU_LLM_CONNECT_TIMEOUT", "5")),
        read=read_seconds,
        write=30.0,
        pool=5.0,
    )

# 复用一个进程级 httpx 客户端，避免每次请求都新建连接（连接池 + keep-alive）。
_shared_client: Optional[httpx.AsyncClient] = None


def _http() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient()
    return _shared_client


def messages_to_api(messages: List[BaseMessage]) -> List[Dict[str, str]]:
    """Convert LangChain messages to OpenAI chat format."""
    out: List[Dict[str, str]] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": str(m.content)})
        elif isinstance(m, AIMessage):
            out.append({"role": "assistant", "content": str(m.content)})
        elif isinstance(m, SystemMessage):
            out.append({"role": "system", "content": str(m.content)})
        elif hasattr(m, "type") and m.type == "human":
            out.append({"role": "user", "content": str(m.content)})
        elif hasattr(m, "type") and m.type == "ai":
            out.append({"role": "assistant", "content": str(m.content)})
        else:
            out.append({"role": "user", "content": str(m.content)})
    return out


class LLMClient:
    """Async client for self-hosted or fallback commercial LLM APIs."""

    def __init__(self, config: Optional[LLMConfig] = None, model_type: Optional[str] = None):
        self.config = config or get_llm_config(model_type)

    async def chat(
        self,
        messages: List[Dict[str, str]] | List[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if messages and isinstance(messages[0], BaseMessage):
            api_messages = messages_to_api(messages)
        else:
            api_messages = messages

        payload = {
            "model": self.config.model,
            "messages": api_messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
        }

        data = await self._post_chat(payload)
        return self._extract_content(data)

    async def chat_json(
        self,
        messages: List[Dict[str, str]] | List[BaseMessage],
        schema_model: Type[T],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> T:
        """Request JSON output; retry once with a stricter reminder on parse failure."""
        if messages and isinstance(messages[0], BaseMessage):
            api_messages = messages_to_api(messages)
        else:
            api_messages = list(messages)

        text = await self.chat(api_messages, temperature=temperature, max_tokens=max_tokens)
        parsed = parse_and_validate(text, schema_model)
        if parsed is not None:
            return parsed

        logger.warning("JSON parse failed, retrying with strict JSON reminder")
        retry_messages = api_messages + [
            {
                "role": "user",
                "content": (
                    "Your previous response was not valid JSON. "
                    "Reply with ONLY a single JSON object matching the required schema. "
                    "No markdown, no explanation."
                ),
            }
        ]
        text2 = await self.chat(retry_messages, temperature=0.3, max_tokens=max_tokens)
        parsed2 = parse_and_validate(text2, schema_model)
        if parsed2 is not None:
            return parsed2

        # Log the unusable output for debugging, but never surface model text (or any
        # provider detail) as an error the visitor could see.
        logger.warning("Model returned unusable JSON for %s", schema_model.__name__)
        raise LLMUnavailable("model returned an unusable structured response")

    async def chat_stream(
        self,
        messages: List[Dict[str, str]] | List[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """逐 token 流式返回（OpenAI 兼容 SSE）。失败时抛错，调用方自行兜底。"""
        if messages and isinstance(messages[0], BaseMessage):
            api_messages = messages_to_api(messages)
        else:
            api_messages = list(messages)

        payload = {
            "model": self.config.model,
            "messages": api_messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
            "stream": True,
        }
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with _http().stream(
                "POST", url, json=payload, headers=headers, timeout=_timeout(self.config.timeout)
            ) as resp:
                if resp.status_code >= 400:
                    raise LLMUnavailable(f"model provider returned HTTP {resp.status_code}")
                async for chunk in self._iter_sse(resp):
                    yield chunk
            return
        except LLMUnavailable:
            raise
        except Exception as exc:
            raise LLMUnavailable("could not reach the model provider") from exc

    async def _iter_sse(self, resp) -> AsyncIterator[str]:
        """Parse an OpenAI-compatible SSE stream into content deltas."""
        async for line in resp.aiter_lines():
            if not line or not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = obj.get("choices") or []
            if not choices:
                continue
            delta = (choices[0].get("delta") or {}).get("content")
            if delta:
                yield delta

    async def _post_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        attempts = max(1, self.config.max_retries + 1)
        last_status: Optional[int] = None
        for attempt in range(attempts):
            try:
                resp = await _http().post(
                    url, json=payload, headers=headers, timeout=_timeout(self.config.timeout)
                )
            except Exception:
                # Connection error / timeout: transient, worth one more try.
                last_status = None
                logger.warning(
                    "LLM request attempt %s/%s could not reach the provider", attempt + 1, attempts
                )
                continue

            if 200 <= resp.status_code < 300:
                try:
                    return resp.json()
                except Exception as exc:
                    raise LLMUnavailable("model provider returned an unreadable response") from exc

            last_status = resp.status_code
            # 4xx (bad key, no balance, bad request) will not fix itself: fail fast.
            if resp.status_code < 500 and resp.status_code != 429:
                logger.warning("LLM provider rejected the request with HTTP %s", resp.status_code)
                raise LLMUnavailable(f"model provider returned HTTP {resp.status_code}")
            logger.warning(
                "LLM request attempt %s/%s got HTTP %s", attempt + 1, attempts, resp.status_code
            )

        raise LLMUnavailable(
            "model provider unavailable"
            + (f" (last HTTP {last_status})" if last_status else "")
        )

    def _extract_content(self, data: Dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise LLMUnavailable("model provider returned an empty response")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if content is None:
            raise LLMUnavailable("model provider returned an empty message")
        return str(content).strip()


def get_client(model_type: Optional[str] = None) -> LLMClient:
    """Factory for EasyEdu LLM client."""
    return LLMClient(model_type=model_type)
