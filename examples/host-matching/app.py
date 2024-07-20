from flask import Flask, url_for

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


class ThirdViewAllHosts(admin.BaseView):
    @admin.expose('/')
    def index(self):
        return self.render('third.html')


# Create flask app
app = Flask(__name__, template_folder='templates', host_matching=True, static_host='static.localhost:5000')


# Flask views
@app.route('/', host='<anyhost>')
def index(anyhost):
    return (
        f'<a href="{url_for("admin.index")}">Click me to get to Admin 1</a>'
        f'<br/>'
        f'<a href="{url_for("admin2.index")}">Click me to get to Admin 2</a>'
        f'<br/>'
        f'<a href="{url_for("admin3.index", admin_routes_host="anything.localhost:5000")}">Click me to get to Admin 3 under `anything.localhost:5000`</a>'
    )


if __name__ == '__main__':
    # Create first administrative interface at `first.localhost:5000/admin1`
    admin1 = admin.Admin(app, url='/admin1', host='first.localhost:5000')
    admin1.add_view(FirstView())

    # Create second administrative interface at `second.localhost:5000/admin2`
    admin2 = admin.Admin(app, url='/admin2', endpoint='admin2', host='second.localhost:5000')
    admin2.add_view(SecondView())

    # Create third administrative interface, available on any domain at `/admin3`
    admin3 = admin.Admin(app, url='/admin3', endpoint='admin3', host='*')
    admin3.add_view(ThirdViewAllHosts())

    # Start app
    app.run(debug=True)
