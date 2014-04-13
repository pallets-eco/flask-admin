import warnings
import re

from flask import request, url_for, redirect, flash, abort, json, Response

from jinja2 import contextfunction

from flask.ext.admin.babel import gettext

from flask.ext.admin.base import BaseView, expose
from flask.ext.admin.form import BaseForm, FormOpts, rules
from flask.ext.admin.model import filters, typefmt
from flask.ext.admin.actions import ActionsMixin
from flask.ext.admin.helpers import get_form_data, validate_form_on_submit, get_redirect_target
from flask.ext.admin.tools import rec_getattr
from flask.ext.admin._backwards import ObsoleteAttr
from flask.ext.admin._compat import iteritems, OrderedDict
from .helpers import prettify_name, get_mdict_item_or_list
from .ajax import AjaxModelLoader


# Used to generate filter query string name
filter_char_re = re.compile('[^a-z0-9 ]')
filter_compact_re = re.compile(' +')


class BaseModelView(BaseView, ActionsMixin):
    """
        Base model view.

        This view does not make any assumptions on how models are stored or managed, but expects the following:

            1. The provided model is an object
            2. The model contains properties
            3. Each model contains an attribute which uniquely identifies it (i.e. a primary key for a database model)
            4. It is possible to retrieve a list of sorted models with pagination applied from a data source
            5. You can get one model by its identifier from the data source

        Essentially, if you want to support a new data store, all you have to do is:

            1. Derive from the `BaseModelView` class
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
                column_formatters = dict(price=lambda v, c, m, p: m.price*2)

        or using Jinja2 `macro` in template::

            from flask.ext.admin.model.template import macro

            class MyModelView(BaseModelView):
                column_formatters = dict(price=macro('render_price'))

            # in template
            {% macro render_price(model, column) %}
                {{ model.price * 2 }}
            {% endmacro %}

        The Callback function has the prototype::

            def formatter(view, context, model, name):
                # `view` is current administrative view
                # `context` is instance of jinja2.runtime.Context
                # `model` is model instance
                # `name` is property name
                pass
    """

    column_type_formatters = ObsoleteAttr('column_type_formatters', 'list_type_formatters', None)
    """
        Dictionary of value type formatters to be used in the list view.

        By default, two types are formatted:
        1. ``None`` will be displayed as an empty string
        2. ``bool`` will be displayed as a checkmark if it is ``True``

        If you don't like the default behavior and don't want any type formatters
        applied, just override this property with an empty dictionary::

            class MyModelView(BaseModelView):
                column_type_formatters = dict()

        If you want to display `NULL` instead of an empty string, you can do
        something like this::

            from flask.ext.admin.model import typefmt

            MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS)
            MY_DEFAULT_FORMATTERS.update({
                    type(None): typefmt.null_formatter
                })

            class MyModelView(BaseModelView):
                column_type_formatters = MY_DEFAULT_FORMATTERS

        Type formatters have lower priority than list column formatters.

        The callback function has following prototype::

            def type_formatter(view, value):
                # `view` is current administrative view
                # `value` value to format
                pass
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
        sorting, you can use a tuple::

            class MyModelView(BaseModelView):
                column_sortable_list = ('name', ('user', 'user.username'))

        When using SQLAlchemy models, model attributes can be used instead
        of strings::

            class MyModelView(BaseModelView):
                column_sortable_list = ('name', ('user', User.username))
    """

    column_default_sort = None
    """
        Default sort column if no sorting is applied.

        Example::

            class MyModelView(BaseModelView):
                column_default_sort = 'user'

        You can use tuple to control ascending descending order. In following example, items
        will be sorted in descending order::

            class MyModelView(BaseModelView):
                column_default_sort = ('user', True)
    """

    column_searchable_list = ObsoleteAttr('column_searchable_list',
                                          'searchable_columns',
                                          None)
    """
        A collection of the searchable columns. It is assumed that only
        text-only fields are searchable, but it is up to the model
        implementation to decide.

        Example::

            class MyModelView(BaseModelView):
                column_searchable_list = ('name', 'email')
    """

    column_choices = None
    """
        Map choices to columns in list view

        Example::

            class MyModelView(BaseModelView):
                column_choices = {
                    'my_column': [
                        ('db_value', 'display_value'),
                    ]
                }
    """

    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of :class:`~flask.ext.admin.model.filters.BaseFilter` classes.

        Example::

            class MyModelView(BaseModelView):
                column_filters = ('user', 'email')
    """

    named_filter_urls = False
    """
        Set to True to use human-readable names for filters in URL parameters.

        False by default so as to be robust across translations.

        Changing this parameter will break any existing URLs that have filters.
    """

    column_display_pk = ObsoleteAttr('column_display_pk',
                                     'list_display_pk',
                                     False)
    """
        Controls if the primary key should be displayed in the list view.
    """

    form = None
    """
        Form class. Override if you want to use custom form for your model.
        Will completely disable form scaffolding functionality.

        For example::

            class MyForm(Form):
                name = TextField('Name')

            class MyModelView(BaseModelView):
                form = MyForm
    """

    form_base_class = BaseForm
    """
        Base form class. Will be used by form scaffolding function when creating model form.

        Useful if you want to have custom contructor or override some fields.

        Example::

            class MyBaseForm(Form):
                def do_something(self):
                    pass

            class MyModelView(BaseModelView):
                form_base_class = MyBaseForm

    """

    form_args = None
    """
        Dictionary of form field arguments. Refer to WTForms documentation for
        list of possible options.

        Example::

            class MyModelView(BaseModelView):
                form_args = dict(
                    name=dict(label='First Name', validators=[required()])
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

    form_widget_args = None
    """
        Dictionary of form widget rendering arguments.
        Use this to customize how widget is rendered without using custom template.

        Example::

            class MyModelView(BaseModelView):
                form_widget_args = {
                    'description': {
                        'rows': 10,
                        'style': 'color: black'
                    }
                }
    """

    form_extra_fields = None
    """
        Dictionary of additional fields.

        Example::

            class MyModelView(BaseModelView):
                form_extra_fields = {
                    password: PasswordField('Password')
                }

        You can control order of form fields using ``form_columns`` property. For example::

            class MyModelView(BaseModelView):
                form_columns = ('name', 'email', 'password', 'secret')

                form_extra_fields = {
                    password: PasswordField('Password')
                }

        In this case, password field will be put between email and secret fields that are autogenerated.
    """

    form_ajax_refs = None
    """
        Use AJAX for foreign key model loading.

        Should contain dictionary, where key is field name and value is either a dictionary which
        configures AJAX lookups or backend-specific `AjaxModelLoader` class instance.

        For example, it can look like::

            class MyModelView(BaseModelView):
                form_ajax_refs = {
                    'user': {
                        'fields': ('first_name', 'last_name', 'email')
                        'page_size': 10
                    }
                }

        Or with SQLAlchemy backend like this::

            class MyModelView(BaseModelView):
                form_ajax_refs = {
                    'user': QueryAjaxModelLoader('user', db.session, User, fields=['email'], page_size=10)
                }

        If you need custom loading functionality, you can implement your custom loading behavior
        in your `AjaxModelLoader` class.
    """

    form_rules = None
    """
        List of rendering rules for model creation form.

        This property changed default form rendering behavior and makes possible to rearrange order
        of rendered fields, add some text between fields, group them, etc. If not set, will use
        default Flask-Admin form rendering logic.

        Here's simple example which illustrates how to use::

            from flask.ext.admin.form import rules

            class MyModelView(ModelView):
                form_rules = [
                    # Define field set with header text and four fields
                    rules.FieldSet(('first_name', 'last_name', 'email', 'phone'), 'User'),
                    # ... and it is just shortcut for:
                    rules.Header('User'),
                    rules.Field('first_name'),
                    rules.Field('last_name'),
                    # ...
                    # It is possible to create custom rule blocks:
                    MyBlock('Hello World'),
                    # It is possible to call macros from current context
                    rules.Macro('my_macro', foobar='baz')
                ]
    """

    form_edit_rules = None
    """
        Customized rules for the edit form. Override `form_rules` if present.
    """

    form_create_rules = None
    """
        Customized rules for the create form. Override `form_rules` if present.
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
        Default page size for pagination.
    """

    def __init__(self, model,
                 name=None, category=None, endpoint=None, url=None):
        """
            Constructor.

            :param model:
                Model class
            :param name:
                View name. If not provided, will use the model class name
            :param category:
                View category
            :param endpoint:
                Base endpoint. If not provided, will use the model name + 'view'.
                For example if model name was 'User', endpoint will be
                'userview'
            :param url:
                Base URL. If not provided, will use endpoint as a URL.
            :param debug:
                Enable debugging mode. Won't catch exceptions on model
                save failures.
        """

        # If name not provided, it is model name
        if name is None:
            name = '%s' % self._prettify_class_name(model.__name__)

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

        # Labels
        if self.column_labels is None:
            self.column_labels = {}

        # Forms
        self._form_ajax_refs = self._process_ajax_references()

        if self.form_widget_args is None:
            self.form_widget_args = {}

        self._create_form_class = self.get_create_form()
        self._edit_form_class = self.get_edit_form()

        # Search
        self._search_supported = self.init_search()

        # Choices
        if self.column_choices:
            self._column_choices_map = dict([
                (column, dict(choices))
                for column, choices in self.column_choices.items()
            ])
        else:
            self.column_choices = self._column_choices_map = dict()

        # Filters
        self._filters = self.get_filters()

        # Type formatters
        if self.column_type_formatters is None:
            self.column_type_formatters = dict(typefmt.BASE_FORMATTERS)

        if self.column_descriptions is None:
            self.column_descriptions = dict()

        # Group filters by field name
        if self._filters:
            self._filter_groups = OrderedDict()
            self._filter_args = {}

            for i, flt in enumerate(self._filters):
                if flt.name not in self._filter_groups:
                    self._filter_groups[flt.name] = []

                self._filter_groups[flt.name].append({
                    'index': i,
                    'arg': self.get_filter_arg(i, flt),
                    'operation': flt.operation(),
                    'options': flt.get_options(self) or None,
                    'type': flt.data_type
                })

                self._filter_args[self.get_filter_arg(i, flt)] = (i, flt)
        else:
            self._filter_groups = None
            self._filter_args = None

        # Form rendering rules
        if self.form_create_rules:
            self._form_create_rules = rules.RuleSet(self, self.form_create_rules)
        else:
            self._form_create_rules = None

        if self.form_edit_rules:
            self._form_edit_rules = rules.RuleSet(self, self.form_edit_rules)
        else:
            self._form_edit_rules = None

        if self.form_rules:
            form_rules = rules.RuleSet(self, self.form_rules)

            if not self._form_create_rules:
                self._form_create_rules = form_rules

            if not self._form_edit_rules:
                self._form_edit_rules = form_rules

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
            Return a human-readable column name.

            :param field:
                Model field name.
        """
        if self.column_labels and field in self.column_labels:
            return self.column_labels[field]
        else:
            return self._prettify_name(field)

    def get_list_columns(self):
        """
            Returns a list of the model field names. If `column_list` was
            set, returns it. Otherwise calls `scaffold_list_columns`
            to generate the list from the model.
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

            Expected return format is a dictionary, where keys are field names and
            values are property names.
        """
        raise NotImplemented('Please implement scaffold_sortable_columns method')

    def get_sortable_columns(self):
        """
            Returns a dictionary of the sortable columns. Key is a model
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

    # Filter helpers
    def scaffold_filters(self, name):
        """
            Generate filter object for the given name

            :param name:
                Name of the field
        """
        return None

    def is_valid_filter(self, filter):
        """
            Verify that the provided filter object is valid.

            Override in model backend implementation to verify if
            the provided filter type is allowed.

            :param filter:
                Filter object to verify.
        """
        return isinstance(filter, filters.BaseFilter)

    def get_filters(self):
        """
            Return a list of filter objects.

            If your model backend implementation does not support filters,
            override this method and return `None`.
        """
        if self.column_filters:
            collection = []

            for n in self.column_filters:
                if self.is_valid_filter(n):
                    collection.append(n)
                else:
                    flt = self.scaffold_filters(n)
                    if flt:
                        collection.extend(flt)
                    else:
                        raise Exception('Unsupported filter type %s' % n)
            return collection
        else:
            return None

    def get_filter_arg(self, index, flt):
        """
            Given a filter `flt`, return a unique name for that filter in
            this view.

            Does not include the `flt[n]_` portion of the filter name.

            :param index:
                Filter index in _filters array
            :param flt:
                Filter instance
        """
        if self.named_filter_urls:
            name = ('%s %s' % (flt.name, flt.operation())).lower()
            name = filter_char_re.sub('', name)
            name = filter_compact_re.sub('_', name)
            return name
        else:
            return str(index)

    # Form helpers
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
        return self._create_form_class(get_form_data(), obj=obj)

    def edit_form(self, obj=None):
        """
            Instantiate model editing form and return it.

            Override to implement custom behavior.
        """
        return self._edit_form_class(get_form_data(), obj=obj)

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

    def _get_default_order(self):
        """
            Return default sort order
        """
        if self.column_default_sort:
            if isinstance(self.column_default_sort, tuple):
                return self.column_default_sort
            else:
                return self.column_default_sort, False

        return None

    # Database-related API
    def get_list(self, page, sort_field, sort_desc, search, filters):
        """
            Return a paginated and sorted list of models from the data source.

            Must be implemented in the child class.

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

    # Model event handlers
    def on_model_change(self, form, model, is_created):
        """
            Perform some actions after a model is created or updated.

            Called from create_model and update_model in the same transaction
            (if it has any meaning for a store backend).

            By default does nothing.

            :param form:
                Form used to create/update model
            :param model:
                Model that will be created/updated
            :param is_created:
                Will be set to True if model was created and to False if edited
        """
        pass

    def _on_model_change(self, form, model, is_created):
        """
            Compatibility helper.
        """
        try:
            self.on_model_change(form, model, is_created)
        except TypeError:
            msg = ('%s.on_model_change() now accepts third ' +
                   'parameter is_created. Please update your code') % self.model
            warnings.warn(msg)

            self.on_model_change(form, model)

    def after_model_change(self, form, model, is_created):
        """
            Perform some actions after a model was created or updated and
            committed to the database.

            Called from create_model after successful database commit.

            By default does nothing.

            :param form:
                Form used to create/update model
            :param model:
                Model that was created/updated
            :param is_created:
                True if model was created, False if model was updated
        """
        pass

    def on_model_delete(self, model):
        """
            Perform some actions before a model is deleted.

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
    def _prettify_name(self, name):
        """
            Prettify pythonic variable name.

            For example, 'hello_world' will be converted to 'Hello World'

            :param name:
                Name to prettify
        """
        return prettify_name(name)

    def get_empty_list_message(self):
        return gettext('There are no items in the table.')

    # URL generation helpers
    def _get_list_filter_args(self):
        if self._filters:
            filters = []

            for n in request.args:
                if not n.startswith('flt'):
                    continue

                if '_' not in n:
                    continue

                pos, key = n[3:].split('_', 1)

                if key in self._filter_args:
                    idx, flt = self._filter_args[key]

                    value = request.args[n]

                    if flt.validate(value):
                        filters.append((pos, (idx, flt.clean(value))))

            # Sort filters
            return [v[1] for v in sorted(filters, key=lambda n: n[0])]

        return None

    def _get_list_extra_args(self):
        """
            Return arguments from query string.
        """
        page = request.args.get('page', 0, type=int)
        sort = request.args.get('sort', None, type=int)
        sort_desc = request.args.get('desc', None, type=int)
        search = request.args.get('search', None)
        filters = self._get_list_filter_args()

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
            for i, pair in enumerate(filters):
                idx, value = pair

                key = 'flt%d_%s' % (i, self.get_filter_arg(idx, self._filters[idx]))
                kwargs[key] = value

        return url_for(view, **kwargs)

    def is_action_allowed(self, name):
        """
            Override this method to allow or disallow actions based
            on some condition.

            The default implementation only checks if the particular action
            is not in `action_disallowed_list`.
        """
        return name not in self.action_disallowed_list

    def _get_field_value(self, model, name):
        """
            Get unformatted field value from the model
        """
        return rec_getattr(model, name)

    @contextfunction
    def get_list_value(self, context, model, name):
        """
            Returns the value to be displayed in the list view

            :param context:
                :py:class:`jinja2.runtime.Context`
            :param model:
                Model instance
            :param name:
                Field name
        """
        column_fmt = self.column_formatters.get(name)
        if column_fmt is not None:
            value = column_fmt(self, context, model, name)
        else:
            value = self._get_field_value(model, name)

        choices_map = self._column_choices_map.get(name, {})
        if choices_map:
            return choices_map.get(value) or value

        type_fmt = self.column_type_formatters.get(type(value))
        if type_fmt is not None:
            value = type_fmt(self, value)

        return value

    # AJAX references
    def _process_ajax_references(self):
        """
            Process `form_ajax_refs` and generate model loaders that
            will be used by the `ajax_lookup` view.
        """
        result = {}

        if self.form_ajax_refs:
            for name, options in iteritems(self.form_ajax_refs):
                if isinstance(options, dict):
                    result[name] = self._create_ajax_loader(name, options)
                elif isinstance(options, AjaxModelLoader):
                    result[name] = options
                else:
                    raise ValueError('%s.form_ajax_refs can not handle %s types' % (self, type(options)))

        return result

    def _create_ajax_loader(self, name, options):
        """
            Model backend will override this to implement AJAX model loading.
        """
        raise NotImplemented()

    # Views
    @expose('/')
    def index_view(self):
        """
            List view
        """
        # Grab parameters from URL
        page, sort_idx, sort_desc, search, filters = self._get_list_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(sort_idx)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get count and data
        count, data = self.get_list(page, sort_column, sort_desc,
                                    search, filters)

        # Calculate number of pages
        num_pages = count // self.page_size
        if count % self.page_size != 0:
            num_pages += 1

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
                               active_filters=filters,

                               # Actions
                               actions=actions,
                               actions_confirmation=actions_confirmation)

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        """
            Create model view
        """
        return_url = get_redirect_target() or url_for('.index_view')

        if not self.can_create:
            return redirect(return_url)

        form = self.create_form()

        if validate_form_on_submit(form):
            if self.create_model(form):
                if '_add_another' in request.form:
                    flash(gettext('Model was successfully created.'))
                    return redirect(url_for('.create_view', url=return_url))
                else:
                    return redirect(return_url)

        form_opts = FormOpts(widget_args=self.form_widget_args,
                             form_rules=self._form_create_rules)

        return self.render(self.create_template,
                           form=form,
                           form_opts=form_opts,
                           return_url=return_url)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """
            Edit model view
        """
        return_url = get_redirect_target() or url_for('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            return redirect(return_url)

        form = self.edit_form(obj=model)

        if validate_form_on_submit(form):
            if self.update_model(form, model):
                if '_continue_editing' in request.form:
                    flash(gettext('Model was successfully saved.'))
                    return redirect(request.url)
                else:
                    return redirect(return_url)

        form_opts = FormOpts(widget_args=self.form_widget_args,
                             form_rules=self._form_edit_rules)

        return self.render(self.edit_template,
                           model=model,
                           form=form,
                           form_opts=form_opts,
                           return_url=return_url)

    @expose('/delete/', methods=('POST',))
    def delete_view(self):
        """
            Delete model view. Only POST method is allowed.
        """
        return_url = get_redirect_target() or url_for('.index_view')

        # TODO: Use post
        if not self.can_delete:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')
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

    @expose('/ajax/lookup/')
    def ajax_lookup(self):
        name = request.args.get('name')
        query = request.args.get('query')
        offset = request.args.get('offset', type=int)
        limit = request.args.get('limit', 10, type=int)

        loader = self._form_ajax_refs.get(name)

        if not loader:
            abort(404)

        data = [loader.format(m) for m in loader.get_list(query, offset, limit)]
        return Response(json.dumps(data), mimetype='application/json')
