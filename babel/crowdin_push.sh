#!/bin/sh
sh babel.sh
curl -F "files[/admin.pot]=@admin.pot" http://api.crowdin.net/api/project/flask-admin/update-file?key=`cat ~/.crowdin.flaskadmin.key`
