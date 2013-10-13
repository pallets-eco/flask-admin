from nose.tools import eq_, ok_
from nose.plugins.skip import SkipTest

# Skip test on PY3
from flask.ext.admin._compat import PY2, as_unicode
if not PY2:
    raise SkipTest('MongoEngine is not Python 3 compatible')

from wtforms import fields

from flask.ext.admin import form
from flask.ext.admin.contrib.mongoengine import ModelView

from . import setup


class CustomModelView(ModelView):
    def __init__(self, model,
                 name=None, category=None, endpoint=None, url=None,
                 **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        super(CustomModelView, self).__init__(model,
                                              name, category,
                                              endpoint, url)


def create_models(db):
    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        test2 = db.StringField(max_length=20)
        test3 = db.StringField()
        test4 = db.StringField()

    class Model2(db.Document):
        int_field = db.IntField()
        bool_field = db.BooleanField()

    Model1.objects.delete()
    Model2.objects.delete()

    return Model1, Model2


def test_model():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1)
    admin.add_view(view)

    eq_(view.model, Model1)
    eq_(view.name, 'Model1')
    eq_(view.endpoint, 'model1view')

    eq_(view._primary_key, 'id')

    ok_('test1' in view._sortable_columns)
    ok_('test2' in view._sortable_columns)
    ok_('test3' in view._sortable_columns)
    ok_('test4' in view._sortable_columns)

    ok_(view._create_form_class is not None)
    ok_(view._edit_form_class is not None)
    eq_(view._search_supported, False)
    eq_(view._filters, None)

    # Verify form
    # TODO: Figure out why there's inconsistency
    try:
        eq_(view._create_form_class.test1.field_class, fields.TextField)
        eq_(view._create_form_class.test2.field_class, fields.TextField)
    except AssertionError:
        eq_(view._create_form_class.test1.field_class, fields.StringField)
        eq_(view._create_form_class.test2.field_class, fields.StringField)

    eq_(view._create_form_class.test3.field_class, fields.TextAreaField)
    eq_(view._create_form_class.test4.field_class, fields.TextAreaField)

    # Make some test clients
    client = app.test_client()

    rv = client.get('/admin/model1view/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/model1view/new/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/model1view/new/',
                     data=dict(test1='test1large', test2='test2'))
    eq_(rv.status_code, 302)

    model = Model1.objects.first()
    eq_(model.test1, 'test1large')
    eq_(model.test2, 'test2')
    eq_(model.test3, '')
    eq_(model.test4, '')

    rv = client.get('/admin/model1view/')
    eq_(rv.status_code, 200)
    ok_('test1large' in rv.data)

    url = '/admin/model1view/edit/?id=%s' % model.id
    rv = client.get(url)
    eq_(rv.status_code, 200)

    rv = client.post(url,
                     data=dict(test1='test1small', test2='test2large'))
    eq_(rv.status_code, 302)

    model = Model1.objects.first()
    eq_(model.test1, 'test1small')
    eq_(model.test2, 'test2large')
    eq_(model.test3, '')
    eq_(model.test4, '')

    url = '/admin/model1view/delete/?id=%s' % model.id
    rv = client.post(url)
    eq_(rv.status_code, 302)
    eq_(Model1.objects.count(), 0)


def test_default_sort():
    app, db, admin = setup()
    M1, _ = create_models(db)

    M1(test1='c').save()
    M1(test1='b').save()
    M1(test1='a').save()

    eq_(M1.objects.count(), 3)

    view = CustomModelView(M1, column_default_sort='test1')
    admin.add_view(view)

    _, data = view.get_list(0, None, None, None, None)

    eq_(data[0].test1, 'a')
    eq_(data[1].test1, 'b')
    eq_(data[2].test1, 'c')


def test_extra_fields():
    app, db, admin = setup()

    Model1, _ = create_models(db)

    view = CustomModelView(
        Model1,
        form_extra_fields={
            'extra_field': fields.TextField('Extra Field')
        }
    )
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1view/new/')
    eq_(rv.status_code, 200)

    # Check presence and order
    data = rv.data.decode('utf-8')
    ok_('Extra Field' in data)
    pos1 = data.find('Extra Field')
    pos2 = data.find('Test1')
    ok_(pos2 < pos1)


