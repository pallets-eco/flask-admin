# Fix for older setuptools
import multiprocessing, logging, os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def desc():
    info = read('README.rst')
    try:
        return info + '\n\n' + read('doc/changelog.rst')
    except IOError:
        return info

setup(
    name='Flask-Admin',
    version='1.0.0',
    url='https://github.com/mrjoes/flask-admin/',
    license='BSD',
    author='Serge S. Koval',
    author_email='serge.koval+github@gmail.com',
    description='Simple and extensible admin interface framework for Flask',
    long_description=desc(),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.7',
        'Flask-WTF>=0.6'
    ],
    tests_require=[
        'nose>=1.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    test_suite='nose.collector'
)
