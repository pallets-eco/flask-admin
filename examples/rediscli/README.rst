This example shows how to set up a Flask-Admin view as a Redis terminal.

To run this example:

1. Clone the repository::

    git clone https://github.com/flask-admin/flask-admin.git
    cd flask-admin

2. Create and activate a virtual environment::

    virtualenv env
    source env/bin/activate

3. Install requirements::

    pip install -r 'examples/rediscli/requirements.txt'

4. Run the application::

    python examples/rediscli/app.py

You should now be able to access a Redis instance on your machine (if it is running) through the admin interface.
