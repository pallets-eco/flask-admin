from nose.tools import eq_, ok_
from nose.plugins.skip import SkipTest

# Skip test on PY3
from flask_admin._compat import PY2, as_unicode
if not PY2:
    raise SkipTest('Peewee is not Python 3 compatible')

import peewee

from wtforms import fields, validators

from flask_admin import form
from flask_admin._compat import iteritems
from flask_admin.contrib.peewee import ModelView

from . import setup

from datetime import datetime, time, date


class CustomModelView(ModelView):
    def __init__(self, model,
                 name=None, category=None, endpoint=None, url=None,
                 **kwargs):
        for k, v in iteritems(kwargs):
            setattr(self, k, v)

        super(CustomModelView, self).__init__(model,
                                              name, category,
                                              endpoint, url)


def create_models(db):
    class BaseModel(peewee.Model):
        class Meta:
            database = db

    class Model1(BaseModel):
        def __init__(self, test1=None, test2=None, test3=None, test4=None,
                     date_field=None, timeonly_field=None,
                     datetime_field=None, **kwargs):
            super(Model1, self).__init__(**kwargs)

            self.test1 = test1
            self.test2 = test2
            self.test3 = test3
            self.test4 = test4
            self.date_field = date_field
            self.timeonly_field = timeonly_field
            self.datetime_field = datetime_field

        test1 = peewee.CharField(max_length=20, null=True)
        test2 = peewee.CharField(max_length=20, null=True)
        test3 = peewee.TextField(null=True)
        test4 = peewee.TextField(null=True)
        date_field = peewee.DateField(null=True)
        timeonly_field = peewee.TimeField(null=True)
        datetime_field = peewee.DateTimeField(null=True)

        def __str__(self):
            # "or ''" fixes error when loading choices for relation field:
            # TypeError: coercing to Unicode: need string or buffer, NoneType found
            return self.test1 or ''

    class Model2(BaseModel):
        def __init__(self, char_field=None, int_field=None, float_field=None,
                     bool_field=0, **kwargs):
            super(Model2, self).__init__(**kwargs)

            self.char_field = char_field
            self.int_field = int_field
            self.float_field = float_field
            self.bool_field = bool_field

        char_field = peewee.CharField(max_length=20)
        int_field = peewee.IntegerField(null=True)
        float_field = peewee.FloatField(null=True)
        bool_field = peewee.BooleanField()

        # Relation
        model1 = peewee.ForeignKeyField(Model1, null=True)

    Model1.create_table()
    Model2.create_table()

    return Model1, Model2


def fill_db(Model1, Model2):
    Model1('test1_val_1', 'test2_val_1').save()
    Model1('test1_val_2', 'test2_val_2').save()
    Model1('test1_val_3', 'test2_val_3').save()
    Model1('test1_val_4', 'test2_val_4').save()
    Model1(None, 'empty_obj').save()

    Model2('char_field_val_1', None, None, bool_field=True).save()
    Model2('char_field_val_2', None, None, bool_field=False).save()
    Model2('char_field_val_3', 5000, 25.9).save()
    Model2('char_field_val_4', 9000, 75.5).save()
    Model2('char_field_val_5', 6169453081680413441).save()

    Model1('date_obj1', date_field=date(2014, 11, 17)).save()
    Model1('date_obj2', date_field=date(2013, 10, 16)).save()
    Model1('timeonly_obj1', timeonly_field=time(11, 10, 9)).save()
    Model1('timeonly_obj2', timeonly_field=time(10, 9, 8)).save()
    Model1('datetime_obj1', datetime_field=datetime(2014, 4, 3, 1, 9, 0)).save()
    Model1('datetime_obj2', datetime_field=datetime(2013, 3, 2, 0, 8, 0)).save()


