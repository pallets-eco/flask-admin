This example shows how to integrate Flask-Security-Too (https://pypi.org/project/Flask-Security-Too/) with Flask-Admin using the SQLAlchemy backend. It implements
the 'login', 'register', 'change password', and 'forgot password' views. In addition, it shows how to utilize Flask-Security-Too's language translations in locally
modified form templates.

To run this example:

1. Clone the repository::

     git clone https://github.com/flask-admin/flask-admin.git
     cd flask-admin

2. Create and activate a virtual environment::

     virtualenv env
     source env/bin/activate

3. Install requirements::

     pip install -r 'examples/auth-fs-too/requirements.txt'

4. Run the application::

     python examples/auth-fs-too/app.py

The first time you run this example, a sample sqlite database gets populated automatically. To suppress this behaviour,
comment the following lines in app.py:::

     if not os.path.exists(database_path):
         build_sample_db()
