import os
import os.path as op
from StringIO import StringIO

from nose.tools import eq_, ok_

from flask import Flask
from flask.ext.admin import form, helpers


def _create_temp():
    path = op.join(op.dirname(__file__), 'tmp')
    if not op.exists(path):
        os.mkdir(path)
    return path


def _remove_testfiles(path):
    try:
        os.remove(op.join(path, 'test1.txt'))
        os.remove(op.join(path, 'test2.txt'))
    except:
        pass


def test_upload_field():
    app = Flask(__name__)

    path = _create_temp()

    class TestForm(form.BaseForm):
        upload = form.FileUploadField('Upload', path=path)

    class Dummy(object):
        pass

    my_form = TestForm()
    eq_(my_form.upload.path, path)

    _remove_testfiles(path)

    dummy = Dummy()

    # Check upload
    with app.test_request_context(method='POST', data={'upload': (StringIO('Hello World'), 'test1.txt')}):
        my_form = TestForm(helpers.get_form_data())

        ok_(my_form.validate())

        my_form.populate_obj(dummy)

        eq_(dummy.upload, 'test1.txt')
        ok_(op.exists(op.join(path, 'test1.txt')))

    # Check replace
    with app.test_request_context(method='POST', data={'upload': (StringIO('Hello World'), 'test2.txt')}):
        my_form = TestForm(helpers.get_form_data())

        ok_(my_form.validate())
        my_form.populate_obj(dummy)

        eq_(dummy.upload, 'test2.txt')
        ok_(not op.exists(op.join(path, 'test1.txt')))
        ok_(op.exists(op.join(path, 'test2.txt')))

    # Check delete
    with app.test_request_context(method='POST', data={'_upload-delete': 'checked'}):
        my_form = TestForm(helpers.get_form_data())

        ok_(my_form.validate())

        my_form.populate_obj(dummy)

        ok_(not op.exists(op.join(path, 'test2.txt')))
