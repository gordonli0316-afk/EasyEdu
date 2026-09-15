#!/bin/bash
# EasyEdu web server. Port configurable via EASYEDU_WEB_PORT (AutoDL: 6006).
set -euo pipefail

PORT="${EASYEDU_WEB_PORT:-6006}"

# Prefer local venv python if present (local dev); else system python (AutoDL)
PY="python"
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; fi

echo "=========================================="
echo "EasyEdu server on port ${PORT}..."
echo "Python: ${PY} | Model backend: ${EASYEDU_LLM_BACKEND:-local_vllm}"
echo "=========================================="

"$PY" -m uvicorn web.main:app --host 0.0.0.0 --port "${PORT}" --workers 1

# AutoDL: map port 6006 via 自定义服务, or use  ssh -L ${PORT}:127.0.0.1:${PORT}
# Local:  open http://127.0.0.1:${PORT}
