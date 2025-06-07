ARG IMAGE=bullseye
FROM mcr.microsoft.com/devcontainers/${IMAGE}

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends postgresql-client \
     && apt-get clean -y && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace

COPY README.md LICENSE.txt ../../uv.lock pyproject.toml setup.cfg .python-version .
COPY flask_admin flask_admin
RUN uv sync --link-mode=copy --extra all
