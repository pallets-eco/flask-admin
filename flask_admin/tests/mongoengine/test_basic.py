import pytest
from wtforms import fields, validators

from flask_admin import form
from flask_admin._compat import as_unicode
from flask_admin.contrib.mongoengine import ModelView

from . import setup

from datetime import datetime


class CustomModelView(ModelView):
    def __init__(self, model,
                 name=None, category=None, endpoint=None, url=None,
                 **kwargs):
        for k, v in kwargs.items():
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
        date_field = db.DateField()
        datetime_field = db.DateTimeField()

        def __str__(self):
            return self.test1

    class Model2(db.Document):
        string_field = db.StringField()
        int_field = db.IntField()
        float_field = db.FloatField()
        bool_field = db.BooleanField()

        model1 = db.ReferenceField(Model1)

    Model1.objects.delete()
    Model2.objects.delete()

    return Model1, Model2


def fill_db(Model1, Model2):
    Model1(test1='test1_val_1', test2='test2_val_1').save()
    Model1(test1='test1_val_2', test2='test2_val_2').save()
    Model1(test1='test1_val_3', test2='test2_val_3').save()
    Model1(test1='test1_val_4', test2='test2_val_4').save()
    Model1(test1=None, test2='empty_obj').save()

    Model2(string_field='string_field_val_1', int_field=None,
           float_field=None, bool_field=True).save()
    Model2(string_field='string_field_val_2', int_field=None,
           float_field=None, bool_field=False).save()
    Model2(string_field='string_field_val_3', int_field=5000,
           float_field=25.9).save()
    Model2(string_field='string_field_val_4', int_field=9000,
           float_field=75.5).save()
    Model2(string_field='string_field_val_5',
           int_field=6169453081680413441).save()

    Model1(test1='datetime_obj1',
           datetime_field=datetime(2014, 4, 3, 1, 9, 0)).save()
    Model1(test1='datetime_obj2',
           datetime_field=datetime(2013, 3, 2, 0, 8, 0)).save()


def test_model():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1)
    admin.add_view(view)

    assert view.model == Model1
    assert view.name == 'Model1'
    assert view.endpoint == 'model1'

    assert view._primary_key == 'id'

    assert 'test1' in view._sortable_columns
    assert 'test2' in view._sortable_columns
    assert 'test3' in view._sortable_columns
    assert 'test4' in view._sortable_columns
    assert 'date_field' in view._sortable_columns

    assert view._create_form_class is not None
    assert view._edit_form_class is not None
    assert not view._search_supported
    assert view._filters is None

    assert view._create_form_class.test1.field_class == fields.StringField
    assert view._create_form_class.test2.field_class == fields.StringField

    assert view._create_form_class.test3.field_class == fields.TextAreaField
    assert view._create_form_class.test4.field_class == fields.TextAreaField

    # Make some test clients
    client = app.test_client()

    rv = client.get('/admin/model1/')
    assert rv.status_code == 200

    rv = client.get('/admin/model1/new/')
    assert rv.status_code == 200

    rv = client.post('/admin/model1/new/',
                     data=dict(test1='test1large', test2='test2'))
    assert rv.status_code == 302

    model = Model1.objects.first()
    assert model.test1 == 'test1large'
    assert model.test2 == 'test2'
    assert model.test3 == ''
    assert model.test4 == ''

    rv = client.get('/admin/model1/')
    assert rv.status_code == 200
    assert b'test1large' in rv.data

    url = '/admin/model1/edit/?id=%s' % model.id
    rv = client.get(url)
    assert rv.status_code == 200

    rv = client.post(url,
                     data=dict(test1='test1small', test2='test2large'))
    assert rv.status_code == 302

    model = Model1.objects.first()
    assert model.test1 == 'test1small'
    assert model.test2 == 'test2large'
    assert model.test3 == ''
    assert model.test4 == ''

    url = '/admin/model1/delete/?id=%s' % model.id
    rv = client.post(url)
    assert rv.status_code == 302
    assert Model1.objects.count() == 0


