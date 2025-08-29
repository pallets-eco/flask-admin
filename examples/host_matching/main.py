from flask import Flask
from flask import url_for
from flask_admin import Admin
from flask_admin import BaseView
from flask_admin import expose


class FirstView(BaseView):
    @expose("/")
    def index(self):
        return self.render("first.html")


class SecondView(BaseView):
    @expose("/")
    def index(self):
        return self.render("second.html")


class ThirdViewAllHosts(BaseView):
    @expose("/")
    def index(self):
        return self.render("third.html")


app = Flask(
    __name__,
    template_folder="templates",
    host_matching=True,
    static_host="static.localhost:5000",
)


@app.route("/", host="<anyhost>")
def index(anyhost):
    admin_host = url_for("admin3.index", admin_routes_host="anything.localhost:5000")
    return (
        f'<a href="{url_for("admin.index")}">Click me to get to Admin 1</a>'
        f"<br/>"
        f'<a href="{url_for("admin2.index")}">Click me to get to Admin 2</a>'
        f"<br/>"
        f'<a href="{admin_host}">Click me to get to Admin 3 under '
        f"`anything.localhost:5000`</a>"
    )


if __name__ == "__main__":
    # Create first administrative interface at `first.localhost:5000/admin1`
    admin1 = Admin(app, url="/admin1", host="first.localhost:5000")
    admin1.add_view(FirstView())

    # Create second administrative interface at `second.localhost:5000/admin2`
    admin2 = Admin(app, url="/admin2", endpoint="admin2", host="second.localhost:5000")
    admin2.add_view(SecondView())

    # Create third administrative interface, available on any domain at `/admin3`
    admin3 = Admin(app, url="/admin3", endpoint="admin3", host="*")
    admin3.add_view(ThirdViewAllHosts())

    app.run(debug=True)
