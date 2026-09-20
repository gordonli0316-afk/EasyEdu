"""Environment helpers for model backend selection."""
import os


def get_default_model_backend() -> str:
    """Pick the LLM backend from the environment.

    Resolution order:
      1. ``EASYEDU_LLM_BACKEND`` when set explicitly (always wins)
      2. ``deepseek`` when ``DEEPSEEK_API_KEY`` is configured
      3. ``tongyi`` when ``TONGYI_API_KEY`` is configured
      4. ``local_vllm`` (a self-hosted OpenAI-compatible server)

    A deployment that simply has a provider key configured therefore works with no
    other settings, while a deployment with no key at all still starts normally:
    the reachability probe in ``src/agents/llm/health.py`` then drops it to demo
    mode. The key value itself is never logged or returned.
    """
    explicit = os.getenv("EASYEDU_LLM_BACKEND", "").strip()
    if explicit:
        return explicit
    if os.getenv("DEEPSEEK_API_KEY", "").strip():
        return "deepseek"
    if os.getenv("TONGYI_API_KEY", "").strip():
        return "tongyi"
    return "local_vllm"


def backend_source() -> str:
    """Why this backend was chosen, for logs and the status endpoint."""
    if os.getenv("EASYEDU_LLM_BACKEND", "").strip():
        return "EASYEDU_LLM_BACKEND"
    if os.getenv("DEEPSEEK_API_KEY", "").strip():
        return "DEEPSEEK_API_KEY configured"
    if os.getenv("TONGYI_API_KEY", "").strip():
        return "TONGYI_API_KEY configured"
    return "default"
