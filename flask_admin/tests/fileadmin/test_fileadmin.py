import os
import os.path as op

from nose.tools import eq_, ok_, with_setup

from flask_admin.contrib import fileadmin
from flask_admin import Admin
from flask import Flask

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


def add_file():
    # make sure that 'files/dummy2.txt' exists, is newest and has bigger size
    with open(op.join(op.dirname(__file__), 'files', 'dummy2.txt'), 'w') as fp:
        fp.write('test')


def remove_file():
    try:
        os.remove(op.join(op.dirname(__file__), 'files', 'dummy2.txt'))
    except (IOError, OSError):
        pass


@with_setup(add_file, remove_file)
def test_fileadmin_sort_default():
    app, admin, view = create_view()
    client = app.test_client()

    # default sort order is newest first
    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_(rv.data.decode('utf-8').find('path=dummy2.txt') <
        rv.data.decode('utf-8').find('path=dummy.txt'))


@with_setup(add_file, remove_file)
def test_fileadmin_sort_url_param_sort():
    app, admin, view = create_view()
    client = app.test_client()

    rv = client.get('/admin/myfileadmin/?sort=name')
    eq_(rv.status_code, 200)
    ok_(rv.data.decode('utf-8').find('path=dummy.txt') <
        rv.data.decode('utf-8').find('path=dummy2.txt'))


@with_setup(add_file, remove_file)
def test_fileadmin_sort_url_param_desc():
    app, admin, view = create_view()
    client = app.test_client()

    rv = client.get('/admin/myfileadmin/?sort=size')
    eq_(rv.status_code, 200)
    ok_(rv.data.decode('utf-8').find('path=dummy.txt') <
        rv.data.decode('utf-8').find('path=dummy2.txt'))


@with_setup(add_file, remove_file)
def test_fileadmin_sort_default_sort_column():
    app, admin, view = create_view()
    client = app.test_client()

    view.default_sort_column = 'name'
    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_(rv.data.decode('utf-8').find('path=dummy.txt') <
        rv.data.decode('utf-8').find('path=dummy2.txt'))


@with_setup(add_file, remove_file)
def test_fileadmin_sort_default_desc():
    app, admin, view = create_view()
    client = app.test_client()

    view.default_sort_column = 'name'
    view.default_desc = True
    rv = client.get('/admin/myfileadmin/')
    eq_(rv.status_code, 200)
    ok_(rv.data.decode('utf-8').find('path=dummy2.txt') <
        rv.data.decode('utf-8').find('path=dummy.txt'))


def test_modal_edit():
    # bootstrap 2 - test edit_modal
    app_bs2 = Flask(__name__)
    admin_bs2 = Admin(app_bs2, template_mode="bootstrap2")

    class EditModalOn(fileadmin.FileAdmin):
        edit_modal = True
        editable_extensions = ('txt',)

    class EditModalOff(fileadmin.FileAdmin):
        edit_modal = False
        editable_extensions = ('txt',)

    path = op.join(op.dirname(__file__), 'files')
    edit_modal_on = EditModalOn(path, '/files/', endpoint='edit_modal_on')
    edit_modal_off = EditModalOff(path, '/files/', endpoint='edit_modal_off')

    admin_bs2.add_view(edit_modal_on)
    admin_bs2.add_view(edit_modal_off)

    client_bs2 = app_bs2.test_client()

    # bootstrap 2 - ensure modal window is added when edit_modal is enabled
    rv = client_bs2.get('/admin/edit_modal_on/')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('fa_modal_window' in data)

    # bootstrap 2 - test edit modal disabled
    rv = client_bs2.get('/admin/edit_modal_off/')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('fa_modal_window' not in data)

    # bootstrap 3
    app_bs3 = Flask(__name__)
    admin_bs3 = Admin(app_bs3, template_mode="bootstrap3")

    admin_bs3.add_view(edit_modal_on)
    admin_bs3.add_view(edit_modal_off)

    client_bs3 = app_bs3.test_client()

    # bootstrap 3 - ensure modal window is added when edit_modal is enabled
    rv = client_bs3.get('/admin/edit_modal_on/')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('fa_modal_window' in data)

    # bootstrap 3 - test modal disabled
    rv = client_bs3.get('/admin/edit_modal_off/')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('fa_modal_window' not in data)
