# Flask-Admin

Flask-Admin is now part of Pallets-Eco, an open source organization managed by the
Pallets team to facilitate community maintenance of Flask extensions. Please update
your references to `https://github.com/pallets-eco/flask-admin.git`.

[![image](https://github.com/pallets-eco/flask-admin/actions/workflows/tests.yaml/badge.svg?branch=master)](https://github.com/pallets-eco/flask-admin/actions/workflows/test.yaml)

## Pallets Community Ecosystem

> [!IMPORTANT]\
> This project is part of the Pallets Community Ecosystem. Pallets is the open
> source organization that maintains Flask; Pallets-Eco enables community
> maintenance of related projects. If you are interested in helping maintain
> this project, please reach out on [the Pallets Discord server][discord].

## Introduction

Flask-Admin is a batteries-included, simple-to-use
[Flask](https://flask.palletsprojects.com/) extension that lets you add admin
interfaces to Flask applications. It is inspired by the *django-admin*
package, but implemented in such a way that the developer has total
control over the look, feel, functionality and user experience of the resulting
application.

Out-of-the-box, Flask-Admin plays nicely with various ORM\'s, including

- [SQLAlchemy](https://www.sqlalchemy.org/)
- [pymongo](https://pymongo.readthedocs.io/)
- [MongoEngine](https://mongoengine.org/)
- and [Peewee](https://github.com/coleifer/peewee).

It also boasts a simple file management interface and a [Redis client](https://redis.io/) console.

The biggest feature of Flask-Admin is its flexibility. It aims to provide a
set of simple tools that can be used to build admin interfaces of
any complexity. To start off, you can create a very simple
application in no time, with auto-generated CRUD-views for each of your
models. Then you can further customize those views and forms as
the need arises.

Flask-Admin is an active project, well-tested and production-ready.

## Examples

Several usage examples are included in the */examples* folder. Please add your own, or improve on the existing examples, and submit a *pull-request*.

### How to run an example

Clone the repository and navigate to an example (for this example we are using SQLAlchemy Example):

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/sqla
```

> All examples use [`uv`](https://docs.astral.sh/uv/) to manage their dependencies and the developer environment.

Run the example using `uv`, which will manage the environment and dependencies automatically:

```shell
uv run main.py
```

Check the Flask app running on <http://localhost:5000>.

## Documentation

Flask-Admin is extensively documented, you can find all of the
documentation at <https://flask-admin.readthedocs.io/en/latest/>.

The docs are auto-generated from the *.rst* files in the */doc* folder.
If you come across any errors or if you think of anything else that
should be included, feel free to make the changes and submit a *pull-request*.

To build the docs in your local environment, from the project directory:

```shell
tox -e docs
```

## Installation

To install Flask-Admin using pip, simply:

```shell
pip install flask-admin
```

## Contributing

If you are a developer working on and maintaining Flask-Admin, checkout the repo by doing:

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin
```

Flask-Admin uses [`uv`](https://docs.astral.sh/uv/) to manage its dependencies and developer environment. With
the repository checked out, to install the minimum version of Python that Flask-Admin supports, create your
virtual environment, and install the required dependencies, run:

```shell
uv sync
```

This will install Flask-Admin but without any of the optional extra dependencies, such as those for sqlalchemy
or mongoengine support. To install all extras, run:

```shell
uv sync --extra all
```

Finally, enable pre-commit hooks:

```shell
pre-commit install
```

## Tests

Tests are run with *pytest*. If you are not familiar with this package, you can find out more on [their website](https://pytest.org/).

### Running tests inside the devcontainer (eg when using VS Code)

If you are developing with the devcontainer configuration, then you can run tests directly using either of the following commands.

To just run the test suite with the default python installation, use:

```shell
uv run pytest
```

To run the test suite against all supported python versions, and also run other checks performed by CI, use:

```shell
uv run tox
```

### Running tests as a one-off via docker-compose run / `make test`

If you don't use devcontainers then you can run the tests using docker (you will need to install and setup docker yourself). Then you can use:

```shell
make test-in-docker
```

This will use the devcontainer docker-compose configuration to start up postgres, azurite and mongo.

You can also run the full test suite including CI checks with:

```shell
make tox-in-docker
```

## 3rd Party Stuff

Flask-Admin is built with the help of
[Bootstrap](https://getbootstrap.com/),
[Select2](https://github.com/ivaynberg/select2) and
[Bootswatch](https://bootswatch.com/).

If you want to localize your application, install the
[Flask-Babel](https://pypi.python.org/pypi/Flask-Babel) package.

You can help improve Flask-Admin\'s translations by opening a PR.
## As a developer who's changed some text in Flask-Admin
```bash
uv sync --group docs
cd babel
./babel.sh --update
```

## As a translator who's updated some `.po`/`.mo` files
Run `cd babel`
Run `./babel.sh`

<!-- refs -->
[discord]: https://discord.gg/pallets
