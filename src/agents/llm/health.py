"""Which response engine is EasyEdu actually using right now?

A public deployment may have no GPU and no API key. Rather than failing, EasyEdu
falls back to the deterministic demo backend (see src/agents/demo.py). This module
is the single place that decides between the two and caches the answer, so the
web layer can report it honestly to the user.
"""
import logging
import os

import httpx

from src.agents.demo import is_demo_mode
from src.agents.llm.config import get_llm_config

logger = logging.getLogger(__name__)

_reachable: bool | None = None


def _probe() -> bool:
    try:
        config = get_llm_config()
    except Exception as exc:  # unsupported backend name
        logger.warning("LLM backend not configured (%s); using demo mode", exc)
        return False

    if config.backend in ("deepseek", "tongyi") and not config.api_key:
        logger.warning("No API key set for backend %s; using demo mode", config.backend)
        return False

    url = config.base_url.rstrip("/") + "/models"
    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=float(os.getenv("EASYEDU_LLM_PROBE_TIMEOUT", "4")),
        )
        # Any response below 500 means a server is answering, even if it dislikes
        # the route or the key (401/404 are still evidence of a live endpoint).
        return response.status_code < 500
    except Exception as exc:
        logger.warning("LLM endpoint %s unreachable (%s); using demo mode", config.base_url, exc)
        return False


def llm_reachable(force: bool = False) -> bool:
    global _reachable
    if _reachable is None or force:
        _reachable = _probe()
    return _reachable


def active_mode() -> str:
    """Return "demo" or "live"."""
    if is_demo_mode():
        return "demo"
    return "live" if llm_reachable() else "demo"


def reset_cache() -> None:
    global _reachable
    _reachable = None
