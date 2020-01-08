from admin import app
from admin.data import build_sample_db
import os
import os.path as op

# Build a sample db on the fly, if one does not exist yet.
app_dir = op.join(op.realpath(os.path.dirname(__file__)), 'admin')
database_path = op.join(app_dir, app.config['DATABASE_FILE'])
if not os.path.exists(database_path):
    build_sample_db()

# Start app
app.run(debug=True)
