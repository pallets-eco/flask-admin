This example shows how to make Flask-Admin display all datetime fields in client's
timezone.
Timezone conversion is handled by the frontend in /static/js/timezone.js, but an
automatic post request to /set_timezone is done so that flask session can store the
client's timezone and save datetime inputs in the correct timezone.

To run this example:

1. Clone the repository and navigate to this example::

    git clone https://github.com/pallets-eco/flask-admin.git
    cd flask-admin/examples/datetime-timezone

2. Create and activate a virtual environment::

    virtualenv env
    source env/bin/activate

3. Install requirements::

    pip install -r requirements.txt

4. Run the application::

    python app.py
