"""
Django settings for flask_admin_django project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from shutil import copyfile
BASE_DIR = os.path.dirname(__file__)
print(BASE_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'h53q_5zi-71bik1)e+yx0(^6fdp#84j#dz7z^@fvch0%4plvh8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True
example_db = os.path.join(BASE_DIR, 'db.sqlite3')
if not os.path.exists(example_db):
    raise Exception('example db file %s not exists' % example_db)
test_db = os.path.join(BASE_DIR, 'db_test.sqlite3')
if not os.path.exists(test_db):
    copyfile(example_db, test_db)
    print('successfully copeid test db: %s  ' % test_db)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': test_db,
    }
}


INSTALLED_APPS = (
    'polls',
)
