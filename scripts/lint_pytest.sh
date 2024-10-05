#!/bin/bash

# Enable exit on non 0
set -e
set -x

# Set the current working directory to the directory in which the script is located, for CI/CD
cd "$(dirname "$0")"
# cd ..
echo "Current working directory: $(pwd)"

# Remove unused imports and unused variables
echo ""
echo "Linting first..."
sh ./lint_apply.sh

echo ""
echo "Running Pytest..."
sh ./pytest_run_all.sh
