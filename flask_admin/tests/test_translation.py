# -*- coding: utf-8 -*-
import re
from nose.tools import eq_, ok_

from flask_babelex import Babel
from flask import Flask
from flask_admin import Admin
from flask_admin.babel import lazy_gettext
from .test_model import MockModelView, Model


def init_admin(template_mode='bootstrap3', lang='es'):
    app = Flask(__name__)
    app.config['CSRF_ENABLED'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = lang
    app.secret_key = '1'
    Babel(app)
    admin = Admin(app, template_mode=template_mode)

    return app, admin


def test_model_list_components_translation():
    for template_mode in ['bootstrap2', 'bootstrap3']:
        yield check_model_list_components_translation, template_mode


def check_model_list_components_translation(template_mode):
    app, admin = init_admin(template_mode=template_mode)

    label = lazy_gettext('Name')
    view = MockModelView(Model,
                         column_list=['test1', 'test3'],
                         column_labels=dict(test1=label),
                         column_filters=('test1',))
    admin.add_view(view)
    client = app.test_client()

    rv = client.get('/admin/model/')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')

    regex = re.compile('<th[^>]*>\s+(.*)\s+</th>')
    column_names = re.findall(regex, rv.data)
    ok_('Nombre' in column_names)
    ok_('title="Borrar registro"' in data)
    ok_('title="Editar Registro"' in data)

    client.post('/admin/model/delete/?id=2')
    rv = client.get('/admin/model/')
    ok_(u'El elemento se ha borrado correctamente.' in rv.data.decode('utf-8'))

    # TODO: Make calls with filters
    # rv = client.get('/admin/model/?flt1_0=test')
    # eq_(rv.status_code, 200)
    # ok_('{"Nombre":' in rv.data.decode('utf-8'))
