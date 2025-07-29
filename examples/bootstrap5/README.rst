This example demonstrates the Bootstrap 5 theme for Flask-Admin, showcasing all the available features and components with the new Bootstrap 5 styling.

To run this example:

1. Clone the repository and navigate to this example::

    git clone https://github.com/pallets-eco/flask-admin.git
    cd flask-admin/examples/bootstrap5

2. Create and activate a virtual environment:

   Using virtualenv::

    virtualenv env
    source env/bin/activate

   Or using uv (faster alternative)::

    uv venv
    source .venv/bin/activate

3. Install requirements:

   Using pip::

    pip install -r requirements.txt

   Or using uv::

    uv pip install -r requirements.txt

4. Run the application::

    python app.py

The first time you run this example, a sample sqlite database gets populated automatically. To suppress this behaviour,
comment the following lines in app.py::

    if not os.path.exists(database_path):
        build_sample_db()
