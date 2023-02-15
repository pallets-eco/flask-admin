from . import setup
from .test_basic import CustomModelView

from flask_sqlalchemy import Model
from sqlalchemy.ext.declarative import declarative_base


def test_multiple_pk():
    # Test multiple primary keys - mix int and string together
    app, db, admin = setup()

    with app.app_context():
        class Model(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            id2 = db.Column(db.String(20), primary_key=True)
            test = db.Column(db.String)

        db.create_all()

        view = CustomModelView(Model, db.session, form_columns=['id', 'id2', 'test'])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get('/admin/model/')
        assert rv.status_code == 200

        rv = client.post('/admin/model/new/',
                         data=dict(id=1, id2='two', test='test3'))
        assert rv.status_code == 302

        rv = client.get('/admin/model/')
        assert rv.status_code == 200
        data = rv.data.decode('utf-8')
        assert 'test3' in data

        rv = client.get('/admin/model/edit/?id=1,two')
        assert rv.status_code == 200
        data = rv.data.decode('utf-8')
        assert 'test3' in data

        # Correct order is mandatory -> fail here
        rv = client.get('/admin/model/edit/?id=two,1')
        assert rv.status_code == 302


def test_joined_inheritance():
    # Test multiple primary keys - mix int and string together
    app, db, admin = setup()

    with app.app_context():
        class Parent(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            test = db.Column(db.String)

            discriminator = db.Column('type', db.String(50))
            __mapper_args__ = {'polymorphic_on': discriminator}

        class Child(Parent):
            __tablename__ = 'children'
            __mapper_args__ = {'polymorphic_identity': 'child'}

            id = db.Column(db.ForeignKey(Parent.id), primary_key=True)
            name = db.Column(db.String(100))

        db.create_all()

        view = CustomModelView(Child, db.session, form_columns=['id', 'test', 'name'])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get('/admin/child/')
        assert rv.status_code == 200

        rv = client.post('/admin/child/new/',
                         data=dict(id=1, test='foo', name='bar'))
        assert rv.status_code == 302

        rv = client.get('/admin/child/edit/?id=1')
        assert rv.status_code == 200
        data = rv.data.decode('utf-8')
        assert 'foo' in data
        assert 'bar' in data


def test_single_table_inheritance():
    # Test multiple primary keys - mix int and string together
    app, db, admin = setup()

    with app.app_context():
        CustomModel = declarative_base(cls=Model, name='Model')

        class Parent(CustomModel):
            __tablename__ = 'parent'

            id = db.Column(db.Integer, primary_key=True)
            test = db.Column(db.String)

            discriminator = db.Column('type', db.String(50))
            __mapper_args__ = {'polymorphic_on': discriminator}

        class Child(Parent):
            __mapper_args__ = {'polymorphic_identity': 'child'}
            name = db.Column(db.String(100))

        CustomModel.metadata.create_all(db.engine)

        view = CustomModelView(Child, db.session, form_columns=['id', 'test', 'name'])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get('/admin/child/')
        assert rv.status_code == 200

        rv = client.post('/admin/child/new/',
                         data=dict(id=1, test='foo', name='bar'))
        assert rv.status_code == 302

        rv = client.get('/admin/child/edit/?id=1')
        assert rv.status_code == 200
        data = rv.data.decode('utf-8')
        assert 'foo' in data
        assert 'bar' in data


def test_concrete_table_inheritance():
    # Test multiple primary keys - mix int and string together
    app, db, admin = setup()

    with app.app_context():
        class Parent(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            test = db.Column(db.String)

        class Child(Parent):
            __mapper_args__ = {'concrete': True}
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(100))
            test = db.Column(db.String)

        db.create_all()

        view = CustomModelView(Child, db.session, form_columns=['id', 'test', 'name'])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get('/admin/child/')
        assert rv.status_code == 200

        rv = client.post('/admin/child/new/',
                         data=dict(id=1, test='foo', name='bar'))
        assert rv.status_code == 302

        rv = client.get('/admin/child/edit/?id=1')
        assert rv.status_code == 200
        data = rv.data.decode('utf-8')
        assert 'foo' in data
        assert 'bar' in data


def test_concrete_multipk_inheritance():
    # Test multiple primary keys - mix int and string together
    app, db, admin = setup()

    with app.app_context():
        class Parent(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            test = db.Column(db.String)

        class Child(Parent):
            __mapper_args__ = {'concrete': True}
            id = db.Column(db.Integer, primary_key=True)
            id2 = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(100))
            test = db.Column(db.String)

        db.create_all()

        view = CustomModelView(Child, db.session, form_columns=['id', 'id2', 'test', 'name'])
        admin.add_view(view)

        client = app.test_client()

        rv = client.get('/admin/child/')
        assert rv.status_code == 200

        rv = client.post('/admin/child/new/',
                         data=dict(id=1, id2=2, test='foo', name='bar'))
        assert rv.status_code == 302

        rv = client.get('/admin/child/edit/?id=1,2')
        assert rv.status_code == 200
        data = rv.data.decode('utf-8')
        assert 'foo' in data
        assert 'bar' in data
