This example shows how to configure Flask-Admin when you're using Flask's `host_matching` mode. Any Flask-Admin instance can be exposed on just a specific host, or on every host.

To run this example:

1. Clone the repository and navigate to this example::

    git clone https://github.com/pallets-eco/flask-admin.git
    cd flask-admin/examples/host-matching

2. Create and activate a virtual environment::

    python3 -m venv .venv
    source .venv/bin/activate

3. Install requirements::

    pip install -r requirements.txt

4. Run the application::

    python app.py
