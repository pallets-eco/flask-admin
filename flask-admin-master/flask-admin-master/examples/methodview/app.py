from flask import Flask, redirect, request

import flask_admin as admin
from flask.views import MethodView


class ViewWithMethodViews(admin.BaseView):
    @admin.expose('/')
    def index(self):
        return self.render('methodtest.html')

    @admin.expose_plugview('/_api/1')
    class API_v1(MethodView):
        def get(self, cls):
            return cls.render('test.html', request=request, name="API_v1")

        def post(self, cls):
            return cls.render('test.html', request=request, name="API_v1")

    @admin.expose_plugview('/_api/2')
    class API_v2(MethodView):
        def get(self, cls):
            return cls.render('test.html', request=request, name="API_v2")

        def post(self, cls):
            return cls.render('test.html', request=request, name="API_v2")


# Create flask app
app = Flask(__name__, template_folder='templates')


# Flask views
@app.route('/')
def index():
    return redirect('/admin')


if __name__ == '__main__':
    # Create admin interface
    admin = admin.Admin(name="Example: MethodView")
    admin.add_view(ViewWithMethodViews())
    admin.init_app(app)

    # Start app
    app.run(debug=True)