def test_model():
    app, db, admin = setup()
    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1)
    admin.add_view(view)

    eq_(view.model, Model1)
    eq_(view.name, 'Model1')
    eq_(view.endpoint, 'model1')

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
    eq_(view._create_form_class.test1.field_class, fields.StringField)
    eq_(view._create_form_class.test2.field_class, fields.StringField)
    eq_(view._create_form_class.test3.field_class, fields.TextAreaField)
    eq_(view._create_form_class.test4.field_class, fields.TextAreaField)

    # Make some test clients
    client = app.test_client()

    rv = client.get('/admin/model1/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/model1/new/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/model1/new/',
                     data=dict(test1='test1large', test2='test2'))
    eq_(rv.status_code, 302)

    model = Model1.select().get()
    eq_(model.test1, 'test1large')
    eq_(model.test2, 'test2')
    ok_(model.test3 is None or model.test3 == '')
    ok_(model.test4 is None or model.test4 == '')

    rv = client.get('/admin/model1/')
    eq_(rv.status_code, 200)
    ok_('test1large' in rv.data)

    url = '/admin/model1/edit/?id=%s' % model.id
    rv = client.get(url)
    eq_(rv.status_code, 200)

    rv = client.post(url,
                     data=dict(test1='test1small', test2='test2large'))
    eq_(rv.status_code, 302)

    model = Model1.select().get()
    eq_(model.test1, 'test1small')
    eq_(model.test2, 'test2large')
    ok_(model.test3 is None or model.test3 == '')
    ok_(model.test4 is None or model.test4 == '')

    url = '/admin/model1/delete/?id=%s' % model.id
    rv = client.post(url)
    eq_(rv.status_code, 302)
    eq_(Model1.select().count(), 0)


def test_column_editable_list():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    # wtf-peewee doesn't automatically add length validators for max_length
    form_args = {'test1': {'validators': [validators.Length(max=20)]}}
    view = CustomModelView(Model1, column_editable_list=['test1'],
                           form_args=form_args)
    admin.add_view(view)

    fill_db(Model1, Model2)

    client = app.test_client()

    # Test in-line edit field rendering
    rv = client.get('/admin/model1/')
    data = rv.data.decode('utf-8')
    ok_('data-role="x-editable"' in data)

    # Form - Test basic in-line edit functionality
    rv = client.post('/admin/model1/ajax/update/', data={
        'list_form_pk': '1',
        'test1': 'change-success-1',
    })
    data = rv.data.decode('utf-8')
    ok_('Record was successfully saved.' == data)

    # ensure the value has changed
    rv = client.get('/admin/model1/')
    data = rv.data.decode('utf-8')
    ok_('change-success-1' in data)

    # Test validation error
    rv = client.post('/admin/model1/ajax/update/', data={
        'list_form_pk': '1',
        'test1': ('longerthantwentycharacterslongerthantwentycharacterslonger'
                  'thantwentycharacterslongerthantwentycharacters'),
    })
    data = rv.data.decode('utf-8')
    eq_(rv.status_code, 500)

    # Test invalid primary key
    rv = client.post('/admin/model1/ajax/update/', data={
        'list_form_pk': '1000',
        'test1': 'problematic-input',
    })
    data = rv.data.decode('utf-8')
    eq_(rv.status_code, 500)

    # Test editing column not in column_editable_list
    rv = client.post('/admin/model1/ajax/update/', data={
        'list_form_pk': '1',
        'test2': 'problematic-input',
    })
    data = rv.data.decode('utf-8')
    ok_('problematic-input' not in data)

    # Test in-line editing for relations
    view = CustomModelView(Model2, column_editable_list=['model1'])
    admin.add_view(view)

    rv = client.post('/admin/model2/ajax/update/', data={
        'list_form_pk': '1',
        'model1': '3',
    })
    data = rv.data.decode('utf-8')
    ok_('Record was successfully saved.' == data)

    # confirm the value has changed
    rv = client.get('/admin/model2/')
    data = rv.data.decode('utf-8')
    ok_('test1_val_3' in data)