def test_extra_field_order():
    app, db, admin = setup()

    Model1, _ = create_models(db)

    view = CustomModelView(
        Model1,
        form_columns=('extra_field', 'test1'),
        form_extra_fields={
            'extra_field': fields.TextField('Extra Field')
        }
    )
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1view/new/')
    eq_(rv.status_code, 200)

    # Check presence and order
    data = rv.data.decode('utf-8')
    pos1 = data.find('Extra Field')
    pos2 = data.find('Test1')
    ok_(pos2 > pos1)


def test_custom_form_base():
    app, db, admin = setup()

    class TestForm(form.BaseForm):
        pass

    Model1, _ = create_models(db)

    view = CustomModelView(
        Model1,
        form_base_class=TestForm
    )
    admin.add_view(view)

    ok_(hasattr(view._create_form_class, 'test1'))

    create_form = view.create_form()
    ok_(isinstance(create_form, TestForm))


def test_subdocument_config():
    app, db, admin = setup()

    class Comment(db.EmbeddedDocument):
        name = db.StringField(max_length=20, required=True)
        value = db.StringField(max_length=20)

    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        subdoc = db.EmbeddedDocumentField(Comment)

    # Check only
    view1 = CustomModelView(
        Model1,
        form_subdocuments = {
            'subdoc': {
                'form_columns': ('name',)
            }
        }
    )

    ok_(hasattr(view1._create_form_class, 'subdoc'))

    form = view1.create_form()
    ok_('name' in dir(form.subdoc.form))
    ok_('value' not in dir(form.subdoc.form))

    # Check exclude
    view2 = CustomModelView(
        Model1,
        form_subdocuments = {
            'subdoc': {
                'form_excluded_columns': ('value',)
            }
        }
    )

    form = view2.create_form()
    ok_('name' in dir(form.subdoc.form))
    ok_('value' not in dir(form.subdoc.form))


def test_subdocument_class_config():
    app, db, admin = setup()

    from flask.ext.admin.contrib.mongoengine import EmbeddedForm

    class Comment(db.EmbeddedDocument):
        name = db.StringField(max_length=20, required=True)
        value = db.StringField(max_length=20)

    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        subdoc = db.EmbeddedDocumentField(Comment)

    class EmbeddedConfig(EmbeddedForm):
        form_columns = ('name',)

    # Check only
    view1 = CustomModelView(
        Model1,
        form_subdocuments = {
            'subdoc': EmbeddedConfig()
        }
    )

    form = view1.create_form()
    ok_('name' in dir(form.subdoc.form))
    ok_('value' not in dir(form.subdoc.form))


def test_nested_subdocument_config():
    app, db, admin = setup()

    # Check recursive
    class Comment(db.EmbeddedDocument):
        name = db.StringField(max_length=20, required=True)
        value = db.StringField(max_length=20)

    class Nested(db.EmbeddedDocument):
        name = db.StringField(max_length=20, required=True)
        comment = db.EmbeddedDocumentField(Comment)

    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        nested = db.EmbeddedDocumentField(Nested)

    view1 = CustomModelView(
        Model1,
        form_subdocuments = {
            'nested': {
                'form_subdocuments': {
                    'comment': {
                        'form_columns': ('name',)
                    }
                }
            }
        }
    )

    form = view1.create_form()
    ok_('name' in dir(form.nested.form.comment.form))
    ok_('value' not in dir(form.nested.form.comment.form))


def test_nested_list_subdocument():
    app, db, admin = setup()

    class Comment(db.EmbeddedDocument):
        name = db.StringField(max_length=20, required=True)
        value = db.StringField(max_length=20)

    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        subdoc = db.ListField(db.EmbeddedDocumentField(Comment))

    # Check only
    view1 = CustomModelView(
        Model1,
        form_subdocuments = {
            'subdoc': {
                'form_subdocuments': {
                    None: {
                        'form_columns': ('name',)
                    }
                }

            }
        }
    )

    form = view1.create_form()
    inline_form = form.subdoc.unbound_field.args[2]

    ok_('name' in dir(inline_form))
    ok_('value' not in dir(inline_form))


