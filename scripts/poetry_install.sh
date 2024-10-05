#!/bin/bash
# This script is for the Dockerfile to run, to create the development image

# Enable exit on non 0
# set -e

# Set the current working directory to the directory in which the script is located, for CI/CD
cd "$(dirname "$0")"
cd ..
echo "Current working directory: $(pwd)"

echo ""
echo "Poetry installation starting..."

# Load environment variables from dotenv / .env file in Bash, and remove comments
# export $(cat /run/secrets/secret_envs | sed 's/#.*//g' | xargs)

echo "DOCKER_BUILDKIT: $DOCKER_BUILDKIT"
echo "COMPOSE_DOCKER_CLI_BUILD: $COMPOSE_DOCKER_CLI_BUILD"
echo "PYPI_USERNAME_PRIVATE: $PYPI_USERNAME_PRIVATE"
echo "PYPI_PASSWORD_PRIVATE: $PYPI_PASSWORD_PRIVATE"
echo "Setting up config..."

# in-project .venv makes it very slow since it's sharing files with Windows/WSL...
# poetry config virtualenvs.in-project true

# These settings get put into the ~/.config./pyconfig/config.toml file
poetry config virtualenvs.create false
poetry config repositories.ijack_private https://pypi.myijack.com
# The following username/password setup doesn't seem to work for some reason...
# poetry config http-basic.ijack_private $PYPI_USERNAME_PRIVATE $PYPI_PASSWORD_PRIVATE
echo "Running poetry install..."
# poetry add --dev gateway-setup
poetry install --no-interaction --no-ansi 

echo ""
echo "Poetry installation complete!"

exit 0