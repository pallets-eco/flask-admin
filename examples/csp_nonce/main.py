from flask import Flask
from flask_admin import Admin
from flask_admin.theme import Bootstrap4Theme
from flask_talisman import Talisman

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
# Get the CSP nonce generator from jinja environment globals which is added by Talisman
csp_nonce_generator = app.jinja_env.globals["csp_nonce"]


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


admin = Admin(
    app,
    name="Example: Simple Views",
    theme=Bootstrap4Theme(),
    csp_nonce_generator=csp_nonce_generator,
)

if __name__ == "__main__":
    app.run(debug=True)
