This example shows how to make Flask-Admin work with a Content-Security-Policy by injecting
a nonce into HTML tags.

To run this example:

1. Clone the repository::

    git clone https://github.com/flask-admin/flask-admin.git
    cd flask-admin

2. Create and activate a virtual environment::

    virtualenv env
    source env/bin/activate

3. Install requirements::

    pip install -r 'examples/csp-nonce/requirements.txt'

4. Run the application::

    python examples/csp-nonce/app.py
