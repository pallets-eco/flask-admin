#!/bin/bash

SOURCE_BASE_PATH="node_modules"
TARGET_BASE_PATH="flask_admin/static/vendor"

echo - Copying Font Awesome
mkdir -p ${TARGET_BASE_PATH}/fontawesome
cp -a ${SOURCE_BASE_PATH}/@fortawesome/fontawesome-free/. ${TARGET_BASE_PATH}/fontawesome/

echo - Copying Tabler
mkdir -p ${TARGET_BASE_PATH}/tabler
cp -a ${SOURCE_BASE_PATH}/@tabler/core/dist/. ${TARGET_BASE_PATH}/tabler/

echo - "Copying X-editable"
mkdir -p ${TARGET_BASE_PATH}/skycyclone/x-editable
cp -a ${SOURCE_BASE_PATH}/x-editable/dist/. ${TARGET_BASE_PATH}/x-editable/
