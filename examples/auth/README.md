# Auth Example

This example shows how to integrate [Flask-Security](https://pythonhosted.org/Flask-Security/) with Flask-Admin using the SQLAlchemy backend. It only implements the 'login' & 'register' views, but you could follow the same approach for using all of Flask-Security's builtin views (e.g. 'forgot password', 'change password', 'reset password', 'send confirmation' and 'send login').

## How to run this example

Clone the repository and navigate to this example:

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/auth
```

> This example uses [`uv`](https://docs.astral.sh/uv/) to manage its dependencies and developer environment.

Run the example using `uv`, which will manage the environment and dependencies automatically:

```shell
uv run main.py
```
