from . import setup
from .test_basic import CustomModelView, create_models

from flask_admin.form import rules


def test_form_rules():
    app, db, admin = setup()

    Model1, _ = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session,
                           form_rules=('test2', 'test1', rules.Field('test4')))
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1/new/')
    assert rv.status_code == 200

    data = rv.data.decode('utf-8')
    pos1 = data.find('Test1')
    pos2 = data.find('Test2')
    pos3 = data.find('Test3')
    pos4 = data.find('Test4')
    assert pos1 > pos2
    assert pos4 > pos1
    assert pos3 == -1


def test_rule_macro():
    app, db, admin = setup()

    Model1, _ = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session,
                           create_template='macro.html',
                           form_create_rules=(rules.Macro('test', arg='foobar'),
                                              rules.Macro('test_lib.another_test')))
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1/new/')
    assert rv.status_code == 200

    data = rv.data.decode('utf-8')
    assert 'Value = foobar' in data
    assert 'Hello another_test' in data


def test_rule_container():
    app, db, admin = setup()

    Model1, _ = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session,
                           create_template='macro.html',
                           form_create_rules=(rules.Container('wrap', rules.Macro('test_lib.another_test')),))
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1/new/')
    assert rv.status_code == 200

    data = rv.data.decode('utf-8')
    pos1 = data.find('<wrapper>')
    pos2 = data.find('another_test')
    pos3 = data.find('</wrapper>')
    assert pos1 != -1
    assert pos2 != -1
    assert pos3 != -1
    assert pos1 < pos2 < pos3


def test_rule_header():
    app, db, admin = setup()

    Model1, _ = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session,
                           form_create_rules=(rules.Header('hello'),))
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1/new/')
    assert rv.status_code == 200

    data = rv.data.decode('utf-8')
    assert '<h3>hello</h3>' in data


def test_rule_field_set():
    app, db, admin = setup()

    Model1, _ = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session,
                           form_create_rules=(rules.FieldSet(['test2', 'test1', 'test4'], 'header'),))
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1/new/')
    assert rv.status_code == 200

    data = rv.data.decode('utf-8')
    assert '<h3>header</h3>' in data
    pos1 = data.find('Test1')
    pos2 = data.find('Test2')
    pos3 = data.find('Test3')
    pos4 = data.find('Test4')
    assert pos1 > pos2
    assert pos4 > pos1
    assert pos3 == -1


def test_rule_inlinefieldlist():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session,
                           inline_models=(Model2,),
                           form_create_rules=('test1', 'model2'))
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1/new/')
    assert rv.status_code == 200


def test_inline_model_rules():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session,
                           inline_models=[(Model2, dict(form_rules=('string_field', 'bool_field')))])
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1/new/')
    assert rv.status_code == 200

    data = rv.data.decode('utf-8')
    assert 'int_field' not in data
