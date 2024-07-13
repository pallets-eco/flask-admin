# -*- coding: utf-8 -*-
from wtforms import fields

from flask_admin import form
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import InlineModelFormList
from flask_admin.contrib.sqla.validators import ItemsRequired

from . import setup


def test_inline_form():
    app, db, admin = setup()

    with app.app_context():
        client = app.test_client()

        # Set up models and database
        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, unique=True)

            def __init__(self, name=None):
                self.name = name

        class UserInfo(db.Model):
            __tablename__ = 'user_info'
            id = db.Column(db.Integer, primary_key=True)
            key = db.Column(db.String, nullable=False)
            val = db.Column(db.String)
            user_id = db.Column(db.Integer, db.ForeignKey(User.id))
            user = db.relationship(User, backref=db.backref('info', cascade="all, delete-orphan", single_parent=True))

        db.create_all()

        # Set up Admin
        class UserModelView(ModelView):
            inline_models = (UserInfo,)

        view = UserModelView(User, db.session)
        admin.add_view(view)

        # Basic tests
        assert view._create_form_class is not None
        assert view._edit_form_class is not None
        assert view.endpoint == 'user'

        # Verify form
        assert view._create_form_class.name.field_class == fields.StringField
        assert view._create_form_class.info.field_class == InlineModelFormList

        rv = client.get('/admin/user/')
        assert rv.status_code == 200

        rv = client.get('/admin/user/new/')
        assert rv.status_code == 200

        # Create
        rv = client.post('/admin/user/new/', data=dict(name=u'äõüxyz'))
        assert rv.status_code == 302
        assert User.query.count() == 1
        assert UserInfo.query.count() == 0

        data = {'name': u'fbar', 'info-0-key': 'foo', 'info-0-val': 'bar'}
        rv = client.post('/admin/user/new/', data=data)
        assert rv.status_code == 302
        assert User.query.count() == 2
        assert UserInfo.query.count() == 1

        # Edit
        rv = client.get('/admin/user/edit/?id=2')
        assert rv.status_code == 200
        # Edit - update
        data = {
            'name': u'barfoo',
            'info-0-id': 1,
            'info-0-key': u'xxx',
            'info-0-val': u'yyy',
        }
        rv = client.post('/admin/user/edit/?id=2', data=data)
        assert UserInfo.query.count() == 1
        assert UserInfo.query.one().key == u'xxx'

        # Edit - add & delete
        data = {
            'name': u'barf',
            'del-info-0': 'on',
            'info-0-id': '1',
            'info-0-key': 'yyy',
            'info-0-val': 'xxx',
            'info-1-id': None,
            'info-1-key': u'bar',
            'info-1-val': u'foo',
        }
        rv = client.post('/admin/user/edit/?id=2', data=data)
        assert rv.status_code == 302
        assert User.query.count() == 2
        assert User.query.get(2).name == u'barf'
        assert UserInfo.query.count() == 1
        assert UserInfo.query.one().key == u'bar'

        # Delete
        rv = client.post('/admin/user/delete/?id=2')
        assert rv.status_code == 302
        assert User.query.count() == 1
        rv = client.post('/admin/user/delete/?id=1')
        assert rv.status_code == 302
        assert User.query.count() == 0
        assert UserInfo.query.count() == 0


def test_inline_form_required():
    app, db, admin = setup()

    with app.app_context():
        client = app.test_client()

        # Set up models and database
        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, unique=True)

            def __init__(self, name=None):
                self.name = name

        class UserEmail(db.Model):
            __tablename__ = 'user_info'
            id = db.Column(db.Integer, primary_key=True)
            email = db.Column(db.String, nullable=False, unique=True)
            verified_at = db.Column(db.DateTime)
            user_id = db.Column(db.Integer, db.ForeignKey(User.id))
            user = db.relationship(User, backref=db.backref('emails', cascade="all, delete-orphan", single_parent=True))

        db.create_all()

        # Set up Admin
        class UserModelView(ModelView):
            inline_models = (UserEmail,)
            form_args = {
                "emails": {"validators": [ItemsRequired()]}
            }

        view = UserModelView(User, db.session)
        admin.add_view(view)

        # Create
        rv = client.post('/admin/user/new/', data=dict(name=u'no-email'))
        assert rv.status_code == 200
        assert User.query.count() == 0

        data = {
            'name': 'hasEmail',
            'emails-0-email': 'foo@bar.com',
        }
        rv = client.post('/admin/user/new/', data=data)
        assert rv.status_code == 302
        assert User.query.count() == 1
        assert UserEmail.query.count() == 1

        # Attempted delete, prevented by ItemsRequired
        data = {
            'name': 'hasEmail',
            'del-emails-0': 'on',
            'emails-0-email': 'foo@bar.com',
        }
        rv = client.post('/admin/user/edit/?id=1', data=data)
        assert rv.status_code == 200
        assert User.query.count() == 1
        assert UserEmail.query.count() == 1


