from flask.ext.adminex import base


class MockView(base.BaseView):
    # Various properties
    allow_call = True
    allow_access = True

    @base.expose('/')
    def index(self):
        return 'Success!'

    @base.expose('/test/')
    def test(self):
        return self.render('mock.html')

    def _handle_view(self, name, **kwargs):
        if self.allow_call:
            return super(MockView, self)._handle_view(name, **kwargs)
        else:
            return 'Failure!'

    def is_accessible(self):
        if self.allow_access:
            return super(MockView, self).is_accessible()
        else:
            return False
