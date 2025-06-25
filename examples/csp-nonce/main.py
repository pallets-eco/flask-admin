from flask import Flask
from flask_admin import Admin
from flask_admin.theme import Bootstrap4Theme
from flask_talisman import Talisman

# Create flask app
app = Flask(__name__, template_folder="templates")
app.debug = True

talisman = Talisman(
    app,
    content_security_policy={
        "default-src": "'self'",
        "object-src": "'none'",
        "script-src": "'self'",
        "style-src": "'self'",
    },
    content_security_policy_nonce_in=["script-src", "style-src"],
)
csp_nonce_generator = app.jinja_env.globals["csp_nonce"]  # this is added by talisman


# Flask views
@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Create admin interface
admin = Admin(
    name="Example: Simple Views",
    theme=Bootstrap4Theme(),
    csp_nonce_generator=csp_nonce_generator,
)
admin.init_app(app)

if __name__ == "__main__":
    # Start app
    app.run()
