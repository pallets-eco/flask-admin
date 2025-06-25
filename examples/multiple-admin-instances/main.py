from flask import Flask
from flask_admin import Admin
from flask_admin import BaseView
from flask_admin import expose


# Views
class FirstView(BaseView):
    @expose("/")
    def index(self):
        return self.render("first.html")


class SecondView(BaseView):
    @expose("/")
    def index(self):
        return self.render("second.html")


app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    return (
        '<a href="/admin1">Click me to get to Admin 1</a><br/><a href="/admin2">'
        "Click me to get to Admin 2</a>"
    )


if __name__ == "__main__":
    # Create first administrative interface under /admin1
    admin1 = Admin(app, url="/admin1")
    admin1.add_view(FirstView())

    # Create second administrative interface under /admin2
    admin2 = Admin(app, url="/admin2", endpoint="admin2")
    admin2.add_view(SecondView())

    # Start app
    app.run(debug=True)
