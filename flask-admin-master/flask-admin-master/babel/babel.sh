#!/bin/sh
pybabel extract -F babel.ini -k _gettext -k _ngettext -k lazy_gettext -o admin.pot --project Flask-Admin ../flask_admin
pybabel compile -f -D admin -d ../flask_admin/translations/

# docs
cd ..
make gettext
cp build/locale/*.pot babel/
sphinx-intl update -p build/locale/ -d flask_admin/translations/