def test_column_editable_list():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1,
                           column_editable_list=['test1', 'datetime_field'])
    admin.add_view(view)

    fill_db(Model1, Model2)

    client = app.test_client()

    # Test in-line edit field rendering
    rv = client.get('/admin/model1/')
    data = rv.data.decode('utf-8')
    assert 'data-role="x-editable"' in data

    # Form - Test basic in-line edit functionality
    obj1 = Model1.objects.get(test1='test1_val_3')
    rv = client.post('/admin/model1/ajax/update/', data={
        'list_form_pk': str(obj1.id),
        'test1': 'change-success-1',
    })
    data = rv.data.decode('utf-8')
    assert 'Record was successfully saved.' == data

    # confirm the value has changed
    rv = client.get('/admin/model1/')
    data = rv.data.decode('utf-8')
    assert 'change-success-1' in data

    # Test validation error
    obj2 = Model1.objects.get(test1='datetime_obj1')
    rv = client.post('/admin/model1/ajax/update/', data={
        'list_form_pk': str(obj2.id),
        'datetime_field': 'problematic-input',
    })
    assert rv.status_code == 500

    # Test invalid primary key
    rv = client.post('/admin/model1/ajax/update/', data={
        'list_form_pk': '1000',
        'test1': 'problematic-input',
    })
    data = rv.data.decode('utf-8')
    assert rv.status_code == 500

    # Test editing column not in column_editable_list
    rv = client.post('/admin/model1/ajax/update/', data={
        'list_form_pk': '1',
        'test2': 'problematic-input',
    })
    data = rv.data.decode('utf-8')
    assert 'problematic-input' not in data

    # Test in-line editing for relations
    view = CustomModelView(Model2, column_editable_list=['model1'])
    admin.add_view(view)

    obj3 = Model2.objects.get(string_field='string_field_val_1')
    rv = client.post('/admin/model2/ajax/update/', data={
        'list_form_pk': str(obj3.id),
        'model1': str(obj1.id),
    })
    data = rv.data.decode('utf-8')
    assert 'Record was successfully saved.' == data

    # confirm the value has changed
    rv = client.get('/admin/model2/')
    data = rv.data.decode('utf-8')
    assert 'test1_val_1' in data


def test_details_view():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view_no_details = CustomModelView(Model1)
    admin.add_view(view_no_details)

    # fields are scaffolded
    view_w_details = CustomModelView(Model2, can_view_details=True)
    admin.add_view(view_w_details)

    # show only specific fields in details w/ column_details_list
    string_field_view = CustomModelView(Model2, can_view_details=True,
                                        column_details_list=["string_field"],
                                        endpoint="sf_view")
    admin.add_view(string_field_view)

    fill_db(Model1, Model2)

    client = app.test_client()

    m1_id = Model1.objects.first().id
    m2_id = Model2.objects.first().id

    # ensure link to details is hidden when can_view_details is disabled
    rv = client.get('/admin/model1/')
    data = rv.data.decode('utf-8')
    assert '/admin/model1/details/' not in data

    # ensure link to details view appears
    rv = client.get('/admin/model2/')
    data = rv.data.decode('utf-8')
    assert '/admin/model2/details/' in data

    # test redirection when details are disabled
    url = '/admin/model1/details/?url=%2Fadmin%2Fmodel1%2F&id=' + str(m1_id)
    rv = client.get(url)
    assert rv.status_code == 302

    # test if correct data appears in details view when enabled
    url = '/admin/model2/details/?url=%2Fadmin%2Fmodel2%2F&id=' + str(m2_id)
    rv = client.get(url)
    data = rv.data.decode('utf-8')
    assert 'String Field' in data
    assert 'string_field_val_1' in data
    assert 'Int Field' in data

    # test column_details_list
    url = '/admin/sf_view/details/?url=%2Fadmin%2Fsf_view%2F&id=' + str(m2_id)
    rv = client.get(url)
    data = rv.data.decode('utf-8')
    assert 'String Field' in data
    assert 'string_field_val_1' in data
    assert 'Int Field' not in data


