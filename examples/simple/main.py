from flask import Flask
from flask_admin import Admin
from flask_admin import BaseView
from flask_admin import expose
from flask_admin.theme import Bootstrap4Theme

app = Flask(__name__, template_folder="templates")
app.debug = True
admin = Admin(app, name="Example: Simple Views", theme=Bootstrap4Theme())


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


class MyAdminView(BaseView):
    @expose("/")
    def index(self):
        return self.render("myadmin.html")


class AnotherAdminView(BaseView):
    @expose("/")
    def index(self):
        return self.render("anotheradmin.html")

    @expose("/test/")
    def test(self):
        return self.render("test.html")


if __name__ == "__main__":
    admin.add_view(MyAdminView(name="view1", category="Test"))
    admin.add_view(AnotherAdminView(name="view2", category="Test"))
    app.run(debug=True)
