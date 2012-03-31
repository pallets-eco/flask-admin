from flask.ext.adminex import base


class MockView(base.BaseView):
    @base.expose('/')
    def index(self):
        return None
