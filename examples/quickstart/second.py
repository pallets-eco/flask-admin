from flask import Flask
from flask.ext.adminex import Admin, BaseView, expose


class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')

app = Flask(__name__)

admin = Admin(app)
admin.add_view(MyView(name='Hello'))

app.run()
