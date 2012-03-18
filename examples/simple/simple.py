from flask import Flask, render_template

from flask.ext import adminex


# Create custom admin view
class MyAdminView(adminex.BaseView):
    @adminex.expose('/')
    def index(self):
        return render_template('myadmin.html', view=self)


class AnotherAdminView(adminex.BaseView):
    @adminex.expose('/')
    def index(self):
        return render_template('anotheradmin.html', view=self)

    @adminex.expose('/test/')
    def test(self):
        return render_template('test.html', view=self)


# Create flask app
app = Flask(__name__, template_folder='templates')


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin interface
    admin = adminex.Admin()
    admin.add_view(MyAdminView(category='Test'))
    admin.add_view(AnotherAdminView(category='Test'))
    admin.apply(app)

    # Start app
    app.debug = True
    app.run()
