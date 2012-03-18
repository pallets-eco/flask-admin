from flask import Flask, render_template

from flask.ext import extadmin


# Create custom admin view
class MyAdminView(extadmin.BaseView):
    @extadmin.expose('/')
    def index(self):
        return render_template('myadmin.html', view=self)


class AnotherAdminView(extadmin.BaseView):
    @extadmin.expose('/')
    def index(self):
        return render_template('anotheradmin.html', view=self)


# Create flask app
app = Flask(__name__, template_folder='templates')


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin interface
    admin = extadmin.Admin(app)
    admin.add_view(MyAdminView())
    admin.add_view(AnotherAdminView())

    # Start app
    app.debug = True
    app.run()
