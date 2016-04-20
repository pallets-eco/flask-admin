# Fix for older setuptools
import re
import os

from setuptools import setup, find_packages


def fpath(name):
    return os.path.join(os.path.dirname(__file__), name)


def read(fname):
    return open(fpath(fname)).read()


def desc():
    info = read('README.rst')
    try:
        return info + '\n\n' + read('doc/changelog.rst')
    except IOError:
        return info

# grep flask_admin/__init__.py since python 3.x cannot import it before using 2to3
file_text = read(fpath('flask_admin/__init__.py'))


def grep(attrname):
    pattern = r"{0}\W*=\W*'([^']+)'".format(attrname)
    strval, = re.findall(pattern, file_text)
    return strval


setup(
    name='Flask-Admin',
    version=grep('__version__'),
    url='https://github.com/flask-admin/flask-admin/',
    license='BSD',
    author=grep('__author__'),
    author_email=grep('__email__'),
    description='Simple and extensible admin interface framework for Flask',
    long_description=desc(),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.7',
        'wtforms'
    ],
    tests_require=[
        'nose>=1.0',
        'pillow==2.9.0',
        'mongoengine',
        'pymongo',
        'wtf-peewee',
        'sqlalchemy',
        'flask-mongoengine',
        'flask-sqlalchemy',
        'flask-babelex',
        'shapely',
        'geoalchemy2',
        'psycopg2',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='nose.collector'
)
