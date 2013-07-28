import os
import os.path as op

from io import BytesIO

from nose.tools import eq_, ok_

from flask import Flask
from flask.ext.admin import form, helpers


def _create_temp():
    path = op.join(op.dirname(__file__), 'tmp')
    if not op.exists(path):
        os.mkdir(path)
    return path


def safe_delete(path, name):
    try:
        os.remove(op.join(path, name))
    except:
        pass


def test_upload_field():
    app = Flask(__name__)

    path = _create_temp()

    def _remove_testfiles():
        safe_delete(path, 'test1.txt')
        safe_delete(path, 'test2.txt')

    class TestForm(form.BaseForm):
        upload = form.FileUploadField('Upload', path=path)

    class Dummy(object):
        pass

    my_form = TestForm()
    eq_(my_form.upload.path, path)

    _remove_testfiles()

    dummy = Dummy()

    # Check upload
    with app.test_request_context(method='POST', data={'upload': (BytesIO(b'Hello World 1'), 'test1.txt')}):
        my_form = TestForm(helpers.get_form_data())

        ok_(my_form.validate())

        my_form.populate_obj(dummy)

        eq_(dummy.upload, 'test1.txt')
        ok_(op.exists(op.join(path, 'test1.txt')))

    # Check replace
    with app.test_request_context(method='POST', data={'upload': (BytesIO(b'Hello World 2'), 'test2.txt')}):
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
        eq_(dummy.upload, None)

        ok_(not op.exists(op.join(path, 'test2.txt')))


def test_image_upload_field():
    app = Flask(__name__)

    path = _create_temp()

    def _remove_testimages():
        safe_delete(path, 'test1.png')
        safe_delete(path, 'test1_thumb.jpg')
        safe_delete(path, 'test2.png')
        safe_delete(path, 'test2_thumb.jpg')

    class TestForm(form.BaseForm):
        upload = form.ImageUploadField('Upload', path=path, thumbnail_size=(100, 100, True))

    class TestNoResizeForm(form.BaseForm):
        upload = form.ImageUploadField('Upload', path=path)

    class Dummy(object):
        pass

    my_form = TestForm()
    eq_(my_form.upload.path, path)
    eq_(my_form.upload.endpoint, 'static')

    _remove_testimages()

    dummy = Dummy()

    # Check upload
    filename = op.join(op.dirname(__file__), 'data', 'copyleft.png')

    with open(filename, 'rb') as fp:
        with app.test_request_context(method='POST', data={'upload': (fp, 'test1.png')}):
            my_form = TestForm(helpers.get_form_data())

            ok_(my_form.validate())

            my_form.populate_obj(dummy)

            eq_(dummy.upload, 'test1.png')
            ok_(op.exists(op.join(path, 'test1.png')))
            ok_(op.exists(op.join(path, 'test1_thumb.jpg')))

    # Check replace
    with open(filename, 'rb') as fp:
        with app.test_request_context(method='POST', data={'upload': (fp, 'test2.png')}):
            my_form = TestForm(helpers.get_form_data())

            ok_(my_form.validate())

            my_form.populate_obj(dummy)

            eq_(dummy.upload, 'test2.png')
            ok_(op.exists(op.join(path, 'test2.png')))
            ok_(op.exists(op.join(path, 'test2_thumb.jpg')))

            ok_(not op.exists(op.join(path, 'test1.png')))
            ok_(not op.exists(op.join(path, 'test1_thumb.jpg')))

    # Check delete
    with app.test_request_context(method='POST', data={'_upload-delete': 'checked'}):
        my_form = TestForm(helpers.get_form_data())

        ok_(my_form.validate())

        my_form.populate_obj(dummy)
        eq_(dummy.upload, None)

        ok_(not op.exists(op.join(path, 'test2.png')))
        ok_(not op.exists(op.join(path, 'test2_thumb.jpg')))

    # Check upload no-resize
    with open(filename, 'rb') as fp:
        with app.test_request_context(method='POST', data={'upload': (fp, 'test1.png')}):
            my_form = TestNoResizeForm(helpers.get_form_data())

            ok_(my_form.validate())

            my_form.populate_obj(dummy)

            eq_(dummy.upload, 'test1.png')
            ok_(op.exists(op.join(path, 'test1.png')))
            ok_(not op.exists(op.join(path, 'test1_thumb.jpg')))
