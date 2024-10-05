#!/bin/sh

# get newest translations from Crowdin
cd ../flask_admin/translations/
curl http://api.crowdin.net/api/project/flask-admin/export?key=`cat ~/.crowdin.flaskadmin.key`
wget http://api.crowdin.net/api/project/flask-admin/download/all.zip?key=`cat ~/.crowdin.flaskadmin.key` -O all.zip

# unzip and move .po files in subfolders called LC_MESSAGES
unzip -o all.zip
find . -maxdepth 2 -name "*.po" -exec bash -c 'mkdir -p $(dirname {})/LC_MESSAGES; mv {} $(dirname {})/LC_MESSAGES/admin.po' \;
rm all.zip
mv es-ES/LC_MESSAGES/* es/LC_MESSAGES/
rm -r es-ES/
mv ca/LC_MESSAGES/* ca_ES/LC_MESSAGES/
rm -r ca/
mv zh-CN/LC_MESSAGES/* zh_Hans_CN/LC_MESSAGES/
rm -r zh-CN/
mv zh-TW/LC_MESSAGES/* zh_Hant_TW/LC_MESSAGES/
rm -r zh-TW/
mv pt-PT/LC_MESSAGES/* pt/LC_MESSAGES/
rm -r pt-PT/
mv pt-BR/LC_MESSAGES/* pt_BR/LC_MESSAGES/
rm -r pt-BR/
mv sv-SE/LC_MESSAGES/* sv/LC_MESSAGES/
rm -r sv-SE/
mv pa-IN/LC_MESSAGES/* pa/LC_MESSAGES/
rm -r pa-IN/

cd ../../babel
sh babel.sh
