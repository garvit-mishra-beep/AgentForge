FROM python:3.11-slim AS builder

WORKDIR /build
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

RUN groupadd -r agentforge && useradd -r -g agentforge -m -d /app agentforge

WORKDIR /app
COPY --from=builder /root/.local /home/agentforge/.local
ENV PATH=/home/agentforge/.local/bin:$PATH

COPY apps/api/ .

RUN chown -R agentforge:agentforge /app

USER agentforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
