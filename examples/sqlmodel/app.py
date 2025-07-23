import os
import os.path as op

from admin import app  # type: ignore
from admin.data import build_sample_db
from jinja2 import StrictUndefined

# Build a sample db on the fly, if one does not exist yet.
app_dir = op.join(op.realpath(os.path.dirname(__file__)), "admin")
database_path = op.join(app_dir, app.config["DATABASE_FILE"])
if not os.path.exists(database_path):
    with app.app_context():
        build_sample_db()

if __name__ == "__main__":
    # Start app
    app.jinja_env.undefined = StrictUndefined
    app.run(debug=True)
