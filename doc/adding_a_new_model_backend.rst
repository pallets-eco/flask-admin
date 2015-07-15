.. _adding-model-backend:

Adding A Model Backend
======================

Flask-Admin makes a few assumptions about the database models that it works with. If you want to implement your own
database backend, and still have Flask-Admin's model views work as expected, then you should take note of the following:

    1. Each model must have one field which acts as a `primary key` to uniquely identify instances of that model.
       However, there are no restriction on the data type or the field name of the `primary key` field.
    2. Models must make their data accessible as python properties.

If that is the case, then you can implement your own database backend by extending the `BaseModelView` class,
and implementing the set of scaffolding methods listed below.

Extending BaseModelView
-----------------------

    Start off by defining a new class, which derives from from :class:`~flask_admin.model.BaseModelView`::

        class MyDbModel(BaseModelView):
            pass

    This class inherits BaseModelView's `__init__` method, which accepts a model class as first argument. The model
    class is stored as the attribute ``self.model`` so that other methods may access it.

    Now, implement the following scaffolding methods for the new class:

    1. :meth:`~flask_admin.model.BaseModelView.get_pk_value`

        This method returns a primary key value from
        the model instance. In the SQLAlchemy backend, it gets the primary key from the model
        using :meth:`~flask_admin.contrib.sqla.ModelView.scaffold_pk`, caches it
        and then returns the value from the model whenever requested.

        For example::

            class MyDbModel(BaseModelView):
                def get_pk_value(self, model):
                    return self.model.id

    2. :meth:`~flask_admin.model.BaseModelView.scaffold_list_columns`

        Returns a list of columns to be displayed in a list view. For example::

            class MyDbModel(BaseModelView):
                def scaffold_list_columns(self):
                    columns = []

                    for p in dir(self.model):
                        attr = getattr(self.model)
                        if isinstance(attr, MyDbColumn):
                            columns.append(p)

                    return columns

    3. :meth:`~flask_admin.model.BaseModelView.scaffold_sortable_columns`

        Returns a dictionary of sortable columns. The keys in the dictionary should correspond to the model's
        field names. The values should be those variables that will be used for sorting.

        For example, in the SQLAlchemy backend it is possible to sort by a foreign key field. So, if there is a
        field named `user`, which is a foreign key for the `Users` table, and the `Users` table also has a name
        field, then the key will be `user` and value will be `Users.name`.

        If your backend does not support sorting, return
        `None` or an empty dictionary.

    4. :meth:`~flask_admin.model.BaseModelView.init_search`

        Initialize search functionality. If your backend supports
        full-text search, do initializations and return `True`.
        If your backend does not support full-text search, return
        `False`.

        For example, SQLAlchemy backend reads value of the `self.searchable_columns` and verifies if all fields are of
        text type, if they're local to the current model (if not,
        it will add a join, etc) and caches this information for
        future use.

    5. :meth:`~flask_admin.model.BaseModelView.scaffold_form`

        Generate `WTForms` form class from the model.

        For example::

            class MyDbModel(BaseModelView):
                def scaffold_form(self):
                    class MyForm(Form):
                        pass

                    # Do something
                    return MyForm

    6. :meth:`~flask_admin.model.BaseModelView.get_list`

        This method should return list of model instances with paging,
        sorting, etc applied.

        For SQLAlchemy backend it looks like:

            1. If search was enabled and provided search value is not empty,
               generate LIKE statements for each field from `self.searchable_columns`

            2. If filter values were passed, call `apply` method
               with values::

                    for flt, value in filters:
                        query = self._filters[flt].apply(query, value)

            3. Execute query to get total number of rows in the
               database (count)

            4. If `sort_column` was passed, will do something like (with some extra FK logic which is omitted in this example)::

                    if sort_desc:
                        query = query.order_by(desc(sort_field))
                    else:
                        query = query.order_by(sort_field)

            5. Apply paging

            6. Return count, list as a tuple

    7. :meth:`~flask_admin.model.BaseModelView.get_one`

        Return a model instance by its primary key.

    8. :meth:`~flask_admin.model.BaseModelView.create_model`

        Create a new instance of the model from the `Form` object.

    9. :meth:`~flask_admin.model.BaseModelView.update_model`

        Update the model instance with data from the form.

    10. :meth:`~flask_admin.model.BaseModelView.delete_model`

        Delete the specified model instance from the data store.

    11. :meth:`~flask_admin.model.BaseModelView.is_valid_filter`

        Verify whether the given object is a valid filter.

    12. :meth:`~flask_admin.model.BaseModelView.scaffold_filters`

        Return a list of filter objects for one model field.

        This method will be called once for each entry in the
        `self.column_filters` setting.

        If your backend does not know how to generate filters
        for the provided field, it should return `None`.

        For example::

            class MyDbModel(BaseModelView):
                def scaffold_filters(self, name):
                    attr = getattr(self.model, name)

                    if isinstance(attr, MyDbTextField):
                        return [MyEqualFilter(name, name)]

Implementing filters
--------------------

    Each model backend should have its own set of filter implementations. It is not possible to use the
    filters from SQLAlchemy models in a non-SQLAlchemy backend.
    This also means that different backends might have different set of available filters.

    The filter is a class derived from :class:`~flask_admin.model.filters.BaseFilter` which implements at least two methods:

        1. :meth:`~flask_admin.model.filters.BaseFilter.apply`
        2. :meth:`~flask_admin.model.filters.BaseFilter.operation`

    `apply` method accepts two parameters: `query` object and a value from the client. Here you can add
    filtering logic for the filter type.

    Lets take SQLAlchemy model backend as an example:

    All SQLAlchemy filters derive from :class:`~flask_admin.contrib.sqla.filters.BaseSQLAFilter` class.

    Each filter implements one simple filter SQL operation (like, not like, greater, etc) and accepts a column as
    input parameter.

    Whenever model view wants to apply a filter to a query
    object, it will call `apply` method in a filter class
    with a query and value. Filter will then apply
    real filter operation.

    For example::

        class MyBaseFilter(BaseFilter):
            def __init__(self, column, name, options=None, data_type=None):
                super(MyBaseFilter, self).__init__(name, options, data_type)

                self.column = column

        class MyEqualFilter(MyBaseFilter):
            def apply(self, query, value):
                return query.filter(self.column == value)

            def operation(self):
                return gettext('equals')

            # You can validate values. If value is not valid,
            # return `False`, so filter will be ignored.
            def validate(self, value):
                return True

            # You can "clean" values before they will be
            # passed to the your data access layer
            def clean(self, value):
                return value


Feel free ask questions if you have problems adding a new model backend.
Also, if you get stuck, try taking a look at the SQLAlchemy model backend and use it as a reference.