def test_ajax_fk():
    app, db, admin = setup()

    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        test2 = db.StringField(max_length=20)

        def __str__(self):
            return self.test1

    class Model2(db.Document):
        int_field = db.IntField()
        bool_field = db.BooleanField()

        model1 = db.ReferenceField(Model1)

    Model1.objects.delete()
    Model2.objects.delete()

    view = CustomModelView(
        Model2,
        url='view',
        form_ajax_refs={
            'model1': {
                'fields': ('test1', 'test2')
            }
        }
    )
    admin.add_view(view)

    ok_(u'model1' in view._form_ajax_refs)

    model = Model1(test1=u'first')
    model.save()
    model2 = Model1(test1=u'foo', test2=u'bar').save()

    # Check loader
    loader = view._form_ajax_refs[u'model1']
    mdl = loader.get_one(model.id)
    eq_(mdl.test1, model.test1)

    items = loader.get_list(u'fir')
    eq_(len(items), 1)
    eq_(items[0].id, model.id)

    items = loader.get_list(u'bar')
    eq_(len(items), 1)
    eq_(items[0].test1, u'foo')

    # Check form generation
    form = view.create_form()
    eq_(form.model1.__class__.__name__, u'AjaxSelectField')

    with app.test_request_context('/admin/view/'):
        ok_(u'value=""' not in form.model1())

        form.model1.data = model
        needle = u'data-json="[&quot;%s&quot;, &quot;first&quot;]"' % as_unicode(model.id)
        ok_(needle in form.model1())
        ok_(u'value="%s"' % as_unicode(model.id) in form.model1())

    # Check querying
    client = app.test_client()

    req = client.get(u'/admin/view/ajax/lookup/?name=model1&query=foo')
    eq_(req.data, u'[["%s", "foo"]]' % model2.id)

    # Check submitting
    client.post('/admin/view/new/', data={u'model1': as_unicode(model.id)})
    mdl = Model2.objects.first()

    ok_(mdl is not None)
    ok_(mdl.model1 is not None)
    eq_(mdl.model1.id, model.id)
    eq_(mdl.model1.test1, u'first')


def test_nested_ajax_refs():
    app, db, admin = setup()

    # Check recursive
    class Comment(db.Document):
        name = db.StringField(max_length=20, required=True)
        value = db.StringField(max_length=20)

    class Nested(db.EmbeddedDocument):
        name = db.StringField(max_length=20, required=True)
        comment = db.ReferenceField(Comment)

    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        nested = db.EmbeddedDocumentField(Nested)

    view1 = CustomModelView(
        Model1,
        form_subdocuments = {
            'nested': {
                'form_ajax_refs': {
                    'comment': {
                        'fields': ['name']
                    }
                }
            }
        }
    )

    form = view1.create_form()
    eq_(type(form.nested.form.comment).__name__, 'AjaxSelectField')
    ok_('nested-comment' in view1._form_ajax_refs)


def test_form_flat_choices():
    app, db, admin = setup()

    class Model(db.Document):
        name = db.StringField(max_length=20, choices=('a', 'b', 'c'))

    view = CustomModelView(Model)
    admin.add_view(view)

    form = view.create_form()
    eq_(form.name.choices, [('a', 'a'), ('b', 'b'), ('c', 'c')])


def test_form_args_embeddeddoc():
    app, db, admin = setup()

    class Info(db.EmbeddedDocument):
        name = db.StringField()
        age = db.StringField()

    class Model(db.Document):
        info = db.EmbeddedDocumentField('Info')
        timestamp = db.DateTimeField()

    view = CustomModelView(
        Model,
        form_args= {
            'info': {'label': 'Information'},
            'timestamp': {'label': 'Last Updated Time'}
        }
    )
    admin.add_view(view)
    form = view.create_form()
    eq_(form.timestamp.label.text, 'Last Updated Time')
    # This is the failure
    eq_(form.info.label.text, 'Information')
