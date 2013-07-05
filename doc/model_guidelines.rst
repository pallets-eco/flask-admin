Adding new model backend
========================

If you want to implement new database backend to use with model views, follow steps found in this guideline.

There are few assumptions about models:

    1. Model has "primary key" - value which uniquely identifies
       one model in a data store. There's no restriction on the
       data type or field name.
    2. Model has readable python properties
    3. It is possible to get list of models (optionally - sorted,
       filtered, etc) from data store
    4. It is possible to get one model by its primary key


Steps to add new model backend:

    1. Create new class and derive it from :class:`~flask.ext.admin.model.BaseModelView`::

        class MyDbModel(BaseModelView):
            pass

    By default, all model views accept model class and it
    will be stored as ``self.model``.

    2. Implement following scaffolding methods:

    - :meth:`~flask.ext.admin.model.BaseModelView.get_pk_value`

    This method will return primary key value from
    the model. For example, in SQLAlchemy backend,
    it gets primary key from the model using :meth:`~flask.ext.admin.contrib.sqla.ModelView.scaffold_pk`, caches it
    and returns actual value from the model when requested.

    For example::

        class MyDbModel(BaseModelView):
            def get_pk_value(self, model):
                return self.model.id

    - :meth:`~flask.ext.admin.model.BaseModelView.scaffold_list_columns`

    Returns list of columns to be displayed in a list view.

    For example::

        class MyDbModel(BaseModelView):
            def scaffold_list_columns(self):
                columns = []

                for p in dir(self.model):
                    attr = getattr(self.model)
                    if isinstance(attr, MyDbColumn):
                        columns.append(p)

                return columns

    - :meth:`~flask.ext.admin.model.BaseModelView.scaffold_sortable_columns`

    Returns dictionary of sortable columns. Key in a dictionary is field name. Value - implementation
    specific, value that will be used by you backend implementation to do actual sort operation.

    For example, in SQLAlchemy backend it is possible to
    sort by foreign key. If there's a field `user` and
    it is foreign key for a `Users` table which has a name
    field, key will be `user` and value will be `Users.name`.

    If your backend does not support sorting, return
    `None` or empty dictionary.

    - :meth:`~flask.ext.admin.model.BaseModelView.init_search`

    Initialize search functionality. If your backend supports
    full-text search, do initializations and return `True`.
    If your backend does not support full-text search, return
    `False`.

    For example, SQLAlchemy backend reads value of the `self.searchable_columns` and verifies if all fields are of
    text type, if they're local to the current model (if not,
    it will add a join, etc) and caches this information for
    future use.

    - :meth:`~flask.ext.admin.model.BaseModelView.is_valid_filter`

    Verify if provided object is a valid filter.

    Each model backend should have its own set of
    filter implementations. It is not possible to use
    filters from SQLAlchemy models in non-SQLAlchemy backend.
    This also means that different backends might have
    different set of available filters.

    Filter is a class derived from :class:`~flask.ext.admin.model.filters.BaseFilter` which implements at least two methods:

        1. :meth:`~flask.ext.admin.model.filters.BaseFilter.apply`
        2. :meth:`~flask.ext.admin.model.filters.BaseFilter.operation`

    `apply` method accepts two parameters: `query` object and a value from the client. Here you will add
    filtering logic for this filter type.

    Lets take SQLAlchemy model backend as an example.
    All SQLAlchemy filters derive from :class:`~flask.ext.admin.contrib.sqla.filters.BaseSQLAFilter` class.

    Each filter implements one simple filter SQL operation
    (like, not like, greater, etc) and accepts column as
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

    - :meth:`~flask.ext.admin.model.BaseModelView.scaffold_filters`

    Return list of filter objects for one model field.

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

    - :meth:`~flask.ext.admin.model.BaseModelView.scaffold_form`

        Generate `WTForms` form class from the model.

        For example::

            class MyDbModel(BaseModelView):
                def scaffold_form(self):
                    class MyForm(Form):
                        pass

                    # Do something
                    return MyForm

        - :meth:`~flask.ext.admin.model.BaseModelView.get_list`

        This method should return list of models with paging,
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

        - :meth:`~flask.ext.admin.model.BaseModelView.get_one`

        Return one model by its primary key.

        - :meth:`~flask.ext.admin.model.BaseModelView.create_model`

        Create new model from the `Form` object.

        - :meth:`~flask.ext.admin.model.BaseModelView.update_model`

        Update provided model with the data from the form.

        - :meth:`~flask.ext.admin.model.BaseModelView.delete_model`

        Delete provided model from the data store.

Feel free ask questions if you have problem adding new model backend.
Also, it is good idea to take a look on SQLAlchemy model backend to
see how it works in different circumstances.
