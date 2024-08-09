from flask import request, redirect, flash, url_for
from flask_admin import AdminIndexView, expose
from config import MyConfig


class IndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('index.html',
            bt=MyConfig.BASIC_ADMIN_BOOTSWATCH_THEME,
            st=MyConfig.SUPER_ADMIN_BOOTSWATCH_THEME
        )

    @expose('/change/theme/swatch/<swatch_name>/', methods=['GET'])
    def change_theme_swatch(self, swatch_name):
        if swatch_name in MyConfig.SWATCH_THEMES:
            self.admin.theme.swatch = swatch_name   # type: ignore
            if self.admin.name == 'BasicAdmin':  # type: ignore
                MyConfig.BASIC_ADMIN_BOOTSWATCH_THEME = swatch_name
            elif self.admin.name == 'SuperAdmin':   # type: ignore
                MyConfig.SUPER_ADMIN_BOOTSWATCH_THEME = swatch_name

            flash('Swatch theme changed!', 'success')
            return redirect(request.args.get('redirect', url_for('.index')))
        else:
            flash('Swatch theme not found.', 'danger')
            return redirect(request.args.get('redirect', url_for('.index')))
