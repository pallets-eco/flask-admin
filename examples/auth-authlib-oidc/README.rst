This example shows how to integrate Flask-Security (https://pythonhosted.org/Flask-Security/) with Flask-Admin using the SQLAlchemy backend, while relying on OpenID Connect authentication, based on authlib.
Since authentication is delegated to an OIDC provider, there is no need for a login/register/forgot password/etc. views provided by Flask-Security.
We'll replace those by simples login/logout views that will trigger OIDC authentication.


To run this example:

1. Clone the repository::

     git clone https://github.com/flask-admin/flask-admin.git
     cd flask-admin

2. Create and activate a virtual environment::

     virtualenv env
     source env/bin/activate

3. Install requirements::

     pip install -r 'examples/auth-oidc-authlib/requirements.txt'

4. Point the configuration to your own OIDC provider, in examples/auth-oidc-authlib/config.py::

    OIDC_SAMPLE_SERVER_METADATA_URL = "https://your.oidc.com/.well-known/openid-configuration"
    OIDC_SAMPLE_CLIENT_ID = "your_client_id"
    OIDC_SAMPLE_CLIENT_SECRET = "your_client_secret"

4. Run the application::

     python examples/auth-authlib-oidc/app.py

The first time you run this example, a sample sqlite database gets populated automatically. To suppress this behaviour,
comment the following lines in app.py:::

     if not os.path.exists(database_path):
         build_sample_db()
