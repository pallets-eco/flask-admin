#!/bin/bash

# Set the current working directory to the directory in which the script is located, for CI/CD
cd "$(dirname "$0")"
echo "Current working directory: $(pwd)"

sudo dos2unix ./dos2unix_poetry_publish_package_prod.sh

bash ./dos2unix_poetry_publish_package_prod.sh

exit 0
