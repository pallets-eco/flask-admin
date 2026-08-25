import os
import os.path as op

from admin import app
from admin.data import build_sample_db
from flask import redirect
from flask import url_for

app_dir = op.join(op.realpath(os.path.dirname(__file__)), "admin")
database_path = op.join(app_dir, app.config["DATABASE_FILE"])
if not os.path.exists(database_path):
    with app.app_context():
        build_sample_db()


@app.route("/")
def index():
    tmp = """
    <p><a href="/admin/?lang=en">Click me to get to Admin! (English)</a></p>
    <p><a href="/admin/?lang=cs">Click me to get to Admin! (Czech)</a></p>
    <p><a href="/admin/?lang=de">Click me to get to Admin! (German)</a></p>
    <p><a href="/admin/?lang=es">Click me to get to Admin! (Spanish)</a></p>
    <p><a href="/admin/?lang=fa">Click me to get to Admin! (Farsi)</a></p>
    <p><a href="/admin/?lang=fr">Click me to get to Admin! (French)</a></p>
    <p><a href="/admin/?lang=pt">Click me to get to Admin! (Portuguese)</a></p>
    <p><a href="/admin/?lang=ru">Click me to get to Admin! (Russian)</a></p>
    <p><a href="/admin/?lang=pa">Click me to get to Admin! (Punjabi)</a></p>
    <p>
      <a href="/admin/?lang=zh_CN">Click me to get to Admin! (Chinese - Simplified)</a>
    </p>
    <p>
      <a href="/admin/?lang=zh_TW">Click me to get to Admin! (Chinese - Traditional)</a>
    </p>
    """
    return tmp


@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="favicon.ico"))


if __name__ == "__main__":
    app.run(debug=True)
