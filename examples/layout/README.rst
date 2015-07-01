This example shows how you can customize the look & feel of the admin interface. This is done by overriding some of the built-in templates.

To run this example:

1. Clone the repository::

    git clone https://github.com/flask-admin/flask-admin.git
    cd flask-admin

2. Create and activate a virtual environment::

    virtualenv env
    source env/bin/activate

3. Install requirements::

    pip install -r 'examples/layout/requirements.txt'

4. Run the application::

    python examples/layout/app.py

The first time you run this example, a sample sqlite database gets populated automatically. To suppress this behaviour,
comment the following lines in app.py:::

    if not os.path.exists(database_path):
        build_sample_db()
