# SQLAlchemy column_editable_list Example

This example demonstrates inline editing in Flask-Admin list views using `column_editable_list`. It covers all supported field types:

- **StringField** - text input
- **TextAreaField** - text area
- **IntegerField** - number input
- **FloatField** - number input (decimal)
- **BooleanField** - Yes/No select
- **DateField** - date picker
- **TimeField** - time picker
- **DateTimeField** - datetime picker
- **Enum (SelectField)** - dropdown
- **ForeignKey (QuerySelectField)** - relation dropdown

## How to run this example

Clone the repository and navigate to this example:

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/sqla_column_editable
```

> This example uses [`uv`](https://docs.astral.sh/uv/) to manage its dependencies and developer environment.

Run the example using `uv`, which will manage the environment and dependencies automatically:

```shell
uv run main.py
```

Then visit http://127.0.0.1:5000/admin/dish/ and click any value in the editable columns to edit inline.