def test_details_view():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view_no_details = CustomModelView(Model1)
    admin.add_view(view_no_details)

    # fields are scaffolded
    view_w_details = CustomModelView(Model2, can_view_details=True)
    admin.add_view(view_w_details)

    # show only specific fields in details w/ column_details_list
    char_field_view = CustomModelView(Model2, can_view_details=True,
                                      column_details_list=["char_field"],
                                      endpoint="cf_view")
    admin.add_view(char_field_view)

    fill_db(Model1, Model2)

    client = app.test_client()

    # ensure link to details is hidden when can_view_details is disabled
    rv = client.get('/admin/model1/')
    data = rv.data.decode('utf-8')
    ok_('/admin/model1/details/' not in data)

    # ensure link to details view appears
    rv = client.get('/admin/model2/')
    data = rv.data.decode('utf-8')
    ok_('/admin/model2/details/' in data)

    # test redirection when details are disabled
    rv = client.get('/admin/model1/details/?url=%2Fadmin%2Fmodel1%2F&id=3')
    eq_(rv.status_code, 302)

    # test if correct data appears in details view when enabled
    rv = client.get('/admin/model2/details/?url=%2Fadmin%2Fmodel2%2F&id=3')
    data = rv.data.decode('utf-8')
    ok_('Char Field' in data)
    ok_('char_field_val_3' in data)
    ok_('Int Field' in data)
    ok_('5000' in data)

    # test column_details_list
    rv = client.get('/admin/cf_view/details/?url=%2Fadmin%2Fcf_view%2F&id=3')
    data = rv.data.decode('utf-8')
    ok_('Char Field' in data)
    ok_('char_field_val_3' in data)
    ok_('Int Field' not in data)
    ok_('5000' not in data)


