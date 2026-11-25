from flask_admin import AdminIndexView
from flask_admin import expose


class IndexView(AdminIndexView):
    @expose("/")
    def index(self):
        return self.render("index.html")
