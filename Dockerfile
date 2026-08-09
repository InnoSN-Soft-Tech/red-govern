FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE.md NOTICE COMMERCIAL_LICENSE.md TRADEMARKS.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir ".[remote]" \
    && addgroup --system redgovern \
    && adduser --system --ingroup redgovern --no-create-home redgovern

USER redgovern

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/v1/meta', timeout=3).read()" || exit 1

CMD ["python", "-m", "uvicorn", "red_govern.remote_api:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header", "--no-access-log", "--workers", "1"]
