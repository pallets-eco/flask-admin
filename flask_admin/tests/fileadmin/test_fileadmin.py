import os.path as op

from nose.tools import eq_, ok_

from flask.ext.admin.contrib import fileadmin

from . import setup

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def create_view():
    app, admin = setup()

    class MyFileAdmin(fileadmin.FileAdmin):
        editable_extensions = ('txt',)

    path = op.join(op.dirname(__file__), 'files')
    view = MyFileAdmin(path, '/files/', name='Files')
    admin.add_view(view)

    return app, admin, view


def test_file_admin():
    app, admin, view = create_view()

    client = app.test_client()

    # index
    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_('path=dummy.txt' in rv.data.decode('utf-8'))

    # edit
    rv = client.get('/admin/myfileadmin/edit/?path=dummy.txt')
    eq_(rv.status_code, 200)
    ok_('dummy.txt' in rv.data.decode('utf-8'))

    rv = client.post('/admin/myfileadmin/edit/?path=dummy.txt', data=dict(
        content='new_string'
    ))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/myfileadmin/edit/?path=dummy.txt')
    eq_(rv.status_code, 200)
    ok_('dummy.txt' in rv.data.decode('utf-8'))
    ok_('new_string' in rv.data.decode('utf-8'))

    # rename
    rv = client.get('/admin/myfileadmin/rename/?path=dummy.txt')
    eq_(rv.status_code, 200)
    ok_('dummy.txt' in rv.data.decode('utf-8'))

    rv = client.post('/admin/myfileadmin/rename/?path=dummy.txt', data=dict(
        name='dummy_renamed.txt',
        path='dummy.txt'
    ))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_('path=dummy_renamed.txt' in rv.data.decode('utf-8'))
    ok_('path=dummy.txt' not in rv.data.decode('utf-8'))

    # upload
    rv = client.get('/admin/myfileadmin/upload/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/myfileadmin/upload/', data=dict(
        upload=(StringIO(""), 'dummy.txt'),
    ))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_('path=dummy.txt' in rv.data.decode('utf-8'))
    ok_('path=dummy_renamed.txt' in rv.data.decode('utf-8'))

    # delete
    rv = client.post('/admin/myfileadmin/delete/', data=dict(
        path='dummy_renamed.txt'
    ))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_('path=dummy_renamed.txt' not in rv.data.decode('utf-8'))
    ok_('path=dummy.txt' in rv.data.decode('utf-8'))

    # mkdir
    rv = client.get('/admin/myfileadmin/mkdir/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/myfileadmin/mkdir/', data=dict(
        name='dummy_dir'
    ))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_('path=dummy.txt' in rv.data.decode('utf-8'))
    ok_('path=dummy_dir' in rv.data.decode('utf-8'))

    # rename - directory
    rv = client.get('/admin/myfileadmin/rename/?path=dummy_dir')
    eq_(rv.status_code, 200)
    ok_('dummy_dir' in rv.data.decode('utf-8'))

    rv = client.post('/admin/myfileadmin/rename/?path=dummy_dir', data=dict(
        name='dummy_renamed_dir',
        path='dummy_dir'
    ))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_('path=dummy_renamed_dir' in rv.data.decode('utf-8'))
    ok_('path=dummy_dir' not in rv.data.decode('utf-8'))

    # delete - directory
    rv = client.post('/admin/myfileadmin/delete/', data=dict(
        path='dummy_renamed_dir'
    ))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_('path=dummy_renamed_dir' not in rv.data.decode('utf-8'))
    ok_('path=dummy.txt' in rv.data.decode('utf-8'))