def test_inline_form_ajax_fk():
    app, db, admin = setup()

    with app.app_context():
        # Set up models and database
        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, unique=True)

            def __init__(self, name=None):
                self.name = name

        class Tag(db.Model):
            __tablename__ = 'tags'

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, unique=True)

        class UserInfo(db.Model):
            __tablename__ = 'user_info'
            id = db.Column(db.Integer, primary_key=True)
            key = db.Column(db.String, nullable=False)
            val = db.Column(db.String)

            user_id = db.Column(db.Integer, db.ForeignKey(User.id))
            user = db.relationship(User, backref=db.backref('info', cascade="all, delete-orphan", single_parent=True))

            tag_id = db.Column(db.Integer, db.ForeignKey(Tag.id))
            tag = db.relationship(Tag, backref='user_info')

        db.create_all()

        # Set up Admin
        class UserModelView(ModelView):
            opts = {
                'form_ajax_refs': {
                    'tag': {
                        'fields': ['name']
                    }
                }
            }

            inline_models = [(UserInfo, opts)]

        view = UserModelView(User, db.session)
        admin.add_view(view)

        form = view.create_form()
        user_info_form = form.info.unbound_field.args[0]
        loader = user_info_form.tag.args[0]
        assert loader.name == 'userinfo-tag'
        assert loader.model == Tag

        assert 'userinfo-tag' in view._form_ajax_refs


def test_inline_form_self():
    app, db, admin = setup()

    with app.app_context():
        class Tree(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            parent_id = db.Column(db.Integer, db.ForeignKey('tree.id'))
            parent = db.relationship('Tree', remote_side=[id], backref='children')

        db.create_all()

        class TreeView(ModelView):
            inline_models = (Tree,)

        view = TreeView(Tree, db.session)

        parent = Tree()
        child = Tree(parent=parent)
        form = view.edit_form(child)
        assert form.parent.data == parent


def test_inline_form_base_class():
    app, db, admin = setup()
    client = app.test_client()

    with app.app_context():
        # Set up models and database
        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, unique=True)

            def __init__(self, name=None):
                self.name = name

        class UserEmail(db.Model):
            __tablename__ = 'user_info'
            id = db.Column(db.Integer, primary_key=True)
            email = db.Column(db.String, nullable=False, unique=True)
            verified_at = db.Column(db.DateTime)
            user_id = db.Column(db.Integer, db.ForeignKey(User.id))
            user = db.relationship(User, backref=db.backref('emails', cascade="all, delete-orphan", single_parent=True))

        db.create_all()

        # Customize error message
        class StubTranslation(object):
            def gettext(self, *args):
                return 'success!'

            def ngettext(self, *args):
                return 'success!'

        class StubBaseForm(form.BaseForm):
            def _get_translations(self):
                return StubTranslation()

        # Set up Admin
        class UserModelView(ModelView):
            inline_models = ((UserEmail, {"form_base_class": StubBaseForm}),)
            form_args = {
                "emails": {"validators": [ItemsRequired()]}
            }

        view = UserModelView(User, db.session)
        admin.add_view(view)

        # Create
        data = {
            'name': 'emptyEmail',
            'emails-0-email': '',
        }
        rv = client.post('/admin/user/new/', data=data)
        assert rv.status_code == 200
        assert User.query.count() == 0
        assert b'success!' in rv.data, rv.data
