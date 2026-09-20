FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Runtime dependencies first so the layer is cached between code changes
COPY requirements.txt ./
RUN pip install --no-cache-dir --timeout=100 -r requirements.txt

# Application code
COPY . /app/

# Run as a non-root user
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data/courses /app/data/uploads /app/data/exports \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Hosting platforms set $PORT; 8000 is the local default.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/healthz').read()"

CMD ["sh", "-c", "python -m uvicorn web.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
