# Custom Layout Example

This example shows how you can customize the look & feel of the admin interface. This is done by overriding some of the built-in templates.

## How to run this example

Clone the repository and navigate to this example:

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/custom-layout
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
