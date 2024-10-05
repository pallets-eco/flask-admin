This example shows how to:
1. Use x-editable-ajax to speed up the list view, and speed up editing of records.
2. Store images in a PostgreSQL database, instead of as a file
3. Use custom inline forms for uploading your image

To run this example:

1. Clone the repository::

    git clone https://github.com/flask-admin/flask-admin.git
    cd flask-admin

2. Create and activate a virtual environment::

    virtualenv env
    source env/bin/activate

3. Install requirements::

    pip install -r 'examples/sqla-images-postgres-x-editable-ajax/requirements.txt'

4. Run the application::

    python examples/sqla-images-postgres-x-editable-ajax/app.py
