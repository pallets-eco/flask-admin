import os
from flask_admin import Admin
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from config import MyConfig
from models import User, Post, db
from .views import IndexView


class UserModelView(ModelView):
    column_editable_list = ['active']
    can_view_details = True


class PostModelView(ModelView):
    column_list = ['id', 'title', 'body', 'author', 'created_at']
    column_editable_list = ['title']


admin = Admin(
    name='SuperAdmin',
    theme=Bootstrap4Theme(
        base_template='master.html',
        swatch=MyConfig.SUPER_ADMIN_BOOTSWATCH_THEME,
        fluid=False
    ),
    index_view=IndexView('Home', endpoint='superadmin', url='/superadmin'),
)


_path_filemanager = os.path.join(os.path.dirname(__file__), '../')
admin.add_view(FileAdmin(_path_filemanager, name='File Manager',
    endpoint='b/filemanager'))
admin.add_view(UserModelView(User, db.session, name='Users', endpoint='s/user'))
admin.add_view(PostModelView(Post, db.session, name='Posts', endpoint='s/posts'))
