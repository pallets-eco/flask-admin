# Flask-Admin

Flask-Admin is now part of Pallets-Eco, an open source organization managed by the
Pallets team to facilitate community maintenance of Flask extensions. Please update
your references to `https://github.com/pallets-eco/flask-admin.git`.

[![image](https://d322cqt584bo4o.cloudfront.net/flask-admin/localized.svg)](https://crowdin.com/project/flask-admin) [![image](https://github.com/pallets-eco/flask-admin/actions/workflows/tests.yaml/badge.svg?branch=master)](https://github.com/pallets-eco/flask-admin/actions/workflows/test.yaml)

## Pallets Community Ecosystem

> [!IMPORTANT]\
> This project is part of the Pallets Community Ecosystem. Pallets is the open
> source organization that maintains Flask; Pallets-Eco enables community
> maintenance of related projects. If you are interested in helping maintain
> this project, please reach out on [the Pallets Discord server][discord].

[discord]: https://discord.gg/pallets

## Introduction

Flask-Admin is a batteries-included, simple-to-use
[Flask](https://flask.palletsprojects.com/) extension that lets you add admin
interfaces to Flask applications. It is inspired by the *django-admin*
package, but implemented in such a way that the developer has total
control over the look, feel, functionality and user experience of the resulting
application.

Out-of-the-box, Flask-Admin plays nicely with various ORM\'s, including

-   [SQLAlchemy](https://www.sqlalchemy.org/)
-   [pymongo](https://pymongo.readthedocs.io/)
-   and [Peewee](https://github.com/coleifer/peewee).

It also boasts a simple file management interface and a [Redis
client](https://redis.io/) console.

The biggest feature of Flask-Admin is its flexibility. It aims to provide a
set of simple tools that can be used to build admin interfaces of
any complexity. To start off, you can create a very simple
application in no time, with auto-generated CRUD-views for each of your
models. Then you can further customize those views and forms as
the need arises.

Flask-Admin is an active project, well-tested and production-ready.

## Examples

Several usage examples are included in the */examples* folder. Please
add your own, or improve on the existing examples, and submit a
*pull-request*.

To run the examples in your local environment:
1. Clone the repository:

    ```bash
    git clone https://github.com/pallets-eco/flask-admin.git
    cd flask-admin
    ```
2. Create and activate a virtual environment:

    ```bash
    # Windows:
    python -m venv .venv
    .venv\Scripts\activate

    # Linux:
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. Navigate into the SQLAlchemy example folder:

    ```bash
    cd examples/sqla
    ```

4. Install requirements:

    ```bash
    pip install -r requirements.txt
    ```

5. Run the application:

    ```bash
    python app.py
    ```

6. Check the Flask app running on <http://localhost:5000>.

## Documentation

Flask-Admin is extensively documented, you can find all of the
documentation at <https://flask-admin.readthedocs.io/en/latest/>.

The docs are auto-generated from the *.rst* files in the */doc* folder.
If you come across any errors or if you think of anything else that
should be included, feel free to make the changes and submit a *pull-request*.

To build the docs in your local environment, from the project directory:

    tox -e docs-html

## Installation

To install Flask-Admin, simply:

    pip install flask-admin

Or alternatively, you can download the repository and install manually
by doing:

    git clone https://github.com/pallets-eco/flask-admin.git
    cd flask-admin
    pip install .

## Tests

Tests are run with *pytest*. If you are not familiar with this package, you can find out more on [their website](https://pytest.org/).

To run the tests, from the project directory, simply run:

    pip install --use-pep517 -r requirements/dev.txt
    pytest

You should see output similar to:

    .............................................
    ----------------------------------------------------------------------
    Ran 102 tests in 13.132s

    OK

**NOTE!** For all the tests to pass successfully, you'll need several services running locally:
Postgres (with the postgis and hstore extension), MongoDB, and Azurite.
You'll also need *libgeos* available.
See tests.yaml for Docker configuration and follow service-specific setup below.

## Setting up local Postgres for tests

```bash
psql postgres
> CREATE DATABASE flask_admin_test;
> # Connect to database "flask_admin_test":
> \c flask_admin_test;
> CREATE EXTENSION postgis;
> CREATE EXTENSION hstore;
```

If you\'re using Homebrew on MacOS, you might need this:

```bash
# Install postgis and geos
brew install postgis
brew install geos

# Set up a PostgreSQL user
createuser -s postgresql
brew services restart postgresql
```

## Setting up Azure Blob Storage emulator for tests

1. Run the [Azurite emulator](https://learn.microsoft.com/azure/storage/common/storage-use-azurite?tabs=visual-studio%2Cblob-storage)

2. Set the connection string for the emulator:

```bash
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
```

You can also run the tests on multiple environments using *tox*.

## 3rd Party Stuff

Flask-Admin is built with the help of
[Bootstrap](https://getbootstrap.com/),
[Select2](https://github.com/ivaynberg/select2) and
[Bootswatch](https://bootswatch.com/).

If you want to localize your application, install the
[Flask-Babel](https://pypi.python.org/pypi/Flask-Babel) package.

You can help improve Flask-Admin\'s translations through Crowdin:
<https://crowdin.com/project/flask-admin>
