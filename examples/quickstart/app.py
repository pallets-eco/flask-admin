from flask import Flask
from flask_admin import Admin


app = Flask(__name__)
app.debug = True

admin = Admin(app, name="Example: Quickstart")

if __name__ == '__main__':

    # Start app
    app.run(debug=True)
