# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.12-slim-trixie
ARG UV_VERSION=0.12.3

# A stage of its own because --from does not expand build args.
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM ${PYTHON_IMAGE} AS builder
COPY --from=uv /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# pyproject.toml has no [build-system], so uv treats this as a virtual project:
# only the dependencies are installed, and the manifest plus lockfile are the
# entire input. Keeping the source out of this layer keeps it cached across
# code changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project


FROM ${PYTHON_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=3000

RUN groupadd --system --gid 1001 app \
 && useradd --system --uid 1001 --gid app --home-dir /app app

WORKDIR /app

COPY --chown=app:app . /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv

USER app
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import os,sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','3000'), timeout=3).status == 200 else 1)"]

# --workers 1 is load-bearing: wsgi.py kicks off the public-channel auto-join
# sweep at import, and gunicorn imports the app once per worker.
CMD ["sh", "-c", "exec gunicorn wsgi:application \
  --bind 0.0.0.0:${PORT:-3000} \
  --worker-class gthread \
  --workers 1 \
  --threads 8 \
  --timeout 30 \
  --graceful-timeout 60 \
  --keep-alive 65 \
  --no-control-socket \
  --forwarded-allow-ips '*' \
  --access-logfile - \
  --error-logfile - \
  --log-level info"]
