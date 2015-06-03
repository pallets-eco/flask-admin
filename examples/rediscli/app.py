from flask import Flask

from redis import Redis

import flask_admin as admin
from flask_admin.contrib import rediscli

# Create flask app
app = Flask(__name__)


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin interface
    admin = admin.Admin(app, name="Example: Redis")
    admin.add_view(rediscli.RedisCli(Redis()))

    # Start app
    app.run(debug=True)
