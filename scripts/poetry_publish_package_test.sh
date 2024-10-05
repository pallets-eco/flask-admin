#!/bin/bash

set -e

# Set the current working directory to the directory in which the script is located, for CI/CD
cd "$(dirname "$0")"
echo "Current working directory: $(pwd)"

# Load environment variables from dotenv / .env file in Bash, and remove comments
export $(cat ../.env | sed 's/#.*//g' | xargs)
echo "PYPI_TOKEN_TEST: $PYPI_TOKEN_TEST"

# https://python-poetry.org/docs/libraries/
# https://python-poetry.org/docs/cli/#publish
poetry config repositories.testpypi https://test.pypi.org/legacy/
# poetry config pypi-token.pypi $PYPI_TOKEN_TEST

# First build the files to be uploaded
poetry build

# Publish to the test repository
# poetry publish --repository testpypi
poetry publish --repository testpypi --username __token__ --password $PYPI_TOKEN_TEST
# poetry publish --repository testpypi --username $PYPI_USERNAME_TEST --password $PYPI_PASSWORD_TEST

# Test that it worked
# pip install --index-url https://test.pypi.org/simple/ make-responsive-images