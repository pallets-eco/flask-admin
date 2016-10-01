import os.path as op
import pytest

PIL = pytest.importorskip("PIL.Image")

from flask_admin.contrib import fileadmin
from flask_admin import Admin
from flask import Flask

from . import setup

# confusion
try:
    from io import StringIO
except ImportError:
    from io import StringIO


def setup():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1123321sgdsfgdfgfddfcxvbbnhjtyutiutiuiui'
    app.config['CSRF_ENABLED'] = False

    admin = Admin(app)
    return app, admin


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
    assert rv.status_code == 200
    assert 'path=dummy.txt' in rv.data.decode('utf-8')

    # edit
    rv = client.get('/admin/myfileadmin/edit/?path=dummy.txt')
    assert rv.status_code == 200
    assert 'dummy.txt' in rv.data.decode('utf-8')

    rv = client.post('/admin/myfileadmin/edit/?path=dummy.txt', data=dict(
        content='new_string'
    ))
    assert rv.status_code == 302

    rv = client.get('/admin/myfileadmin/edit/?path=dummy.txt')
    assert rv.status_code == 200
    assert 'dummy.txt' in rv.data.decode('utf-8')
    assert 'new_string' in rv.data.decode('utf-8')

    # rename
    rv = client.get('/admin/myfileadmin/rename/?path=dummy.txt')
    assert rv.status_code == 200
    assert 'dummy.txt' in rv.data.decode('utf-8')

    rv = client.post('/admin/myfileadmin/rename/?path=dummy.txt', data=dict(
        name='dummy_renamed.txt',
        path='dummy.txt'
    ))
    assert rv.status_code == 302

    rv = client.get('/admin/myfileadmin/')
    assert rv.status_code == 200
    assert 'path=dummy_renamed.txt' in rv.data.decode('utf-8')
    assert 'path=dummy.txt' not in rv.data.decode('utf-8')

    # upload
    rv = client.get('/admin/myfileadmin/upload/')
    assert rv.status_code == 200

    rv = client.post('/admin/myfileadmin/upload/', data=dict(
        upload=(StringIO(""), 'dummy.txt'),
    ))
    assert rv.status_code == 302

    rv = client.get('/admin/myfileadmin/')
    assert rv.status_code == 200
    assert 'path=dummy.txt' in rv.data.decode('utf-8')
    assert 'path=dummy_renamed.txt' in rv.data.decode('utf-8')

    # delete
    rv = client.post('/admin/myfileadmin/delete/', data=dict(
        path='dummy_renamed.txt'
    ))
    assert rv.status_code == 302

    rv = client.get('/admin/myfileadmin/')
    assert rv.status_code == 200
    assert 'path=dummy_renamed.txt' not in rv.data.decode('utf-8')
    assert 'path=dummy.txt' in rv.data.decode('utf-8')

    # mkdir
    rv = client.get('/admin/myfileadmin/mkdir/')
    assert rv.status_code == 200

    rv = client.post('/admin/myfileadmin/mkdir/', data=dict(
        name='dummy_dir'
    ))
    assert rv.status_code == 302

    rv = client.get('/admin/myfileadmin/')
    assert rv.status_code == 200
    assert 'path=dummy.txt' in rv.data.decode('utf-8')
    assert 'path=dummy_dir' in rv.data.decode('utf-8')

    # rename - directory
    rv = client.get('/admin/myfileadmin/rename/?path=dummy_dir')
    assert rv.status_code == 200
    assert 'dummy_dir' in rv.data.decode('utf-8')

    rv = client.post('/admin/myfileadmin/rename/?path=dummy_dir', data=dict(
        name='dummy_renamed_dir',
        path='dummy_dir'
    ))
    assert rv.status_code == 302

    rv = client.get('/admin/myfileadmin/')
    assert rv.status_code == 200
    assert 'path=dummy_renamed_dir' in rv.data.decode('utf-8')
    assert 'path=dummy_dir' not in rv.data.decode('utf-8')

    # delete - directory
    rv = client.post('/admin/myfileadmin/delete/', data=dict(
        path='dummy_renamed_dir'
    ))
    assert rv.status_code == 302

    rv = client.get('/admin/myfileadmin/')
    assert rv.status_code == 200
    assert 'path=dummy_renamed_dir' not in rv.data.decode('utf-8')
    assert 'path=dummy.txt' in rv.data.decode('utf-8')

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
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'fa_modal_window' in data

    # bootstrap 2 - test edit modal disabled
    rv = client_bs2.get('/admin/edit_modal_off/')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'fa_modal_window' not in data

    # bootstrap 3
    app_bs3 = Flask(__name__)
    admin_bs3 = Admin(app_bs3, template_mode="bootstrap3")

    admin_bs3.add_view(edit_modal_on)
    admin_bs3.add_view(edit_modal_off)

    client_bs3 = app_bs3.test_client()

    # bootstrap 3 - ensure modal window is added when edit_modal is enabled
    rv = client_bs3.get('/admin/edit_modal_on/')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'fa_modal_window' in data

    # bootstrap 3 - test modal disabled
    rv = client_bs3.get('/admin/edit_modal_off/')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'fa_modal_window' not in data
