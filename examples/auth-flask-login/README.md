# Auth with Flask-Login Example

This example shows how to integrate Flask-Login authentication with Flask-Admin using the SQLAlchemy backend.

## How to run this example

Clone the repository and navigate to this example:

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/auth-flask-login
```

> This example uses [`uv`](https://docs.astral.sh/uv/) to manage its dependencies and developer environment.

Run the example using `uv`, which will manage the environment and dependencies automatically:

```shell
uv run main.py
```

The first time you run this example, a sample sqlite database gets populated automatically. To suppress this behaviour, comment the following lines in main.py:

```python
if not os.path.exists(database_path):
    with app.app_context():
        build_sample_db()
```
