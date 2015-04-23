#!/bin/sh

# get newest translations from Crowdin
cd ../flask_admin/translations/
curl http://api.crowdin.net/api/project/flask-admin/export?key=`cat ~/.crowdin.flaskadmin.key`
wget http://api.crowdin.net/api/project/flask-admin/download/all.zip?key=`cat ~/.crowdin.flaskadmin.key` -O all.zip

# unzip and move .po files in subfolders called LC_MESSAGES
unzip -o all.zip
find . -maxdepth 2 -name "*.po" -exec bash -c 'mkdir -p $(dirname {})/LC_MESSAGES; mv {} $(dirname {})/LC_MESSAGES/admin.po' \;
rm all.zip

