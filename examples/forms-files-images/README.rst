This example shows how you can::

    * define your own custom forms by using form rendering rules
    * handle generic static file uploads
    * handle image uploads
    * turn a TextArea field into a rich WYSIWYG editor using WTForms and CKEditor
    * set up a Flask-Admin view as a Redis terminal


To run this example:

1. Clone the repository and navigate to this example::

    git clone https://github.com/flask-admin/flask-admin.git
    cd flask-admin/examples/forms-files-images

2. Create and activate a virtual environment::

    virtualenv env
    source env/bin/activate

3. Install requirements::

    pip install -r requirements.txt

4. Run the application::

    python app.py

The first time you run this example, a sample sqlite database gets populated automatically. To suppress this behaviour,
comment the following lines in app.py:::

    if not os.path.exists(database_path):
        build_sample_db()