def test_column_filters():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    # fill DB with values
    fill_db(Model1, Model2)

    # Test string filter
    view = CustomModelView(Model1, column_filters=['test1'])
    admin.add_view(view)

    assert len(view._filters) == 7

    assert \
        [(f['index'], f['operation']) for f in view._filter_groups[u'Test1']] == \
        [
            (0, 'contains'),
            (1, 'not contains'),
            (2, 'equals'),
            (3, 'not equal'),
            (4, 'empty'),
            (5, 'in list'),
            (6, 'not in list'),
        ]

    # Make some test clients
    client = app.test_client()

    # string - equals
    rv = client.get('/admin/model1/?flt0_0=test1_val_1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'test2_val_1' in data
    assert 'test1_val_2' not in data

    # string - not equal
    rv = client.get('/admin/model1/?flt0_1=test1_val_1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'test2_val_1' not in data
    assert 'test1_val_2' in data

    # string - contains
    rv = client.get('/admin/model1/?flt0_2=test1_val_1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'test2_val_1' in data
    assert 'test1_val_2' not in data

    # string - not contains
    rv = client.get('/admin/model1/?flt0_3=test1_val_1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'test2_val_1' not in data
    assert 'test1_val_2' in data

    # string - empty
    rv = client.get('/admin/model1/?flt0_4=1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'empty_obj' in data
    assert 'test1_val_1' not in data
    assert 'test1_val_2' not in data

    # string - not empty
    rv = client.get('/admin/model1/?flt0_4=0')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'empty_obj' not in data
    assert 'test1_val_1' in data
    assert 'test1_val_2' in data

    # string - in list
    rv = client.get('/admin/model1/?flt0_5=test1_val_1%2Ctest1_val_2')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'test2_val_1' in data
    assert 'test2_val_2' in data
    assert 'test1_val_3' not in data
    assert 'test1_val_4' not in data

    # string - not in list
    rv = client.get('/admin/model1/?flt0_6=test1_val_1%2Ctest1_val_2')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'test2_val_1' not in data
    assert 'test2_val_2' not in data
    assert 'test1_val_3' in data
    assert 'test1_val_4' in data

    # Test numeric filter
    view = CustomModelView(Model2, column_filters=['int_field'])
    admin.add_view(view)

    assert \
        [(f['index'], f['operation']) for f in view._filter_groups[u'Int Field']] == \
        [
            (0, 'equals'),
            (1, 'not equal'),
            (2, 'greater than'),
            (3, 'smaller than'),
            (4, 'empty'),
            (5, 'in list'),
            (6, 'not in list'),
        ]

    # integer - equals
    rv = client.get('/admin/model2/?flt0_0=5000')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_3' in data
    assert 'string_field_val_4' not in data

    # integer - equals (huge number)
    rv = client.get('/admin/model2/?flt0_0=6169453081680413441')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_5' in data
    assert 'string_field_val_4' not in data

    # integer - equals - test validation
    rv = client.get('/admin/model2/?flt0_0=badval')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'Invalid Filter Value' in data

    # integer - not equal
    rv = client.get('/admin/model2/?flt0_1=5000')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_3' not in data
    assert 'string_field_val_4' in data

    # integer - greater
    rv = client.get('/admin/model2/?flt0_2=6000')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_3' not in data
    assert 'string_field_val_4' in data

    # integer - smaller
    rv = client.get('/admin/model2/?flt0_3=6000')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_3' in data
    assert 'string_field_val_4' not in data

    # integer - empty
    rv = client.get('/admin/model2/?flt0_4=1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' in data
    assert 'string_field_val_2' in data
    assert 'string_field_val_3' not in data
    assert 'string_field_val_4' not in data

    # integer - not empty
    rv = client.get('/admin/model2/?flt0_4=0')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' not in data
    assert 'string_field_val_2' not in data
    assert 'string_field_val_3' in data
    assert 'string_field_val_4' in data

    # integer - in list
    rv = client.get('/admin/model2/?flt0_5=5000%2C9000')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' not in data
    assert 'string_field_val_2' not in data
    assert 'string_field_val_3' in data
    assert 'string_field_val_4' in data

    # integer - in list (huge number)
    rv = client.get('/admin/model2/?flt0_5=6169453081680413441')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' not in data
    assert 'string_field_val_5' in data

    # integer - in list - test validation
    rv = client.get('/admin/model2/?flt0_5=5000%2Cbadval')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'Invalid Filter Value' in data

    # integer - not in list
    rv = client.get('/admin/model2/?flt0_6=5000%2C9000')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' in data
    assert 'string_field_val_2' in data
    assert 'string_field_val_3' not in data
    assert 'string_field_val_4' not in data

    # Test boolean filter
    view = CustomModelView(Model2, column_filters=['bool_field'],
                           endpoint="_bools")
    admin.add_view(view)

    assert \
        [(f['index'], f['operation']) for f in view._filter_groups[u'Bool Field']] == \
        [
            (0, 'equals'),
            (1, 'not equal'),
        ]

    # boolean - equals - Yes
    rv = client.get('/admin/_bools/?flt0_0=1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' in data
    assert 'string_field_val_2' not in data

    # boolean - equals - No
    rv = client.get('/admin/_bools/?flt0_0=0')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' not in data
    assert 'string_field_val_2' in data

    # boolean - not equals - Yes
    rv = client.get('/admin/_bools/?flt0_1=1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' not in data
    assert 'string_field_val_2' in data

    # boolean - not equals - No
    rv = client.get('/admin/_bools/?flt0_1=0')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' in data
    assert 'string_field_val_2' not in data

    # Test float filter
    view = CustomModelView(Model2, column_filters=['float_field'],
                           endpoint="_float")
    admin.add_view(view)

    assert \
        [(f['index'], f['operation']) for f in view._filter_groups[u'Float Field']] == \
        [
            (0, 'equals'),
            (1, 'not equal'),
            (2, 'greater than'),
            (3, 'smaller than'),
            (4, 'empty'),
            (5, 'in list'),
            (6, 'not in list'),
        ]

    # float - equals
    rv = client.get('/admin/_float/?flt0_0=25.9')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_3' in data
    assert 'string_field_val_4' not in data

    # float - equals - test validation
    rv = client.get('/admin/_float/?flt0_0=badval')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'Invalid Filter Value' in data

    # float - not equal
    rv = client.get('/admin/_float/?flt0_1=25.9')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_3' not in data
    assert 'string_field_val_4' in data

    # float - greater
    rv = client.get('/admin/_float/?flt0_2=60.5')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_3' not in data
    assert 'string_field_val_4' in data

    # float - smaller
    rv = client.get('/admin/_float/?flt0_3=60.5')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_3' in data
    assert 'string_field_val_4' not in data

    # float - empty
    rv = client.get('/admin/_float/?flt0_4=1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' in data
    assert 'string_field_val_2' in data
    assert 'string_field_val_3' not in data
    assert 'string_field_val_4' not in data

    # float - not empty
    rv = client.get('/admin/_float/?flt0_4=0')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' not in data
    assert 'string_field_val_2' not in data
    assert 'string_field_val_3' in data
    assert 'string_field_val_4' in data

    # float - in list
    rv = client.get('/admin/_float/?flt0_5=25.9%2C75.5')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' not in data
    assert 'string_field_val_2' not in data
    assert 'string_field_val_3' in data
    assert 'string_field_val_4' in data

    # float - in list - test validation
    rv = client.get('/admin/_float/?flt0_5=25.9%2Cbadval')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'Invalid Filter Value' in data

    # float - not in list
    rv = client.get('/admin/_float/?flt0_6=25.9%2C75.5')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'string_field_val_1' in data
    assert 'string_field_val_2' in data
    assert 'string_field_val_3' not in data
    assert 'string_field_val_4' not in data

    # Test datetime filter
    view = CustomModelView(Model1,
                           column_filters=['datetime_field'],
                           endpoint="_datetime")
    admin.add_view(view)

    assert \
        [(f['index'], f['operation']) for f in view._filter_groups[u'Datetime Field']] == \
        [
            (0, 'equals'),
            (1, 'not equal'),
            (2, 'greater than'),
            (3, 'smaller than'),
            (4, 'between'),
            (5, 'not between'),
            (6, 'empty'),
        ]

    # datetime - equals
    rv = client.get('/admin/_datetime/?flt0_0=2014-04-03+01%3A09%3A00')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'datetime_obj1' in data
    assert 'datetime_obj2' not in data

    # datetime - not equal
    rv = client.get('/admin/_datetime/?flt0_1=2014-04-03+01%3A09%3A00')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'datetime_obj1' not in data
    assert 'datetime_obj2' in data

    # datetime - greater
    rv = client.get('/admin/_datetime/?flt0_2=2014-04-03+01%3A08%3A00')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'datetime_obj1' in data
    assert 'datetime_obj2' not in data

    # datetime - smaller
    rv = client.get('/admin/_datetime/?flt0_3=2014-04-03+01%3A08%3A00')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'datetime_obj1' not in data
    assert 'datetime_obj2' in data

    # datetime - between
    rv = client.get('/admin/_datetime/?flt0_4=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'datetime_obj1' in data
    assert 'datetime_obj2' not in data

    # datetime - not between
    rv = client.get('/admin/_datetime/?flt0_5=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'datetime_obj1' not in data
    assert 'datetime_obj2' in data

    # datetime - empty
    rv = client.get('/admin/_datetime/?flt0_6=1')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'test1_val_1' in data
    assert 'datetime_obj1' not in data
    assert 'datetime_obj2' not in data

    # datetime - not empty
    rv = client.get('/admin/_datetime/?flt0_6=0')
    assert rv.status_code == 200
    data = rv.data.decode('utf-8')
    assert 'test1_val_1' not in data
    assert 'datetime_obj1' in data
    assert 'datetime_obj2' in data


def test_default_sort():
    app, db, admin = setup()
    M1, _ = create_models(db)

    M1(test1='c', test2='x').save()
    M1(test1='b', test2='x').save()
    M1(test1='a', test2='y').save()

    assert M1.objects.count() == 3

    view = CustomModelView(M1, column_default_sort='test1')
    admin.add_view(view)

    _, data = view.get_list(0, None, None, None, None)

    assert data[0].test1 == 'a'
    assert data[1].test1 == 'b'
    assert data[2].test1 == 'c'

    # test default sort with multiple columns
    order = [('test2', False), ('test1', False)]
    view2 = CustomModelView(M1, column_default_sort=order, endpoint='m1_2')
    admin.add_view(view2)

    _, data = view2.get_list(0, None, None, None, None)

    assert len(data) == 3
    assert data[0].test1 == 'b'
    assert data[1].test1 == 'c'
    assert data[2].test1 == 'a'


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
    assert rv.status_code == 200

    # Check presence and order
    data = rv.data.decode('utf-8')
    assert 'Extra Field' in data
    pos1 = data.find('Extra Field')
    pos2 = data.find('Test1')
    assert pos2 < pos1


def test_extra_field_order():
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
    assert rv.status_code == 200

    # Check presence and order
    data = rv.data.decode('utf-8')
    assert 'Extra Field' in data
    pos1 = data.find('Extra Field')
    pos2 = data.find('Test1')
    assert pos2 < pos1


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

    assert hasattr(view._create_form_class, 'test1')

    create_form = view.create_form()
    assert isinstance(create_form, TestForm)


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
        form_subdocuments={
            'subdoc': {
                'form_columns': ('name',)
            }
        }
    )

    assert hasattr(view1._create_form_class, 'subdoc')

    form = view1.create_form()
    assert 'name' in dir(form.subdoc.form)
    assert 'value' not in dir(form.subdoc.form)

    # Check exclude
    view2 = CustomModelView(
        Model1,
        form_subdocuments={
            'subdoc': {
                'form_excluded_columns': ('value',)
            }
        }
    )

    form = view2.create_form()
    assert 'name' in dir(form.subdoc.form)
    assert 'value' not in dir(form.subdoc.form)


def test_subdocument_class_config():
    app, db, admin = setup()

    from flask_admin.contrib.mongoengine import EmbeddedForm

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
        form_subdocuments={
            'subdoc': EmbeddedConfig()
        }
    )

    form = view1.create_form()
    assert 'name' in dir(form.subdoc.form)
    assert 'value' not in dir(form.subdoc.form)


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
        form_subdocuments={
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
    assert 'name' in dir(form.nested.form.comment.form)
    assert 'value' not in dir(form.nested.form.comment.form)


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
        form_subdocuments={
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

    assert 'name' in dir(inline_form)
    assert 'value' not in dir(inline_form)


def test_nested_sortedlist_subdocument():
    app, db, admin = setup()

    class Comment(db.EmbeddedDocument):
        name = db.StringField(max_length=20, required=True)
        value = db.StringField(max_length=20)

    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        subdoc = db.SortedListField(db.EmbeddedDocumentField(Comment))

    # Check only
    view1 = CustomModelView(
        Model1,
        form_subdocuments={
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

    assert 'name' in dir(inline_form)
    assert 'value' not in dir(inline_form)


def test_sortedlist_subdocument_validation():
    app, db, admin = setup()

    class Comment(db.EmbeddedDocument):
        name = db.StringField(max_length=20, required=True)
        value = db.StringField(max_length=20)

    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        subdoc = db.SortedListField(db.EmbeddedDocumentField(Comment))

    view = CustomModelView(Model1)
    admin.add_view(view)
    client = app.test_client()

    rv = client.post('/admin/model1/new/',
                     data={'test1': 'test1large', 'subdoc-0-name': 'comment', 'subdoc-0-value': 'test'})
    assert rv.status_code == 302

    rv = client.post('/admin/model1/new/',
                     data={'test1': 'test1large', 'subdoc-0-name': '', 'subdoc-0-value': 'test'})
    assert rv.status_code == 200
    assert b'This field is required' in rv.data


def test_list_subdocument_validation():
    app, db, admin = setup()

    class Comment(db.EmbeddedDocument):
        name = db.StringField(max_length=20, required=True)
        value = db.StringField(max_length=20)

    class Model1(db.Document):
        test1 = db.StringField(max_length=20)
        subdoc = db.ListField(db.EmbeddedDocumentField(Comment))

    view = CustomModelView(Model1)
    admin.add_view(view)
    client = app.test_client()

    rv = client.post('/admin/model1/new/',
                     data={'test1': 'test1large', 'subdoc-0-name': 'comment', 'subdoc-0-value': 'test'})
    assert rv.status_code == 302

    rv = client.post('/admin/model1/new/',
                     data={'test1': 'test1large', 'subdoc-0-name': '', 'subdoc-0-value': 'test'})
    assert rv.status_code == 200
    assert b'This field is required' in rv.data


def test_ajax_fk():
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

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

    assert u'model1' in view._form_ajax_refs

    model = Model1(test1=u'first')
    model.save()
    model2 = Model1(test1=u'foo', test2=u'bar').save()

    # Check loader
    loader = view._form_ajax_refs[u'model1']
    mdl = loader.get_one(model.id)
    assert mdl.test1 == model.test1

    items = loader.get_list(u'fir')
    assert len(items) == 1
    assert items[0].id == model.id

    items = loader.get_list(u'bar')
    assert len(items) == 1
    assert items[0].test1 == u'foo'

    # Check form generation
    form = view.create_form()
    assert form.model1.__class__.__name__ == u'AjaxSelectField'

    with app.test_request_context('/admin/view/'):
        assert u'value=""' not in form.model1()

        form.model1.data = model
        assert (u'data-json="[&quot;%s&quot;, &quot;first&quot;]"' % as_unicode(model.id) in form.model1() or
                u'data-json="[&#34;%s&#34;, &#34;first&#34;]"' % as_unicode(model.id) in form.model1())
        assert u'value="%s"' % as_unicode(model.id) in form.model1()

    # Check querying
    client = app.test_client()

    req = client.get(u'/admin/view/ajax/lookup/?name=model1&query=foo')
    assert req.data.decode('utf-8') == u'[["%s", "foo"]]' % model2.id

    # Check submitting
    client.post('/admin/view/new/', data={u'model1': as_unicode(model.id)})
    mdl = Model2.objects.first()

    assert mdl is not None
    assert mdl.model1 is not None
    assert mdl.model1.id == model.id
    assert mdl.model1.test1 == u'first'


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
        form_subdocuments={
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
    assert type(form.nested.form.comment).__name__ == 'AjaxSelectField'
    assert 'nested-comment' in view1._form_ajax_refs


def test_form_flat_choices():
    app, db, admin = setup()

    class Model(db.Document):
        name = db.StringField(max_length=20, choices=('a', 'b', 'c'))

    view = CustomModelView(Model)
    admin.add_view(view)

    form = view.create_form()
    assert form.name.choices == [('a', 'a'), ('b', 'b'), ('c', 'c')]


def test_form_args():
    app, db, admin = setup()

    class Model(db.Document):
        test = db.StringField(required=True)

    shared_form_args = {'test': {'validators': [validators.Regexp('test')]}}

    view = CustomModelView(Model, form_args=shared_form_args)
    admin.add_view(view)

    # ensure shared field_args don't create duplicate validators
    create_form = view.create_form()
    assert len(create_form.test.validators) == 2

    edit_form = view.edit_form()
    assert len(edit_form.test.validators) == 2


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
        form_args={
            'info': {'label': 'Information'},
            'timestamp': {'label': 'Last Updated Time'}
        }
    )
    admin.add_view(view)
    form = view.create_form()
    assert form.timestamp.label.text == 'Last Updated Time'
    # This is the failure
    assert form.info.label.text == 'Information'


def test_simple_list_pager():
    app, db, admin = setup()
    Model1, _ = create_models(db)

    class TestModelView(CustomModelView):
        simple_list_pager = True

        def get_count_query(self):
            assert False

    view = TestModelView(Model1)
    admin.add_view(view)

    count, data = view.get_list(0, None, None, None, None)
    assert count is None


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
    assert rv.status_code == 200
    assert "Test1,Test2\r\n" + \
        "test1_val_1,test2_val_1\r\n" + \
        "test1_val_2,test2_val_2\r\n" == data

    view = CustomModelView(Model1, can_export=True,
                           column_list=['test1', 'test2'],
                           endpoint='no_row_limit')
    admin.add_view(view)

    # test row limit without export_max_rows
    rv = client.get('/admin/no_row_limit/export/csv/')
    data = rv.data.decode('utf-8')
    assert rv.status_code == 200
    assert len(data.splitlines()) > 21
