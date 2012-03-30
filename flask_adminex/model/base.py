from itertools import count

from flask import request, url_for, redirect, flash

from flask.ext.adminex.base import BaseView, expose
from flask.ext.adminex.model import filters


class BaseModelView(BaseView):
    """
        Base model view.

        View does not make any assumptions on how models are stored or managed, but expects following:
        1. Model is an object
        2. Model contains properties
        3. Each model contains attribute which uniquely identifies it (i.e. primary key for database model)
        4. You can get list of sorted models with pagination applied from a data source
        5. You can get one model by its identifier from the data source

        Essentially, if you want to support new data store, all you have to do:
        1. Derive from `BaseModelView` class
        2. Implement various data-related methods (`get_list`, `get_one`, `create_model`, etc)
        3. Implement automatic form generation from the model representation (`scaffold_form`)
    """

    # Permissions
    can_create = True
    """Is model creation allowed"""

    can_edit = True
    """Is model editing allowed"""

    can_delete = True
    """Is model deletion allowed"""

    # Templates
    list_template = 'admin/model/list.html'
    """Default list view template"""

    edit_template = 'admin/model/edit.html'
    """Default edit template"""

    create_template = 'admin/model/create.html'
    """Default create template"""

    # Customizations
    list_columns = None
    """
        Collection of the model field names for the list view.
        If set to `None`, will get them from the model.

        For example::

            class MyModelView(BaseModelView):
                list_columns = ('name', 'last_name', 'email')
    """

    excluded_list_columns = None
    """
        Collection of excluded list column names.

        For example::

            class MyModelView(BaseModelView):
                excluded_list_columns = ('last_name', 'email')
    """

    rename_columns = None
    """
        Dictionary where key is column name and value is string to display.

        For example::

            class MyModelView(BaseModelView):
                rename_columns = dict(name='Name', last_name='Last Name')
    """

    sortable_columns = None
    """
        Collection of the sortable columns for the list view.
        If set to `None`, will get them from the model.

        For example::

            class MyModelView(BaseModelView):
                sortable_columns = ('name', 'last_name')

        If you want to explicitly specify field/column to be used while
        sorting, you can use tuple::

            class MyModelView(BaseModelView):
                sortable_columns = ('name', ('user', 'user.username'))

        For SQLAlchemy models, you can pass attribute instead of the string
        too::

            class MyModelView(BaseModelView):
                sortable_columns = ('name', ('user', User.username))
    """

    searchable_columns = None
    """
        Collection of the searchable columns. It is assumed that only
        text-only fields are searchable, but it is up for a model
        implementation to make decision.

        For example::

            class MyModelView(BaseModelView):
                searchable_columns = ('name', 'email')
    """

    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of :class:`flask.ext.adminex.model.filters.BaseFilter` classes.

        For example:

            class MyModelView(BaseModelView):
                column_filters = ('user', 'email')
    """

    form_columns = None
    """
        Collection of the model field names for the form. If set to `None` will
        get them from the model.

        For example:

            class MyModelView(BaseModelView):
                list_columns = ('name', 'email')
    """

    excluded_form_columns = None
    """
        Collection of excluded form field names.

        For example::

            class MyModelView(BaseModelView):
                excluded_form_columns = ('last_name', 'email')
    """

    form_args = None
    """
        Dictionary of form field arguments. Refer to WTForm documentation for
        list of possible options.

        Example::

            class MyModelView(BaseModelView):
                form_args = dict(
                    name=dict(label='First Name', validators=[wtf.required()])
                )
    """

    # Various settings
    page_size = 20
    """
        Default page size.
    """

    def __init__(self, model,
                 name=None, category=None, endpoint=None, url=None):
        """
            Constructor.

            `model`
                Model class
            `name`
                View name. If not provided, will use model class name
            `category`
                View category
            `endpoint`
                Base endpoint. If not provided, will use model name + 'view'.
                For example if model name was 'User', endpoint will be
                'userview'
            `url`
                Base URL. If not provided, will use endpoint as a URL.
        """

        # If name not provided, it is model name
        if name is None:
            name = '%s' % self._prettify_name(model.__name__)

        # If endpoint not provided, it is model name + 'view'
        if endpoint is None:
            endpoint = ('%sview' % model.__name__).lower()

        super(BaseModelView, self).__init__(name, category, endpoint, url)

        self.model = model

        # Scaffolding
        self._refresh_cache()

    # Caching
    def _refresh_cache(self):
        """
            Refresh various cached variables.
        """
        # Primary key
        self._primary_key = self.scaffold_pk()

        if self._primary_key is None:
            raise Exception('Model %s does not have primary key.' % self.model.__name__)

        # List view
        self._list_columns = self.get_list_columns()
        self._sortable_columns = self.get_sortable_columns()

        # Forms
        self._create_form_class = self.get_create_form()
        self._edit_form_class = self.get_edit_form()

        # Search
        self._search_supported = self.init_search()

        # Filters
        self._filters = self.get_filters()

        if self._filters:
            self._filter_names = [unicode(n) for n in self._filters]
            self._filter_types = dict((i, f.data_type)
                                      for i, f in enumerate(self._filters)
                                      if f.data_type)
        else:
            self._filter_names = None
            self._filter_types = None

    # Primary key
    def scaffold_pk(self):
        """
            Find model primary key name
        """
        raise NotImplemented()

    def get_pk_value(self, model):
        return getattr(model, self._primary_key)

    # List view
    def scaffold_list_columns(self):
        """
            Return list of the model field names. Must be implemented in
            the child class.

            Expected return format is list of tuples with field name and
            display text. For example::

                ['name', 'first_name', 'last_name']
        """
        raise NotImplemented('Please implement scaffold_list_columns method')

    def get_column_name(self, field):
        """
            Return human-readable column name.

            `field`
                Model field name.
        """
        if self.rename_columns and field in self.rename_columns:
            return self.rename_columns[field]
        else:
            return self.prettify_name(field)

    def get_list_columns(self):
        """
            Returns list of the model field names. If `list_columns` was
            set, returns it. Otherwise calls `scaffold_list_columns`
            to generate list from the model.
        """
        if self.list_columns is None:
            columns = self.scaffold_list_columns()
        else:
            columns = self.list_columns

        return [(c, self.get_column_name(c)) for c in columns]

    def scaffold_sortable_columns(self):
        """
            Returns dictionary of sortable columns. Must be implemented in
            the child class.

            Expected return format is dictionary, where key is field name and
            value is property name.
        """
        raise NotImplemented('Please implement scaffold_sortable_columns method')

    def get_sortable_columns(self):
        """
            Returns dictionary of the sortable columns. Key is a model
            field name and value is sort column (for example - attribute).

            If `sortable_columns` is set, will use it. Otherwise, will call
            `scaffold_sortable_columns` to get them from the model.
        """
        if self.sortable_columns is None:
            return self.scaffold_sortable_columns()
        else:
            result = dict()

            for c in self.sortable_columns:
                if isinstance(c, tuple):
                    result[c[0]] = c[1]
                else:
                    result[c] = c

            return result

    def init_search(self):
        """
            Initialize search. If data provider does not support search,
            `init_search` will return `False`.
        """
        return False

    def scaffold_filters(self, name):
        """
            Generate filter object for the given name

            `name`
                Name of the field
        """
        return None

    def is_valid_filter(self, filter):
        """
            Verify that provided filter object is valid.

            Override in model backend implementation to verify if
            provided filter type is allowed.

            `filter`
                Filter object to verify.
        """
        return isinstance(filter, filters.BaseFilter)

    def get_filters(self):
        """
            Return list of filter objects.

            If your model backend implementation does not support filters,
            override this method and return `None`.
        """
        if self.column_filters:
            collection = []

            for n in self.column_filters:
                if not self.is_valid_filter(n):
                    flt = self.scaffold_filters(n)
                    if flt:
                        collection.extend(flt)
                    else:
                        raise Exception('Unsupported filter type %s' % n)
                else:
                    collection.append(n)

            return collection
        else:
            return None

    def scaffold_form(self):
        """
            Create `form.BaseForm` inherited class from the model. Must be
            implemented in the child class.
        """
        raise NotImplemented('Please implement scaffold_form method')

    def get_create_form(self):
        """
            Create form class for model creation view.

            Override to implement customized behavior.
        """
        return self.scaffold_form()

    def get_edit_form(self):
        """
            Create form class for model editing view.

            Override to implement customized behavior.
        """
        return self.scaffold_form()

    def create_form(self, form, obj=None):
        """
            Instantiate model creation form and return it.

            Override to implement custom behavior.
        """
        return self._create_form_class(form, obj)

    def edit_form(self, form, obj=None):
        """
            Instantiate model editing form and return it.

            Override to implement custom behavior.
        """
        return self._edit_form_class(form, obj)

    # Helpers
    def is_sortable(self, name):
        """
            Verify if column is sortable.

            `name`
                Column name.
        """
        return name in self._sortable_columns

    def _get_column_by_idx(self, idx):
        """
            Return column index by
        """
        if idx is None or idx < 0 or idx >= len(self._list_columns):
            return None

        return self._list_columns[idx]

    # Database-related API
    def get_list(self, page, sort_field, sort_desc, search, filters):
        """
            Return list of models from the data source with applied pagination
            and sorting.

            Must be implemented in child class.

            `page`
                Page number, 0 based. Can be set to None if it is first page.
            `sort_field`
                Sort column name or None.
            `sort_desc`
                If set to True, sorting is in descending order.
            `search`
                Search query
            `filters`
                List of filter tuples. First value in a tuple is a search
                index, second value is a search value.
        """
        raise NotImplemented('Please implement get_list method')

    def get_one(self, id):
        """
            Return one model by its id.

            Must be implemented in the child class.

            `id`
                Model id
        """
        raise NotImplemented('Please implement get_one method')

    # Model handlers
    def create_model(self, form):
        """
            Create model from the form.

            Returns `True` if operation succeeded.

            Must be implemented in the child class.

            `form`
                Form instance
        """
        raise NotImplemented()

    def update_model(self, form, model):
        """
            Update model from the form.

            Returns `True` if operation succeeded.

            Must be implemented in the child class.

            `form`
                Form instance
            `model`
                Model instance
        """
        raise NotImplemented()

    def delete_model(self, model):
        """
            Delete model.

            Returns `True` if operation succeeded.

            Must be implemented in the child class.

            `model`
                Model instance
        """
        raise NotImplemented()

    # Various helpers
    def prettify_name(self, name):
        """
            Prettify pythonic variable name.

            For example, 'hello_world' will be converted to 'Hello World'

            `name`
                Name to prettify
        """
        return name.replace('_', ' ').title()

    # URL generation helper
    def _get_extra_args(self):
        """
            Return arguments from query string.
        """
        page = request.args.get('page', 0, type=int)
        sort = request.args.get('sort', None, type=int)
        sort_desc = request.args.get('desc', None, type=int)
        search = request.args.get('search', None)

        # Gather filters
        if self._filters:
            filters = []

            for n in count():
                param = 'flt%d' % n
                if param not in request.args:
                    break

                idx = request.args.get(param, None, type=int)
                value = request.args.get(param + 'v', None)

                if idx >= 0 and idx < len(self._filters):
                    flt = self._filters[idx]

                    if flt.validate(value):
                        filters.append((idx, flt.clean(value)))
        else:
            filters = None

        return page, sort, sort_desc, search, filters

    def _get_url(self, view=None, page=None, sort=None, sort_desc=None,
                 search=None, filters=None):
        """
            Generate page URL with current page, sort column and
            other parameters.

            `view`
                View name
            `page`
                Page number
            `sort`
                Sort column index
            `sort_desc`
                Use descending sorting order
            `search`
                Search query
            `filters`
                List of active filters
        """
        if not search:
            search = None

        if not page:
            page = None

        kwargs = dict(page=page, sort=sort, desc=sort_desc, search=search)

        if filters:
            for i, flt in enumerate(filters):
                base = 'flt%d' % i

                kwargs[base] = flt[0]
                kwargs[base + 'v'] = flt[1]

        return url_for(view, **kwargs)

    # Views
    @expose('/')
    def index_view(self):
        """
            List view
        """
        # Grab parameters from URL
        page, sort_idx, sort_desc, search, filters = self._get_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(sort_idx)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get count and data
        count, data = self.get_list(page, sort_column, sort_desc,
                                    search, filters)

        # Calculate number of pages
        num_pages = count / self.page_size
        if count % self.page_size != 0:
            num_pages += 1

        # Pregenerate filters
        if self._filters:
            filters_data = dict()

            for idx, f in enumerate(self._filters):
                flt_data = f.get_options(self)

                if flt_data:
                    filters_data[idx] = flt_data
        else:
            filters_data = None

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_url('.index_view', p, sort_idx, sort_desc,
                                 search, filters)

        def sort_url(column, invert=False):
            desc = None

            if invert and not sort_desc:
                desc = 1

            return self._get_url('.index_view', page, column, desc,
                                 search, filters)

        def get_value(obj, field):
            return getattr(obj, field, None)

        return self.render(self.list_template,
                               data=data,
                               # List
                               list_columns=self._list_columns,
                               sortable_columns=self._sortable_columns,
                               # Stuff
                               enumerate=enumerate,
                               get_pk_value=self.get_pk_value,
                               get_value=get_value,
                               return_url=self._get_url('.index_view',
                                                        page,
                                                        sort_idx,
                                                        sort_desc,
                                                        search,
                                                        filters),
                               # Pagination
                               pager_url=pager_url,
                               num_pages=num_pages,
                               page=page,
                               # Sorting
                               sort_column=sort_idx,
                               sort_desc=sort_desc,
                               sort_url=sort_url,
                               # Search
                               search_supported=self._search_supported,
                               clear_search_url=self._get_url('.index_view',
                                                              None,
                                                              sort_idx,
                                                              sort_desc),
                               search=search,
                               # Filters
                               filter_names=self._filter_names,
                               filter_types=self._filter_types,
                               filter_data=filters_data,
                               active_filters=filters
                               )

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        """
            Create model view
        """
        return_url = request.args.get('url')

        if not self.can_create:
            return redirect(return_url or url_for('.index_view'))

        form = self.create_form(request.form)

        if form.validate_on_submit():
            if self.create_model(form):
                if '_add_another' in request.form:
                    flash('Model was successfully created.')
                    return redirect(url_for('.create_view', url=return_url))
                else:
                    return redirect(return_url or url_for('.index_view'))

        return self.render(self.create_template,
                           form=form,
                           return_url=return_url)

    @expose('/edit/<int:id>/', methods=('GET', 'POST'))
    def edit_view(self, id):
        """
            Edit model view
        """
        return_url = request.args.get('url')

        if not self.can_edit:
            return redirect(return_url or url_for('.index_view'))

        model = self.get_one(id)

        if model is None:
            return redirect(return_url or url_for('.index_view'))

        form = self.edit_form(request.form, model)

        if form.validate_on_submit():
            if self.update_model(form, model):
                return redirect(return_url or url_for('.index_view'))

        return self.render(self.edit_template,
                               form=form,
                               return_url=return_url or url_for('.index_view'))

    @expose('/delete/<int:id>/', methods=('POST',))
    def delete_view(self, id):
        """
            Delete model view. Only POST method is allowed.
        """
        return_url = request.args.get('url')

        # TODO: Use post
        if not self.can_delete:
            return redirect(return_url or url_for('.index_view'))

        model = self.get_one(id)

        if model:
            self.delete_model(model)

        return redirect(return_url or url_for('.index_view'))
