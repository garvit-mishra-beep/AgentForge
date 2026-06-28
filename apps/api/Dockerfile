FROM python:3.11-slim AS builder
WORKDIR /app
# Install dependencies
COPY apps/api/requirements.txt ./apps/api/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./apps/api/requirements.txt
# Copy the application code
COPY . .
FROM python:3.11-slim
# Create non-root user
RUN groupadd -r agentforge && useradd -r -g agentforge -m -d /app agentforge
WORKDIR /app/apps/api
# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app
# Change ownership to non-root user
RUN chown -R agentforge:agentforge /app
USER agentforge
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]