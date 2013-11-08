from flask import Flask
from flask.ext.admin import Admin


app = Flask(__name__)
app.debug = True

admin = Admin(app)

if __name__ == '__main__':

    # Start app
    app.run(debug=True)
