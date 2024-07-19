from flask_admin import AdminIndexView, expose
from config import FlaskAdminConfig

class IndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('index.html',
            basic_admin_bootswatch_theme=FlaskAdminConfig.BASIC_ADMIN_BOOTSWATCH_THEME,
            super_admin_bootswatch_theme=FlaskAdminConfig.SUPER_ADMIN_BOOTSWATCH_THEME
        )
