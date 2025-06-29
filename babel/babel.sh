#!/bin/sh
uv run pybabel extract -F babel.ini -k _gettext -k _ngettext -k lazy_gettext -o admin.pot --project Flask-Admin ../flask_admin

if [ "$1" = '--update' ]; then
    uv run pybabel update -i admin.pot -d ../flask_admin/translations -D admin -N
fi

uv run pybabel compile -f -D admin -d ../flask_admin/translations/

# docs
cd ..
make gettext
cp build/locale/*.pot babel/
uv run sphinx-intl update -p build/locale/ -d flask_admin/translations/
