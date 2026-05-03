ARG IMAGE=python:3.10-slim
FROM ${IMAGE}

ENV UV_PROJECT_ENVIRONMENT=/venv
ENV UV_PYTHON=python3.10
ENV UV_CACHE_DIR=/root/.cache/uv

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends postgresql-client \
     && apt-get clean -y && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra all --no-install-project

COPY . .
