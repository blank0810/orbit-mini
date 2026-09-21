# Builder installs dependencies; the fresh runtime copies only the venv and app, leaving build tools behind.
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/app/.venv
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen || uv sync --no-dev

FROM python:3.12-slim AS runner

RUN groupadd --gid 10001 orbit && useradd --uid 10001 --gid 10001 orbit
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
RUN chown -R orbit:orbit /app
USER orbit
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=6 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready', timeout=2).status==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
