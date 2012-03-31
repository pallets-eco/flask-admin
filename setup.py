from setuptools import setup

setup(
    name='Flask-AdminEx',
    version='0.0.1',
    url='https://github.com/mrjoes/flask-extadmin/',
    license='BSD',
    author='Serge S. Koval',
    author_email='serge.koval+github@gmail.com',
    description='Simple and extensible admin interface framework for Flask',
    long_description=__doc__,
    packages=['flask_adminex', 'flask_adminex.ext'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.7',
        'Flask-WTF>=0.6',
    ],
    setup_required=[
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
    ]
)
