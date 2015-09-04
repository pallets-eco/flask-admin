# -*- coding: utf-8 -*-
from nose.tools import eq_, ok_, raises

from wtforms import fields

from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import InlineModelFormList
from flask_admin.contrib.sqla.validators import ItemsRequired

from . import setup


def test_inline_form():
    app, db, admin = setup()
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
    ok_(view._create_form_class is not None)
    ok_(view._edit_form_class is not None)
    eq_(view.endpoint, 'user')

    # Verify form
    eq_(view._create_form_class.name.field_class, fields.StringField)
    eq_(view._create_form_class.info.field_class, InlineModelFormList)

    rv = client.get('/admin/user/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/user/new/')
    eq_(rv.status_code, 200)

    # Create
    rv = client.post('/admin/user/new/', data=dict(name=u'äõüxyz'))
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 1)
    eq_(UserInfo.query.count(), 0)

    rv = client.post('/admin/user/new/', data={'name': u'fbar', \
                     'info-0-key': 'foo', 'info-0-val' : 'bar'})
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 2)
    eq_(UserInfo.query.count(), 1)

    # Edit
    rv = client.get('/admin/user/edit/?id=2')
    eq_(rv.status_code, 200)
    # Edit - update
    rv = client.post('/admin/user/edit/?id=2', data={'name': u'barfoo', \
                     'info-0-id': 1, 'info-0-key': u'xxx', 'info-0-val':u'yyy'})
    eq_(UserInfo.query.count(), 1)
    eq_(UserInfo.query.one().key, u'xxx')

    # Edit - add & delete
    rv = client.post('/admin/user/edit/?id=2', data={'name': u'barf', \
                     'del-info-0': 'on', 'info-0-id': '1', 'info-0-key': 'yyy', 'info-0-val': 'xxx',
                     'info-1-id': None, 'info-1-key': u'bar', 'info-1-val' : u'foo'})
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 2)
    eq_(User.query.get(2).name, u'barf')
    eq_(UserInfo.query.count(), 1)
    eq_(UserInfo.query.one().key, u'bar')

    # Delete
    rv = client.post('/admin/user/delete/?id=2')
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 1)
    rv = client.post('/admin/user/delete/?id=1')
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 0)
    eq_(UserInfo.query.count(), 0)


def test_inline_form_required():
    app, db, admin = setup()
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
    eq_(rv.status_code, 200)
    eq_(User.query.count(), 0)

    data = {
        'name': 'hasEmail',
        'emails-0-email': 'foo@bar.com',
    }
    rv = client.post('/admin/user/new/', data=data)
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 1)
    eq_(UserEmail.query.count(), 1)


def test_inline_form_ajax_fk():
    app, db, admin = setup()

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
    eq_(loader.name, 'userinfo-tag')
    eq_(loader.model, Tag)

    ok_('userinfo-tag' in view._form_ajax_refs)


def test_inline_form_self():
    app, db, admin = setup()

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
    eq_(form.parent.data, parent)
