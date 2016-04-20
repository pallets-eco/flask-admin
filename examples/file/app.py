import os
import os.path as op

from flask import Flask

import flask_admin as admin
from flask_admin.contrib import fileadmin


# Create flask app
app = Flask(__name__, template_folder='templates', static_folder='files')

# Create dummy secrey key so we can use flash
app.config['SECRET_KEY'] = '123456790'


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create directory
    path = op.join(op.dirname(__file__), 'files')
    try:
        os.mkdir(path)
    except OSError:
        pass

    # Create admin interface
    admin = admin.Admin(app, 'Example: Files')
    admin.add_view(fileadmin.FileAdmin(path, '/files/', name='Files'))

    # Start app
    app.run(debug=True)
