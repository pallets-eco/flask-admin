#!/bin/bash

# Enable exit on non 0
set -e

# Set the current working directory to the directory in which the script is located, for CI/CD
cd "$(dirname "$0")"
cd ..
echo "Current working directory: $(pwd)"

echo ""
echo "Running pytest..."

# pytest /home/user/workspace/tests/ -v --lf --durations=0
pytest /home/user/workspace/tests/ -v --durations=0

echo ""
echo "pytest complete!"

exit 0