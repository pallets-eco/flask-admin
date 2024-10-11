#!/bin/bash

# Enable exit on non 0
set -e
set -x

# Set the current working directory to the directory in which the script is located, for CI/CD
cd "$(dirname "$0")"
# cd ..
echo "Current working directory: $(pwd)"

# Nice sorting of imports
echo ""
echo "Running isort..."
isort --profile black ../flask_admin --check-only
isort --profile black ../flask_admin/tests --check-only

# Remove unused imports and unused variables
echo ""
echo "Running autoflake..."
autoflake --in-place --remove-unused-variables --remove-all-unused-imports --verbose --recursive ../flask_admin
autoflake --in-place --remove-unused-variables --remove-all-unused-imports --verbose --recursive ../flask_admin/tests

# Opinionated but lovely auto-formatting
echo ""
echo "Running black..."
black ../flask_admin --check
black ../flask_admin/tests --check

echo ""
echo "Running flake8..."
# flake8 ../flask_admin
# flake8 ../flask_admin/tests
flake8 ../flask_admin --ignore 'E402,E501,W503,E203,E741,C901'
flake8 ../flask_admin/tests --ignore 'E402,E501,W503,E203,E741,C901'

# echo ""
# echo "Running mypy..."
# mypy --config-file ../mypy.ini ../flask_admin --disallow-untyped-defs

# Security checks with Bandit and Safety
echo ""
echo "Running bandit..."
bandit -r "../flask_admin"
bandit -r "../flask_admin/tests" --configfile "../.bandit_4_tests.yml"

echo ""
echo "Running safety..."
safety check

# For Jinja2 template blocks
echo ""
echo "Running curlylint..."
curlylint ../flask_admin/templates --parse-only

echo ""
echo "Lint check complete!"

exit 0