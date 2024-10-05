#!/bin/bash

# Enable exit on non 0
set -e

# Set the current working directory to the directory in which the script is located, for CI/CD
cd "$(dirname "$0")"
cd ..
echo "Current working directory: $(pwd)"

echo ""
echo "Making requirements.prod.txt and requirements.dev.txt..."

poetry export --no-interaction --no-ansi --without-hashes --format requirements.txt --output ./requirements.prod.txt
poetry export --no-interaction --no-ansi --without-hashes --format requirements.txt --dev --output ./requirements.dev.txt

echo ""
echo "Process complete!"

exit 0