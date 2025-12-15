from flask import Flask
from flask_admin import Admin
from flask_admin import BaseView
from flask_admin import expose
from flask_admin.theme import TablerTheme

app = Flask(__name__)


admin = Admin(
    app=app,
    name="Example: Simple Views with Tabler Theme",
    theme=TablerTheme(),
)


@app.route("/")
def index() -> str:
    """Render Home page."""
    return '<a href="/admin/">Click me to get to Admin!</a>'


class AboutView(BaseView):
    """About View, to add a simple custom view."""

    @expose("/")
    def index(self) -> str:
        """Render About page."""
        return self.render("about.html")


if __name__ == "__main__":
    admin.add_view(AboutView(name="About"))
    app.run(debug=True)
