FROM python:3.12-slim AS runtime

ARG APP_VERSION=1.0.0
LABEL org.opencontainers.image.title="AfyaPlus Service Platform" \
      org.opencontainers.image.version="${APP_VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

# Dependency metadata is copied first so source changes reuse the dependency layer.
COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt \
    && addgroup --system afyaplus \
    && adduser --system --ingroup afyaplus afyaplus

COPY service ./service
COPY agent ./agent
COPY mcp_server ./mcp_server

USER afyaplus
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8000"]

