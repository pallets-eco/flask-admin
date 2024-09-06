SQLAlchemy model backend integration examples.

To run this example:

1. Clone the repository and navigate to this example::

    git clone https://github.com/pallets-eco/flask-admin.git
    cd flask-admin/examples/sqla

2. Create and activate a virtual environment::

    virtualenv env -p python3
    source env/bin/activate

3. Install requirements::

    pip install -r requirements.txt

4. Run the application::

    python app.py

The first time you run this example, a sample sqlite database gets populated automatically. To start
with a fresh database: `rm examples/sqla/admin/sample_db.sqlite`, and then restart the application.
