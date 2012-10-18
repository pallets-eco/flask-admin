# -*- coding: utf-8 -*-
from nose.tools import eq_, ok_, raises

from flask.ext import wtf
from flask.ext.admin.contrib.sqlamodel import ModelView, fields

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
    eq_(view.endpoint, 'userview')

    # Verify form
    eq_(view._create_form_class.name.field_class, wtf.TextField)
    eq_(view._create_form_class.info.field_class, fields.InlineModelFormList)

    rv = client.get('/admin/userview/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/userview/new/')
    eq_(rv.status_code, 200)

    # Create
    rv = client.post('/admin/userview/new/', data=dict(name=u'äõüxyz'))
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 1)
    eq_(UserInfo.query.count(), 0)

    rv = client.post('/admin/userview/new/', data={'name': u'fbar', \
                     'info-0-key': 'foo', 'info-0-val' : 'bar'})
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 2)
    eq_(UserInfo.query.count(), 1)

    # Edit
    rv = client.get('/admin/userview/edit/?id=2')
    eq_(rv.status_code, 200)
    # Edit - update
    rv = client.post('/admin/userview/edit/?id=2', data={'name': u'barfoo', \
                     'info-0-id': 1, 'info-0-key': u'xxx', 'info-0-val':u'yyy'})
    eq_(UserInfo.query.count(), 1)
    eq_(UserInfo.query.one().key, u'xxx')

    # Edit - add & delete
    rv = client.post('/admin/userview/edit/?id=2', data={'name': u'barf', \
                     'del-info-0': 'on', 'info-0-id': '1', 'info-0-key': 'yyy', 'info-0-val': 'xxx',
                     'info-1-id': None, 'info-1-key': u'bar', 'info-1-val' : u'foo'})
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 2)
    eq_(User.query.get(2).name, u'barf')
    eq_(UserInfo.query.count(), 1)
    eq_(UserInfo.query.one().key, u'bar')

    # Delete
    rv = client.post('/admin/userview/delete/?id=2')
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 1)
    rv = client.post('/admin/userview/delete/?id=1')
    eq_(rv.status_code, 302)
    eq_(User.query.count(), 0)
    eq_(UserInfo.query.count(), 0)
