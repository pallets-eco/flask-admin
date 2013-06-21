from nose.tools import eq_, ok_
import os.path as op

from flask.ext.admin.contrib import fileadmin

from . import setup


def create_view():
    app, admin = setup()

    path = op.join(op.dirname(__file__), 'files')
    view = fileadmin.FileAdmin(path, '/files/', name='Files')
    admin.add_view(view)

    return app, admin, view


def test_file_admin():
    app, admin, view = create_view()

    client = app.test_client()

    rv = client.get('/admin/fileadmin/')
    eq_(rv.status_code, 200)
    ok_('dummy.txt' in rv.data.decode('utf-8'))

    # TODO: Check actions, etc
