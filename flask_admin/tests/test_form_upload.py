import os
import os.path as op

from io import BytesIO

from nose.tools import eq_, ok_

from flask import Flask, url_for
from flask_admin import form, helpers


def _create_temp():
    path = op.join(op.dirname(__file__), 'tmp')
    if not op.exists(path):
        os.mkdir(path)

    inner = op.join(path, 'inner')
    if not op.exists(inner):
        os.mkdir(inner)

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
        upload = form.FileUploadField('Upload', base_path=path)

    class TestNoOverWriteForm(form.BaseForm):
        upload = form.FileUploadField('Upload', base_path=path, allow_overwrite=False)

    class Dummy(object):
        pass

    my_form = TestForm()
    eq_(my_form.upload.base_path, path)

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

    # Check overwrite
    _remove_testfiles()
    my_form_ow = TestNoOverWriteForm()
    with app.test_request_context(method='POST', data={'upload': (BytesIO(b'Hullo'), 'test1.txt')}):
        my_form_ow = TestNoOverWriteForm(helpers.get_form_data())

        ok_(my_form_ow.validate())
        my_form_ow.populate_obj(dummy)
        eq_(dummy.upload, 'test1.txt')
        ok_(op.exists(op.join(path, 'test1.txt')))

    with app.test_request_context(method='POST', data={'upload': (BytesIO(b'Hullo'), 'test1.txt')}):
        my_form_ow = TestNoOverWriteForm(helpers.get_form_data())

        ok_(not my_form_ow.validate())

    _remove_testfiles()


def test_image_upload_field():
    app = Flask(__name__)

    path = _create_temp()

    def _remove_testimages():
        safe_delete(path, 'test1.png')
        safe_delete(path, 'test1_thumb.jpg')
        safe_delete(path, 'test2.png')
        safe_delete(path, 'test2_thumb.jpg')
        safe_delete(path, 'test1.jpg')
        safe_delete(path, 'test1.jpeg')
        safe_delete(path, 'test1.gif')
        safe_delete(path, 'test1.png')
        safe_delete(path, 'test1.tiff')

    class TestForm(form.BaseForm):
        upload = form.ImageUploadField('Upload',
                                       base_path=path,
                                       thumbnail_size=(100, 100, True))

    class TestNoResizeForm(form.BaseForm):
        upload = form.ImageUploadField('Upload', base_path=path, endpoint='test')

    class TestAutoResizeForm(form.BaseForm):
        upload = form.ImageUploadField('Upload',
                                       base_path=path,
                                       max_size=(64, 64, True))

    class Dummy(object):
        pass

    my_form = TestForm()
    eq_(my_form.upload.base_path, path)
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
            ok_(op.exists(op.join(path, 'test1_thumb.png')))

    # Check replace
    with open(filename, 'rb') as fp:
        with app.test_request_context(method='POST', data={'upload': (fp, 'test2.png')}):
            my_form = TestForm(helpers.get_form_data())

            ok_(my_form.validate())

            my_form.populate_obj(dummy)

            eq_(dummy.upload, 'test2.png')
            ok_(op.exists(op.join(path, 'test2.png')))
            ok_(op.exists(op.join(path, 'test2_thumb.png')))

            ok_(not op.exists(op.join(path, 'test1.png')))
            ok_(not op.exists(op.join(path, 'test1_thumb.jpg')))

    # Check delete
    with app.test_request_context(method='POST', data={'_upload-delete': 'checked'}):
        my_form = TestForm(helpers.get_form_data())

        ok_(my_form.validate())

        my_form.populate_obj(dummy)
        eq_(dummy.upload, None)

        ok_(not op.exists(op.join(path, 'test2.png')))
        ok_(not op.exists(op.join(path, 'test2_thumb.png')))

    # Check upload no-resize
    with open(filename, 'rb') as fp:
        with app.test_request_context(method='POST', data={'upload': (fp, 'test1.png')}):
            my_form = TestNoResizeForm(helpers.get_form_data())

            ok_(my_form.validate())

            my_form.populate_obj(dummy)

            eq_(dummy.upload, 'test1.png')
            ok_(op.exists(op.join(path, 'test1.png')))
            ok_(not op.exists(op.join(path, 'test1_thumb.png')))

    # Check upload, auto-resize
    filename = op.join(op.dirname(__file__), 'data', 'copyleft.png')

    with open(filename, 'rb') as fp:
        with app.test_request_context(method='POST', data={'upload': (fp, 'test1.png')}):
            my_form = TestAutoResizeForm(helpers.get_form_data())

            ok_(my_form.validate())

            my_form.populate_obj(dummy)

            eq_(dummy.upload, 'test1.png')
            ok_(op.exists(op.join(path, 'test1.png')))

    filename = op.join(op.dirname(__file__), 'data', 'copyleft.tiff')

    with open(filename, 'rb') as fp:
        with app.test_request_context(method='POST', data={'upload': (fp, 'test1.tiff')}):
            my_form = TestAutoResizeForm(helpers.get_form_data())

            ok_(my_form.validate())

            my_form.populate_obj(dummy)

            eq_(dummy.upload, 'test1.jpg')
            ok_(op.exists(op.join(path, 'test1.jpg')))


    # check allowed extensions
    for extension in ('gif', 'jpg', 'jpeg', 'png', 'tiff'):
        filename = 'copyleft.' + extension
        filepath = op.join(op.dirname(__file__), 'data', filename)
        with open(filepath, 'rb') as fp:
            with app.test_request_context(method='POST', data={'upload': (fp, filename)}):
                my_form = TestNoResizeForm(helpers.get_form_data())
                ok_(my_form.validate())
                my_form.populate_obj(dummy)
                eq_(dummy.upload, my_form.upload.data.filename)

    # check case-sensitivity for extensions
    filename = op.join(op.dirname(__file__), 'data', 'copyleft.jpg')
    with open(filename, 'rb') as fp:
        with app.test_request_context(method='POST', data={'upload': (fp, 'copyleft.JPG')}):
            my_form = TestNoResizeForm(helpers.get_form_data())
            ok_(my_form.validate())


def test_relative_path():
    app = Flask(__name__)

    path = _create_temp()

    def _remove_testfiles():
        safe_delete(path, 'test1.txt')

    class TestForm(form.BaseForm):
        upload = form.FileUploadField('Upload', base_path=path, relative_path='inner/')

    class Dummy(object):
        pass

    my_form = TestForm()
    eq_(my_form.upload.base_path, path)
    eq_(my_form.upload.relative_path, 'inner/')

    _remove_testfiles()

    dummy = Dummy()

    # Check upload
    with app.test_request_context(method='POST', data={'upload': (BytesIO(b'Hello World 1'), 'test1.txt')}):
        my_form = TestForm(helpers.get_form_data())

        ok_(my_form.validate())

        my_form.populate_obj(dummy)

        eq_(dummy.upload, 'inner/test1.txt')
        ok_(op.exists(op.join(path, 'inner/test1.txt')))

        eq_(url_for('static', filename=dummy.upload), '/static/inner/test1.txt')
