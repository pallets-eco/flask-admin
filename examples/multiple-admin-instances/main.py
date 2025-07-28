from flask import Flask
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


app = Flask(__name__, template_folder="templates")
admin1 = Admin(app, url="/admin1")
admin2 = Admin(app, url="/admin2", endpoint="admin2")


@app.route("/")
def index():
    return (
        '<a href="/admin1">Click me to get to Admin 1</a><br/><a href="/admin2">'
        "Click me to get to Admin 2</a>"
    )


if __name__ == "__main__":
    admin1.add_view(FirstView())
    admin2.add_view(SecondView())
    app.run(debug=True)
