from flask import Flask
from flask import redirect
from flask import request
from flask.views import MethodView
from flask_admin import Admin
from flask_admin import BaseView
from flask_admin import expose
from flask_admin import expose_plugview

app = Flask(__name__, template_folder="templates")
admin = Admin(app, name="Example: MethodView")


@app.route("/")
def index():
    return redirect("/admin")


class ViewWithMethodViews(BaseView):
    @expose("/")
    def index(self):
        return self.render("methodtest.html")

    @expose_plugview("/_api/1")
    class API_v1(MethodView):
        def get(self, cls):
            return cls.render("test.html", request=request, name="API_v1")

        def post(self, cls):
            return cls.render("test.html", request=request, name="API_v1")

    @expose_plugview("/_api/2")
    class API_v2(MethodView):
        def get(self, cls):
            return cls.render("test.html", request=request, name="API_v2")

        def post(self, cls):
            return cls.render("test.html", request=request, name="API_v2")


if __name__ == "__main__":
    admin.add_view(ViewWithMethodViews())

    app.run(debug=True)
