from flask import Flask
from flask.ext.adminex import Admin, BaseView, expose

class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')

app = Flask(__name__)

admin = Admin(app)
admin.add_view(MyView(name='Hello 1', endpoint='test1', category='Test'))
admin.add_view(MyView(name='Hello 2', endpoint='test2', category='Test'))
admin.add_view(MyView(name='Hello 3', endpoint='test3', category='Test'))
app.run()