def test_column_filters():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    fill_db(Model1, Model2)

    # Test string filter
    view = CustomModelView(Model1, column_filters=['test1'])
    admin.add_view(view)

    eq_(len(view._filters), 7)

    eq_(
        [(f['index'], f['operation']) for f in view._filter_groups[u'Test1']],
        [
            (0, 'contains'),
            (1, 'not contains'),
            (2, 'equals'),
            (3, 'not equal'),
            (4, 'empty'),
            (5, 'in list'),
            (6, 'not in list'),
        ]
    )

    # Make some test clients
    client = app.test_client()

    # string - equals
    rv = client.get('/admin/model1/?flt0_0=test1_val_1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test2_val_1' in data)
    ok_('test1_val_2' not in data)

    # string - not equal
    rv = client.get('/admin/model1/?flt0_1=test1_val_1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test2_val_1' not in data)
    ok_('test1_val_2' in data)

    # string - contains
    rv = client.get('/admin/model1/?flt0_2=test1_val_1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test2_val_1' in data)
    ok_('test1_val_2' not in data)

    # string - not contains
    rv = client.get('/admin/model1/?flt0_3=test1_val_1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test2_val_1' not in data)
    ok_('test1_val_2' in data)

    # string - empty
    rv = client.get('/admin/model1/?flt0_4=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('empty_obj' in data)
    ok_('test1_val_1' not in data)
    ok_('test1_val_2' not in data)

    # string - not empty
    rv = client.get('/admin/model1/?flt0_4=0')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('empty_obj' not in data)
    ok_('test1_val_1' in data)
    ok_('test1_val_2' in data)

    # string - in list
    rv = client.get('/admin/model1/?flt0_5=test1_val_1%2Ctest1_val_2')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test2_val_1' in data)
    ok_('test2_val_2' in data)
    ok_('test1_val_3' not in data)
    ok_('test1_val_4' not in data)

    # string - not in list
    rv = client.get('/admin/model1/?flt0_6=test1_val_1%2Ctest1_val_2')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test2_val_1' not in data)
    ok_('test2_val_2' not in data)
    ok_('test1_val_3' in data)
    ok_('test1_val_4' in data)

    # Test int filter
    view = CustomModelView(Model2, column_filters=['int_field'])
    admin.add_view(view)

    eq_(
        [(f['index'], f['operation']) for f in view._filter_groups[u'Int Field']],
        [
            (0, 'equals'),
            (1, 'not equal'),
            (2, 'greater than'),
            (3, 'smaller than'),
            (4, 'empty'),
            (5, 'in list'),
            (6, 'not in list'),
        ]
    )

    # integer - equals
    rv = client.get('/admin/model2/?flt0_0=5000')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_3' in data)
    ok_('char_field_val_4' not in data)

    # integer - equals (huge number)
    rv = client.get('/admin/model2/?flt0_0=6169453081680413441')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_5' in data)
    ok_('char_field_val_4' not in data)

    # integer - equals - test validation
    rv = client.get('/admin/model2/?flt0_0=badval')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('Invalid Filter Value' in data)

    # integer - not equal
    rv = client.get('/admin/model2/?flt0_1=5000')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_3' not in data)
    ok_('char_field_val_4' in data)

    # integer - greater
    rv = client.get('/admin/model2/?flt0_2=6000')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_3' not in data)
    ok_('char_field_val_4' in data)

    # integer - smaller
    rv = client.get('/admin/model2/?flt0_3=6000')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_3' in data)
    ok_('char_field_val_4' not in data)

    # integer - empty
    rv = client.get('/admin/model2/?flt0_4=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' in data)
    ok_('char_field_val_2' in data)
    ok_('char_field_val_3' not in data)
    ok_('char_field_val_4' not in data)

    # integer - not empty
    rv = client.get('/admin/model2/?flt0_4=0')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' not in data)
    ok_('char_field_val_2' not in data)
    ok_('char_field_val_3' in data)
    ok_('char_field_val_4' in data)

    # integer - in list
    rv = client.get('/admin/model2/?flt0_5=5000%2C9000')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' not in data)
    ok_('char_field_val_2' not in data)
    ok_('char_field_val_3' in data)
    ok_('char_field_val_4' in data)

    # integer - in list (huge number)
    rv = client.get('/admin/model2/?flt0_5=6169453081680413441')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' not in data)
    ok_('char_field_val_5' in data)

    # integer - in list - test validation
    rv = client.get('/admin/model2/?flt0_5=5000%2Cbadval')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('Invalid Filter Value' in data)

    # integer - not in list
    rv = client.get('/admin/model2/?flt0_6=5000%2C9000')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' in data)
    ok_('char_field_val_2' in data)
    ok_('char_field_val_3' not in data)
    ok_('char_field_val_4' not in data)

    # Test boolean filter
    view = CustomModelView(Model2, column_filters=['bool_field'],
                           endpoint="_bools")
    admin.add_view(view)

    eq_(
        [(f['index'], f['operation']) for f in view._filter_groups[u'Bool Field']],
        [
            (0, 'equals'),
            (1, 'not equal'),
        ]
    )

    # boolean - equals - Yes
    rv = client.get('/admin/_bools/?flt0_0=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' in data)
    ok_('char_field_val_2' not in data)
    ok_('char_field_val_3' not in data)

    # boolean - equals - No
    rv = client.get('/admin/_bools/?flt0_0=0')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' not in data)
    ok_('char_field_val_2' in data)
    ok_('char_field_val_3' in data)

    # boolean - not equals - Yes
    rv = client.get('/admin/_bools/?flt0_1=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' not in data)
    ok_('char_field_val_2' in data)
    ok_('char_field_val_3' in data)

    # boolean - not equals - No
    rv = client.get('/admin/_bools/?flt0_1=0')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' in data)
    ok_('char_field_val_2' not in data)
    ok_('char_field_val_3' not in data)

    # Test float filter
    view = CustomModelView(Model2, column_filters=['float_field'],
                           endpoint="_float")
    admin.add_view(view)

    eq_(
        [(f['index'], f['operation']) for f in view._filter_groups[u'Float Field']],
        [
            (0, 'equals'),
            (1, 'not equal'),
            (2, 'greater than'),
            (3, 'smaller than'),
            (4, 'empty'),
            (5, 'in list'),
            (6, 'not in list'),
        ]
    )

    # float - equals
    rv = client.get('/admin/_float/?flt0_0=25.9')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_3' in data)
    ok_('char_field_val_4' not in data)

    # float - equals - test validation
    rv = client.get('/admin/_float/?flt0_0=badval')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('Invalid Filter Value' in data)

    # float - not equal
    rv = client.get('/admin/_float/?flt0_1=25.9')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_3' not in data)
    ok_('char_field_val_4' in data)

    # float - greater
    rv = client.get('/admin/_float/?flt0_2=60.5')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_3' not in data)
    ok_('char_field_val_4' in data)

    # float - smaller
    rv = client.get('/admin/_float/?flt0_3=60.5')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_3' in data)
    ok_('char_field_val_4' not in data)

    # float - empty
    rv = client.get('/admin/_float/?flt0_4=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' in data)
    ok_('char_field_val_2' in data)
    ok_('char_field_val_3' not in data)
    ok_('char_field_val_4' not in data)

    # float - not empty
    rv = client.get('/admin/_float/?flt0_4=0')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' not in data)
    ok_('char_field_val_2' not in data)
    ok_('char_field_val_3' in data)
    ok_('char_field_val_4' in data)

    # float - in list
    rv = client.get('/admin/_float/?flt0_5=25.9%2C75.5')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' not in data)
    ok_('char_field_val_2' not in data)
    ok_('char_field_val_3' in data)
    ok_('char_field_val_4' in data)

    # float - in list - test validation
    rv = client.get('/admin/_float/?flt0_5=25.9%2Cbadval')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('Invalid Filter Value' in data)

    # float - not in list
    rv = client.get('/admin/_float/?flt0_6=25.9%2C75.5')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('char_field_val_1' in data)
    ok_('char_field_val_2' in data)
    ok_('char_field_val_3' not in data)
    ok_('char_field_val_4' not in data)

    # Test date, time, and datetime filters
    view = CustomModelView(Model1,
                           column_filters=['date_field', 'datetime_field', 'timeonly_field'],
                           endpoint="_datetime")
    admin.add_view(view)

    eq_(
        [(f['index'], f['operation']) for f in view._filter_groups[u'Date Field']],
        [
            (0, 'equals'),
            (1, 'not equal'),
            (2, 'greater than'),
            (3, 'smaller than'),
            (4, 'between'),
            (5, 'not between'),
            (6, 'empty'),
        ]
    )

    eq_(
        [(f['index'], f['operation']) for f in view._filter_groups[u'Datetime Field']],
        [
            (7, 'equals'),
            (8, 'not equal'),
            (9, 'greater than'),
            (10, 'smaller than'),
            (11, 'between'),
            (12, 'not between'),
            (13, 'empty'),
        ]
    )

    eq_(
        [(f['index'], f['operation']) for f in view._filter_groups[u'Timeonly Field']],
        [
            (14, 'equals'),
            (15, 'not equal'),
            (16, 'greater than'),
            (17, 'smaller than'),
            (18, 'between'),
            (19, 'not between'),
            (20, 'empty'),
        ]
    )

    # date - equals
    rv = client.get('/admin/_datetime/?flt0_0=2014-11-17')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('date_obj1' in data)
    ok_('date_obj2' not in data)

    # date - not equal
    rv = client.get('/admin/_datetime/?flt0_1=2014-11-17')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('date_obj1' not in data)
    ok_('date_obj2' in data)

    # date - greater
    rv = client.get('/admin/_datetime/?flt0_2=2014-11-16')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('date_obj1' in data)
    ok_('date_obj2' not in data)

    # date - smaller
    rv = client.get('/admin/_datetime/?flt0_3=2014-11-16')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('date_obj1' not in data)
    ok_('date_obj2' in data)

    # date - between
    rv = client.get('/admin/_datetime/?flt0_4=2014-11-13+to+2014-11-20')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('date_obj1' in data)
    ok_('date_obj2' not in data)

    # date - not between
    rv = client.get('/admin/_datetime/?flt0_5=2014-11-13+to+2014-11-20')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('date_obj1' not in data)
    ok_('date_obj2' in data)

    # date - empty
    rv = client.get('/admin/_datetime/?flt0_6=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test1_val_1' in data)
    ok_('date_obj1' not in data)
    ok_('date_obj2' not in data)

    # date - empty
    rv = client.get('/admin/_datetime/?flt0_6=0')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test1_val_1' not in data)
    ok_('date_obj1' in data)
    ok_('date_obj2' in data)

    # datetime - equals
    rv = client.get('/admin/_datetime/?flt0_7=2014-04-03+01%3A09%3A00')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('datetime_obj1' in data)
    ok_('datetime_obj2' not in data)

    # datetime - not equal
    rv = client.get('/admin/_datetime/?flt0_8=2014-04-03+01%3A09%3A00')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('datetime_obj1' not in data)
    ok_('datetime_obj2' in data)

    # datetime - greater
    rv = client.get('/admin/_datetime/?flt0_9=2014-04-03+01%3A08%3A00')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('datetime_obj1' in data)
    ok_('datetime_obj2' not in data)

    # datetime - smaller
    rv = client.get('/admin/_datetime/?flt0_10=2014-04-03+01%3A08%3A00')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('datetime_obj1' not in data)
    ok_('datetime_obj2' in data)

    # datetime - between
    rv = client.get('/admin/_datetime/?flt0_11=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('datetime_obj1' in data)
    ok_('datetime_obj2' not in data)

    # datetime - not between
    rv = client.get('/admin/_datetime/?flt0_12=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('datetime_obj1' not in data)
    ok_('datetime_obj2' in data)

    # datetime - empty
    rv = client.get('/admin/_datetime/?flt0_13=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test1_val_1' in data)
    ok_('datetime_obj1' not in data)
    ok_('datetime_obj2' not in data)

    # datetime - not empty
    rv = client.get('/admin/_datetime/?flt0_13=0')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test1_val_1' not in data)
    ok_('datetime_obj1' in data)
    ok_('datetime_obj2' in data)

    # time - equals
    rv = client.get('/admin/_datetime/?flt0_14=11%3A10%3A09')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('timeonly_obj1' in data)
    ok_('timeonly_obj2' not in data)

    # time - not equal
    rv = client.get('/admin/_datetime/?flt0_15=11%3A10%3A09')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('timeonly_obj1' not in data)
    ok_('timeonly_obj2' in data)

    # time - greater
    rv = client.get('/admin/_datetime/?flt0_16=11%3A09%3A09')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('timeonly_obj1' in data)
    ok_('timeonly_obj2' not in data)

    # time - smaller
    rv = client.get('/admin/_datetime/?flt0_17=11%3A09%3A09')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('timeonly_obj1' not in data)
    ok_('timeonly_obj2' in data)

    # time - between
    rv = client.get('/admin/_datetime/?flt0_18=10%3A40%3A00+to+11%3A50%3A59')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('timeonly_obj1' in data)
    ok_('timeonly_obj2' not in data)

    # time - not between
    rv = client.get('/admin/_datetime/?flt0_19=10%3A40%3A00+to+11%3A50%3A59')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('timeonly_obj1' not in data)
    ok_('timeonly_obj2' in data)

    # time - empty
    rv = client.get('/admin/_datetime/?flt0_20=1')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test1_val_1' in data)
    ok_('timeonly_obj1' not in data)
    ok_('timeonly_obj2' not in data)

    # time - not empty
    rv = client.get('/admin/_datetime/?flt0_20=0')
    eq_(rv.status_code, 200)
    data = rv.data.decode('utf-8')
    ok_('test1_val_1' not in data)
    ok_('timeonly_obj1' in data)
    ok_('timeonly_obj2' in data)


def test_default_sort():
    app, db, admin = setup()
    M1, _ = create_models(db)

    M1('c', 1).save()
    M1('b', 2).save()
    M1('a', 3).save()

    eq_(M1.select().count(), 3)

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
            'extra_field': fields.StringField('Extra Field')
        }
    )
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/model1/new/')
    eq_(rv.status_code, 200)

    # Check presence and order
    data = rv.data.decode('utf-8')
    ok_('Extra Field' in data)
    pos1 = data.find('Extra Field')
    pos2 = data.find('Test1')
    ok_(pos2 < pos1)


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


def test_form_args():
    app, db, admin = setup()

    class BaseModel(peewee.Model):
        class Meta:
            database = db

    class Model(BaseModel):
        test = peewee.CharField(null=False)

    Model.create_table()

    shared_form_args = {'test': {'validators': [validators.Regexp('test')]}}

    view = CustomModelView(Model, form_args=shared_form_args)
    admin.add_view(view)

    # ensure shared field_args don't create duplicate validators
    create_form = view.create_form()

    eq_(len(create_form.test.validators), 2)

    edit_form = view.edit_form()
    eq_(len(edit_form.test.validators), 2)


def test_ajax_fk():
    app, db, admin = setup()

    class BaseModel(peewee.Model):
        class Meta:
            database = db

    class Model1(BaseModel):
        test1 = peewee.CharField(max_length=20)
        test2 = peewee.CharField(max_length=20)

        def __str__(self):
            return self.test1

    class Model2(BaseModel):
        model1 = peewee.ForeignKeyField(Model1)

    Model1.create_table()
    Model2.create_table()

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

    model = Model1(test1=u'first', test2=u'')
    model.save()
    model2 = Model1(test1=u'foo', test2=u'bar')
    model2.save()

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
        needle = u'data-json="[%s, &quot;first&quot;]"' % as_unicode(model.id)
        ok_(needle in form.model1())
        ok_(u'value="%s"' % as_unicode(model.id) in form.model1())

    # Check querying
    client = app.test_client()

    req = client.get(u'/admin/view/ajax/lookup/?name=model1&query=foo')
    eq_(req.data, u'[[%s, "foo"]]' % model2.id)

    # Check submitting
    client.post('/admin/view/new/', data={u'model1': as_unicode(model.id)})
    mdl = Model2.select().first()

    ok_(mdl is not None)
    ok_(mdl.model1 is not None)
    eq_(mdl.model1.id, model.id)
    eq_(mdl.model1.test1, u'first')


def test_export_csv():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, can_export=True,
                           column_list=['test1', 'test2'], export_max_rows=2,
                           endpoint='row_limit_2')
    admin.add_view(view)

    for x in range(5):
        fill_db(Model1, Model2)

    client = app.test_client()

    # test export_max_rows
    rv = client.get('/admin/row_limit_2/export/csv/')
    data = rv.data.decode('utf-8')
    eq_(rv.status_code, 200)
    ok_("Test1,Test2\r\n"
        "test1_val_1,test2_val_1\r\n"
        "test1_val_2,test2_val_2\r\n" == data)

    view = CustomModelView(Model1, can_export=True,
                           column_list=['test1', 'test2'],
                           endpoint='no_row_limit')
    admin.add_view(view)

    # test row limit without export_max_rows
    rv = client.get('/admin/no_row_limit/export/csv/')
    data = rv.data.decode('utf-8')
    eq_(rv.status_code, 200)
    ok_(len(data.splitlines()) > 21)
