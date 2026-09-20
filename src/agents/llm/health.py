"""Which response engine is EasyEdu actually using right now?

A public deployment may have no GPU and no API key, or the configured provider may
be down, out of credit, rate-limited, or reject the key. Rather than failing, EasyEdu
falls back to the deterministic demo backend (see src/agents/demo.py). This module is
the single place that decides between the two and caches the answer, so the web layer
can report it honestly.

No API key material ever passes through this module's logs or return values.
"""
import logging
import os

import httpx

from src.agents.demo import is_demo_mode
from src.agents.llm.config import get_llm_config
from src.agents.llm.env import backend_source

logger = logging.getLogger(__name__)

_reachable: bool | None = None
_reason: str = "not probed yet"

# Status codes that still prove a usable endpoint:
#   2xx        - healthy
#   404        - some gateways do not expose /models but do serve /chat/completions
#   429        - the credential is accepted, we are only being throttled
_REACHABLE_STATUS = lambda code: (200 <= code < 300) or code in (404, 429)  # noqa: E731


def _probe() -> tuple[bool, str]:
    try:
        config = get_llm_config()
    except Exception:
        # Unsupported backend name; nothing secret is in the message.
        logger.warning("Unsupported LLM backend configured; using demo mode")
        return False, "model backend not configured"

    if config.backend in ("deepseek", "tongyi") and not config.api_key:
        logger.warning("Backend %s selected but no API key is set; using demo mode", config.backend)
        return False, "no model key configured"

    url = config.base_url.rstrip("/") + "/models"
    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=float(os.getenv("EASYEDU_LLM_PROBE_TIMEOUT", "5")),
        )
    except Exception:
        # Deliberately not logging the exception text: it can echo request details.
        logger.warning("LLM endpoint for backend %s is unreachable", config.backend)
        return False, "model unreachable"

    if _REACHABLE_STATUS(response.status_code):
        logger.info("LLM backend %s is reachable (%s)", config.backend, backend_source())
        return True, "model connected"

    status = response.status_code
    # 401/402/403 mean the key was rejected, has no balance, or lacks permission.
    # Anything else (5xx, unexpected 4xx) is simply the provider being unavailable.
    if status in (401, 402, 403):
        logger.warning(
            "LLM backend %s rejected the credential (HTTP %s); using demo mode",
            config.backend,
            status,
        )
        return False, "model credentials rejected"

    logger.warning(
        "LLM backend %s is not serving requests (HTTP %s); using demo mode",
        config.backend,
        status,
    )
    return False, "model unavailable"


def llm_reachable(force: bool = False) -> bool:
    global _reachable, _reason
    if _reachable is None or force:
        _reachable, _reason = _probe()
    return _reachable


def mark_unavailable(reason: str = "model unavailable") -> None:
    """Demote this process to demo mode after a live call failed.

    Called from the agents when a real request fails mid-flight (bad key, no credit,
    429, 5xx, timeout). Caching the failure stops the next visitor from waiting on a
    provider we already know is not answering.
    """
    global _reachable, _reason
    if _reachable is not False:
        logger.warning("Switching to demo mode: %s", reason)
    _reachable = False
    _reason = reason


def active_mode() -> str:
    """Return "demo" or "live"."""
    if is_demo_mode():
        return "demo"
    return "live" if llm_reachable() else "demo"


def mode_reason() -> str:
    """Short, non-technical explanation of the current mode (safe to show/log)."""
    if is_demo_mode():
        return "demo mode requested"
    llm_reachable()
    return _reason


def reset_cache() -> None:
    global _reachable, _reason
    _reachable = None
    _reason = "not probed yet"
