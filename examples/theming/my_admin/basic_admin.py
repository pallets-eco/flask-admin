from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from config import MyConfig
from models import User, Post, db
from .views import IndexView


class UserModelView(ModelView):
    column_editable_list = ['active']
    can_edit = False
    can_create = False
    can_delete = False
    can_view_details = False


class PostModelView(ModelView):
    column_list = ['id', 'title', 'body', 'author', 'created_at']
    column_editable_list = ['title']


admin = Admin(
    name='BasicAdmin',
    theme=Bootstrap4Theme(
        base_template='master.html',
        swatch=MyConfig.BASIC_ADMIN_BOOTSWATCH_THEME,
        fluid=False
    ),
    index_view=IndexView('Home', endpoint='basicadmin', url='/basicadmin'),
)


admin.add_view(UserModelView(User, db.session, name='Users', endpoint='b/users'))
admin.add_view(PostModelView(Post, db.session, name='Posts', endpoint='b/posts'))
