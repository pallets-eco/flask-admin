from flask import Flask

import flask_admin as admin


# Views
class FirstView(admin.BaseView):
    @admin.expose('/')
    def index(self):
        return self.render('first.html')


class SecondView(admin.BaseView):
    @admin.expose('/')
    def index(self):
        return self.render('second.html')


# Create flask app
app = Flask(__name__, template_folder='templates')


# Flask views
@app.route('/')
def index():
    return '<a href="/admin1">Click me to get to Admin 1</a><br/><a href="/admin2">Click me to get to Admin 2</a>'


if __name__ == '__main__':
    # Create first administrative interface under /admin1
    admin1 = admin.Admin(app, url='/admin1')
    admin1.add_view(FirstView())

    # Create second administrative interface under /admin2
    admin2 = admin.Admin(app, url='/admin2', endpoint='admin2')
    admin2.add_view(SecondView())

    # Start app
    app.run(debug=True)
