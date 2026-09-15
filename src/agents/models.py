# 模型工厂。默认给一个连本地 vLLM 的客户端；开发时也能切到 deepseek/tongyi 兜底。
from typing import List, Optional

from langchain_core.messages import BaseMessage

from src.agents.llm.client import LLMClient, get_client


def get_llm(model_type: str = "local_vllm", **kwargs) -> LLMClient:
    return get_client(model_type=model_type)


async def stream_or_chat(
    client: LLMClient,
    messages: List[BaseMessage],
    node: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """流式优先：拿得到 LangGraph 的 stream writer 就逐字推送，否则一次性返回。

    返回完整文本（无论是否流式），方便上层把它存进对话历史。
    node 用于前端区分是哪个 agent（teacher_agent / student_agent）。
    """
    try:
        from langgraph.config import get_stream_writer
        writer = get_stream_writer()
    except Exception:
        writer = None

    if writer is None:
        # 没有流式上下文（如直接 ainvoke），退回一次性返回
        return await client.chat(messages, temperature=temperature, max_tokens=max_tokens)

    full = ""
    try:
        async for token in client.chat_stream(messages, temperature=temperature, max_tokens=max_tokens):
            full += token
            writer({"node": node, "content": token})
    except Exception:
        # 流式中途失败：若还没吐过内容，退回一次性返回
        pass

    if not full:
        full = await client.chat(messages, temperature=temperature, max_tokens=max_tokens)
        writer({"node": node, "content": full})

    return full
