#!/bin/bash
# EasyEdu web server (local development and generic hosts).
# Port resolution: $PORT (set by most hosting platforms) -> $EASYEDU_WEB_PORT -> 8000
set -euo pipefail

PORT="${PORT:-${EASYEDU_WEB_PORT:-8000}}"

# Prefer local venv python if present (local dev); else system python
PY="python3"
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; elif command -v python >/dev/null 2>&1; then PY="python"; fi

echo "=========================================="
echo "EasyEdu server on port ${PORT}"
echo "Python: ${PY}"
echo "Response engine: ${EASYEDU_LLM_BACKEND:-auto-detect (falls back to demo mode)}"
echo "=========================================="

exec "$PY" -m uvicorn web.main:app --host 0.0.0.0 --port "${PORT}" --workers 1

# Local:  open http://127.0.0.1:${PORT}
# GPU box (AutoDL): map the port via 自定义服务, or use ssh -L ${PORT}:127.0.0.1:${PORT}
