from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from .views import IndexView
from config import FlaskAdminConfig
from models import User, Post, db


class UserModelView(ModelView):
    column_editable_list = ['active']
    can_view_details = True

class PostModelView(ModelView):
    column_list = ['id', 'title', 'body', 'author', 'created_at']
    column_editable_list = ['title']


admin = Admin(
    name='SuperAdmin',
    base_template='master.html',
    template_mode='bootstrap3',
    bootswatch_theme=FlaskAdminConfig.SUPER_ADMIN_BOOTSWATCH_THEME,
    index_view=IndexView('Home', endpoint='superadmin', url='/superadmin'),
)

admin.add_view(UserModelView(User, db.session, name='Users', endpoint='s/user'))
admin.add_view(PostModelView(Post, db.session, name='Posts', endpoint='s/posts'))

