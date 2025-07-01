#!/bin/sh
uv run pybabel extract -F babel.ini -k _gettext -k _ngettext -k lazy_gettext -o admin.pot --project Flask-Admin ../flask_admin

if [ "$1" = '--update' ]; then
    uv run pybabel update -i admin.pot -d ../flask_admin/translations -D admin -N
fi

uv run pybabel compile -f -D admin -d ../flask_admin/translations/


## Commenting out temporarily: we don't have any of our docs translated right now and we don't have support for doing it.
## We can uncomment this intentionally when we want to start supporting having our docs translated.
# cd ..
# make gettext
# cp build/locale/*.pot babel/
# uv run sphinx-intl update -p build/locale/ -d flask_admin/translations/
