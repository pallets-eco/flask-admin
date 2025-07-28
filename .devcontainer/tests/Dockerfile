ARG IMAGE=3.12-slim
FROM python:${IMAGE}

ENV UV_PROJECT_ENVIRONMENT=/venv

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends postgresql-client git \
     && apt-get clean -y && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace
COPY . .
RUN uv sync --extra all
