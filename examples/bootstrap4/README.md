# Bootstrap4 Customization Example

This example shows how you can customize the look & feel of the admin interface. This is done by overriding some of the built-in templates.

## How to run this example

Clone the repository and navigate to this example:

```bash
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/babel
```

> This example uses [`uv`](https://docs.astral.sh/uv/) to manage its dependencies and developer environment.

To install the minimum version of Python this example supports, create your virtual environment, and install the required dependencies, run:

```bash
uv sync
```

Run the application:

```bash
uv run main.py
```

The first time you run this example, a sample sqlite database gets populated automatically. To suppress this behaviour, comment the following lines in app.py:

```python
if not os.path.exists(database_path):
    build_sample_db()
```
