# Tabler Example

This example demonstrates how to enable and customize the Tabler theme in Flask-Admin.

The theme is configured via TablerTheme:

```python
from flask import Flask
from flask_admin import Admin
from flask_admin.theme import TablerTheme


app = Flask(__name__)
admin = Admin(
    app,
    name="Example: Tabler",
    theme=TablerTheme(layout="fluid", theme_primary="purple")
)
```

In the Example, TablerTheme settings can be adjusted dynamically from the navbar.
In Production, the user can override dynamically only theme_primary (i.e. from dark mode to light mode and viceversa).

The current example uses `TablerTheme(layout="fluid", theme_primary="purple")`.
You can play around with the various settings by changing them from the navbar.

### layout="fluid", theme_primary="indigo", theme="dark":
<img alt="image" src="https://github.com/user-attachments/assets/5380dd6d-fd8d-45d2-8a67-ad5871b41224" />

### layout="fluid", theme_primary="zinc", theme="light":
<img alt="image" src="https://github.com/user-attachments/assets/3cb92eab-c0c4-4d0b-86fc-5224a13937d1" />

### layout="vertical", theme_primary="lime", theme="dark":
<img alt="image" src="https://github.com/user-attachments/assets/ff08013d-46da-4f00-a59d-2ba2e9bec263" />

## How to run this example

Clone the repository and navigate to this example:

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/tabler
```

> This example uses [`uv`](https://docs.astral.sh/uv/) to manage its dependencies and developer environment.

Run the example using `uv`, which will manage the environment and dependencies automatically:

```shell
uv run main.py
```
