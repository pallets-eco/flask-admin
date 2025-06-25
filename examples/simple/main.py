from flask import Flask
from flask_admin import Admin
from flask_admin import BaseView
from flask_admin import expose
from flask_admin.theme import Bootstrap4Theme


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


app = Flask(__name__, template_folder="templates")
app.debug = True


# Flask views
@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Create admin interface
admin = Admin(name="Example: Simple Views", theme=Bootstrap4Theme())
admin.add_view(MyAdminView(name="view1", category="Test"))
admin.add_view(AnotherAdminView(name="view2", category="Test"))
admin.init_app(app)

if __name__ == "__main__":
    # Start app
    app.run()
