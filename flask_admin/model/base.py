from flask import request, url_for, redirect, flash

from jinja2 import contextfunction

from flask.ext.admin.babel import gettext

from flask.ext.admin.base import BaseView, expose
from flask.ext.admin.tools import rec_getattr, ObsoleteAttr
from flask.ext.admin.model import filters, typefmt
from flask.ext.admin.actions import ActionsMixin


class BaseModelView(BaseView, ActionsMixin):
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
    column_list = ObsoleteAttr('column_list', 'list_columns', None)
    """
        Collection of the model field names for the list view.
        If set to `None`, will get them from the model.

        For example::

            class MyModelView(BaseModelView):
                column_list = ('name', 'last_name', 'email')
    """

    column_exclude_list = ObsoleteAttr('column_exclude_list',
                                       'excluded_list_columns', None)
    """
        Collection of excluded list column names.

        For example::

            class MyModelView(BaseModelView):
                column_exclude_list = ('last_name', 'email')
    """

    column_formatters = ObsoleteAttr('column_formatters', 'list_formatters', dict())
    """
        Dictionary of list view column formatters.

        For example, if you want to show price multiplied by
        two, you can do something like this::

            class MyModelView(BaseModelView):
                column_formatters = dict(price=lambda c, m, p: m.price*2)

        Callback function has following prototype::

            def formatter(context, model, name):
                # context is instance of jinja2.runtime.Context
                # model is model instance
                # name is property name
                pass
    """

    column_type_formatters = ObsoleteAttr('column_type_formatters', 'list_type_formatters', None)
    """
        Dictionary of value type formatters to be used in list view.

        By default, two types are formatted:
        1. ``None`` will be displayed as empty string
        2. ``bool`` will be displayed as check if it is ``True``

        If you don't like default behavior and don't want any type formatters
        applied, just override this property with empty dictionary::

            class MyModelView(BaseModelView):
                column_type_formatters = dict()

        If you want to display `NULL` instead of empty string, you can do
        something like this::

            from flask.ext.admin import typefmt

            MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS).extend({
                    type(None): typefmt.null_formatter
                })

            class MyModelView(BaseModelView):
                column_type_formatters = MY_DEFAULT_FORMATTERS

        Type formatters have lower priority than list column formatters.
    """

    column_labels = ObsoleteAttr('column_labels', 'rename_columns', None)
    """
        Dictionary where key is column name and value is string to display.

        For example::

            class MyModelView(BaseModelView):
                column_labels = dict(name='Name', last_name='Last Name')
    """

    column_descriptions = None
    """
        Dictionary where key is column name and
        value is description for `list view` column or add/edit form field.

        For example::

            class MyModelView(BaseModelView):
                column_descriptions = dict(
                    full_name='First and Last name'
                )
    """

    column_sortable_list = ObsoleteAttr('column_sortable_list',
                                        'sortable_columns',
                                        None)
    """
        Collection of the sortable columns for the list view.
        If set to `None`, will get them from the model.

        For example::

            class MyModelView(BaseModelView):
                column_sortable_list = ('name', 'last_name')

        If you want to explicitly specify field/column to be used while
        sorting, you can use tuple::

            class MyModelView(BaseModelView):
                column_sortable_list = ('name', ('user', 'user.username'))

        When using SQLAlchemy models, model attributes can be used instead
        of the string::

            class MyModelView(BaseModelView):
                column_sortable_list = ('name', ('user', User.username))
    """

    column_searchable_list = ObsoleteAttr('column_searchable_list',
                                          'searchable_columns',
                                          None)
    """
        Collection of the searchable columns. It is assumed that only
        text-only fields are searchable, but it is up for a model
        implementation to make decision.

        Example::

            class MyModelView(BaseModelView):
                column_searchable_list = ('name', 'email')
    """

    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of :class:`~flask.ext.admin.model.filters.BaseFilter` classes.

        Example::

            class MyModelView(BaseModelView):
                column_filters = ('user', 'email')
    """

    column_display_pk = ObsoleteAttr('column_display_pk',
                                     'list_display_pk',
                                     False)
    """
        Controls if primary key should be displayed in list view.
    """

    form = None
    """
        Form class. Override if you want to use custom form for your model.

        For example::

            class MyForm(wtf.Form):
                pass

            class MyModelView(BaseModelView):
                form = MyForm
    """

    form_args = None
    """
        Dictionary of form field arguments. Refer to WTForms documentation for
        list of possible options.

        Example::

            class MyModelView(BaseModelView):
                form_args = dict(
                    name=dict(label='First Name', validators=[wtf.required()])
                )
    """

    form_columns = None
    """
        Collection of the model field names for the form. If set to `None` will
        get them from the model.

        Example::

            class MyModelView(BaseModelView):
                form_columns = ('name', 'email')
    """

    form_excluded_columns = ObsoleteAttr('form_excluded_columns',
                                         'excluded_form_columns',
                                         None)
    """
        Collection of excluded form field names.

        For example::

            class MyModelView(BaseModelView):
                form_excluded_columns = ('last_name', 'email')
    """

    form_overrides = None
    """
        Dictionary of form column overrides.

        Example::

            class MyModelView(BaseModelView):
                form_overrides = dict(name=wtf.FileField)
    """

    # Actions
    action_disallowed_list = ObsoleteAttr('action_disallowed_list',
                                          'disallowed_actions',
                                          [])
    """
        Set of disallowed action names. For example, if you want to disable
        mass model deletion, do something like this:

            class MyModelView(BaseModelView):
                action_disallowed_list = ['delete']
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

            :param model:
                Model class
            :param name:
                View name. If not provided, will use model class name
            :param category:
                View category
            :param endpoint:
                Base endpoint. If not provided, will use model name + 'view'.
                For example if model name was 'User', endpoint will be
                'userview'
            :param url:
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

        # Actions
        self.init_actions()

        # Scaffolding
        self._refresh_cache()

    # Caching
    def _refresh_cache(self):
        """
            Refresh various cached variables.
        """
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

        # Type formatters
        if self.column_type_formatters is None:
            self.column_type_formatters = dict(typefmt.BASE_FORMATTERS)

        if self.column_descriptions is None:
            self.column_descriptions = dict()

        if self._filters:
            self._filter_groups = []
            self._filter_dict = dict()

            for i, n in enumerate(self._filters):
                if n.name not in self._filter_dict:
                    group = []
                    self._filter_dict[n.name] = group
                    self._filter_groups.append((n.name, group))
                else:
                    group = self._filter_dict[n.name]

                group.append((i, n.operation()))

            self._filter_types = dict((i, f.data_type)
                                      for i, f in enumerate(self._filters)
                                      if f.data_type)
        else:
            self._filter_groups = None
            self._filter_types = None

    # Primary key
    def get_pk_value(self, model):
        """
            Return PK value from a model object.
        """
        raise NotImplemented()

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

            :param field:
                Model field name.
        """
        if self.column_labels and field in self.column_labels:
            return self.column_labels[field]
        else:
            return self.prettify_name(field)

    def get_list_columns(self):
        """
            Returns list of the model field names. If `column_list` was
            set, returns it. Otherwise calls `scaffold_list_columns`
            to generate list from the model.
        """
        columns = self.column_list

        if columns is None:
            columns = self.scaffold_list_columns()

            # Filter excluded columns
            if self.column_exclude_list:
                columns = [c for c in columns if c not in self.column_exclude_list]

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

            If `column_sortable_list` is set, will use it. Otherwise, will call
            `scaffold_sortable_columns` to get them from the model.
        """
        if self.column_sortable_list is None:
            return self.scaffold_sortable_columns() or dict()
        else:
            result = dict()

            for c in self.column_sortable_list:
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

            :param name:
                Name of the field
        """
        return None

    def is_valid_filter(self, filter):
        """
            Verify that provided filter object is valid.

            Override in model backend implementation to verify if
            provided filter type is allowed.

            :param filter:
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

    def get_form(self):
        """
            Get form class.

            If ``self.form`` is set, will return it and will call
            ``self.scaffold_form`` otherwise.

            Override to implement customized behavior.
        """
        if self.form is not None:
            return self.form

        return self.scaffold_form()

    def get_create_form(self):
        """
            Create form class for model creation view.

            Override to implement customized behavior.
        """
        return self.get_form()

    def get_edit_form(self):
        """
            Create form class for model editing view.

            Override to implement customized behavior.
        """
        return self.get_form()

    def create_form(self, obj=None):
        """
            Instantiate model creation form and return it.

            Override to implement custom behavior.
        """
        return self._create_form_class(obj=obj)

    def edit_form(self, obj=None):
        """
            Instantiate model editing form and return it.

            Override to implement custom behavior.
        """
        return self._edit_form_class(obj=obj)

    # Helpers
    def is_sortable(self, name):
        """
            Verify if column is sortable.

            :param name:
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

            :param page:
                Page number, 0 based. Can be set to None if it is first page.
            :param sort_field:
                Sort column name or None.
            :param sort_desc:
                If set to True, sorting is in descending order.
            :param search:
                Search query
            :param filters:
                List of filter tuples. First value in a tuple is a search
                index, second value is a search value.
        """
        raise NotImplemented('Please implement get_list method')

    def get_one(self, id):
        """
            Return one model by its id.

            Must be implemented in the child class.

            :param id:
                Model id
        """
        raise NotImplemented('Please implement get_one method')

    # Model handlers
    def on_model_change(self, form, model):
        """
            Allow to do some actions after a model was created or updated.

            Called from create_model and update_model in the same transaction
            (if it has any meaning for a store backend).

            By default do nothing.
        """
        pass

    def on_model_delete(self, model):
        """
            Allow to do some actions before a model will be deleted.

            Called from delete_model in the same transaction
            (if it has any meaning for a store backend).

            By default do nothing.
        """
        pass

    def create_model(self, form):
        """
            Create model from the form.

            Returns `True` if operation succeeded.

            Must be implemented in the child class.

            :param form:
                Form instance
        """
        raise NotImplemented()

    def update_model(self, form, model):
        """
            Update model from the form.

            Returns `True` if operation succeeded.

            Must be implemented in the child class.

            :param form:
                Form instance
            :param model:
                Model instance
        """
        raise NotImplemented()

    def delete_model(self, model):
        """
            Delete model.

            Returns `True` if operation succeeded.

            Must be implemented in the child class.

            :param model:
                Model instance
        """
        raise NotImplemented()

    # Various helpers
    def prettify_name(self, name):
        """
            Prettify pythonic variable name.

            For example, 'hello_world' will be converted to 'Hello World'

            :param name:
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
            sfilters = []

            for n in request.args:
                if n.startswith('flt'):
                    ofs = n.find('_')
                    if ofs == -1:
                        continue

                    try:
                        pos = int(n[3:ofs])
                        idx = int(n[ofs + 1:])
                    except ValueError:
                        continue

                    if idx >= 0 and idx < len(self._filters):
                        flt = self._filters[idx]

                        value = request.args[n]

                        if flt.validate(value):
                            sfilters.append((pos, (idx, flt.clean(value))))

            filters = [v[1] for v in sorted(sfilters, key=lambda n: n[0])]
        else:
            filters = None

        return page, sort, sort_desc, search, filters

    def _get_url(self, view=None, page=None, sort=None, sort_desc=None,
                 search=None, filters=None):
        """
            Generate page URL with current page, sort column and
            other parameters.

            :param view:
                View name
            :param page:
                Page number
            :param sort:
                Sort column index
            :param sort_desc:
                Use descending sorting order
            :param search:
                Search query
            :param filters:
                List of active filters
        """
        if not search:
            search = None

        if not page:
            page = None

        kwargs = dict(page=page, sort=sort, desc=sort_desc, search=search)

        if filters:
            for i, flt in enumerate(filters):
                key = 'flt%d_%d' % (i, flt[0])
                kwargs[key] = flt[1]

        return url_for(view, **kwargs)

    def is_action_allowed(self, name):
        """
            Override this method to allow or disallow actions based
            on some condition.

            Default implementation only checks if particular action
            is not in `action_disallowed_list`.
        """
        return name not in self.action_disallowed_list

    @contextfunction
    def get_list_value(self, context, model, name):
        """
            Returns value to be displayed in list view

            :param context:
                :py:class:`jinja2.runtime.Context`
            :param model:
                Model instance
            :param name:
                Field name
        """
        column_fmt = self.column_formatters.get(name)
        if column_fmt is not None:
            return column_fmt(context, model, name)

        value = rec_getattr(model, name)

        type_fmt = self.column_type_formatters.get(type(value))
        if type_fmt is not None:
            value = type_fmt(value)

        return value

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

        # Actions
        actions, actions_confirmation = self.get_actions_list()

        return self.render(self.list_template,
                               data=data,
                               # List
                               list_columns=self._list_columns,
                               sortable_columns=self._sortable_columns,
                               # Stuff
                               enumerate=enumerate,
                               get_pk_value=self.get_pk_value,
                               get_value=self.get_list_value,
                               return_url=self._get_url('.index_view',
                                                        page,
                                                        sort_idx,
                                                        sort_desc,
                                                        search,
                                                        filters),
                               # Pagination
                               count=count,
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
                               filters=self._filters,
                               filter_groups=self._filter_groups,
                               filter_types=self._filter_types,
                               filter_data=filters_data,
                               active_filters=filters,

                               # Actions
                               actions=actions,
                               actions_confirmation=actions_confirmation
                               )

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        """
            Create model view
        """
        return_url = request.args.get('url') or url_for('.index_view')

        if not self.can_create:
            return redirect(return_url)

        form = self.create_form()

        if form.validate_on_submit():
            if self.create_model(form):
                if '_add_another' in request.form:
                    flash(gettext('Model was successfully created.'))
                    return redirect(url_for('.create_view', url=return_url))
                else:
                    return redirect(return_url)

        return self.render(self.create_template,
                           form=form,
                           return_url=return_url)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """
            Edit model view
        """
        return_url = request.args.get('url') or url_for('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        id = request.args.get('id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            return redirect(return_url)

        form = self.edit_form(obj=model)

        if form.validate_on_submit():
            if self.update_model(form, model):
                return redirect(return_url)

        return self.render(self.edit_template,
                               form=form,
                               return_url=return_url)

    @expose('/delete/', methods=('POST',))
    def delete_view(self):
        """
            Delete model view. Only POST method is allowed.
        """
        return_url = request.args.get('url') or url_for('.index_view')

        # TODO: Use post
        if not self.can_delete:
            return redirect(return_url)

        id = request.args.get('id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model:
            self.delete_model(model)

        return redirect(return_url)

    @expose('/action/', methods=('POST',))
    def action_view(self):
        """
            Mass-model action view.
        """
        return self.handle_action()
