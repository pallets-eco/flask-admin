from flask import Flask
from flask.ext.adminex import Admin


app = Flask(__name__)

admin = Admin(app)
app.run()
