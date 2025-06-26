import os
import os.path as op

from admin import app
from admin.data import build_sample_db
from jinja2 import StrictUndefined

if __name__ == "__main__":
    app_dir = op.join(op.realpath(os.path.dirname(__file__)), "admin")
    database_path = op.join(app_dir, app.config["DATABASE_FILE"])
    if not os.path.exists(database_path):
        with app.app_context():
            build_sample_db()

    app.jinja_env.undefined = StrictUndefined
    app.run(debug=True)
