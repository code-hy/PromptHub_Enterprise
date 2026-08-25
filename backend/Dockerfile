FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY app ./app
COPY README.md ./

RUN uv sync --frozen 2>/dev/null || uv sync

EXPOSE 8000

# Render free-tier sets $PORT=10000; local dev uses 8010. Use $PORT if present.
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
