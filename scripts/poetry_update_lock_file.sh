#!/bin/bash

set -e

# Set the current working directory to the directory in which the script is located, for CI/CD
cd "$(dirname "$0")"
cd ..
echo "Current working directory: $(pwd)"

poetry lock --no-update