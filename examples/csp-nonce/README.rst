This example shows how to make Flask-Admin work with a Content-Security-Policy by injecting
a nonce into HTML tags.

To run this example:

1. Clone the repository and navigate to this example::

    git clone https://github.com/pallets-eco/flask-admin.git
    cd flask-admin/examples/csp-nonce

2. Create and activate a virtual environment::

    virtualenv env
    source env/bin/activate

3. Install requirements::

    pip install -r requirements.txt

4. Run the application::

    python app.py
