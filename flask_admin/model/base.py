import warnings
import re

from flask import (request, redirect, flash, abort, json, Response,
                   get_flashed_messages)
from jinja2 import contextfunction
from wtforms.fields import HiddenField
from wtforms.validators import ValidationError, Required

from flask.ext.admin.babel import gettext

from flask.ext.admin.base import BaseView, expose
from flask.ext.admin.form import BaseForm, FormOpts, rules
from flask.ext.admin.model import filters, typefmt
from flask.ext.admin.actions import ActionsMixin
from flask.ext.admin.helpers import (get_form_data, validate_form_on_submit,
                                     get_redirect_target, flash_errors)
from flask.ext.admin.tools import rec_getattr
from flask.ext.admin._backwards import ObsoleteAttr
from flask.ext.admin._compat import iteritems, OrderedDict, as_unicode
from .helpers import prettify_name, get_mdict_item_or_list
from .ajax import AjaxModelLoader
from .fields import ListEditableFieldList


# Used to generate filter query string name
filter_char_re = re.compile('[^a-z0-9 ]')
filter_compact_re = re.compile(' +')


class ViewArgs(object):
    """
        List view arguments.
    """
    def __init__(self, page=None, sort=None, sort_desc=None, search=None, filters=None, extra_args=None):
        self.page = page
        self.sort = sort
        self.sort_desc = bool(sort_desc)
        self.search = search
        self.filters = filters

        if not self.search:
            self.search = None

        self.extra_args = extra_args or dict()

    def clone(self, **kwargs):
        if self.filters:
            flt = list(self.filters)
        else:
            flt = None

        kwargs.setdefault('page', self.page)
        kwargs.setdefault('sort', self.sort)
        kwargs.setdefault('sort_desc', self.sort_desc)
        kwargs.setdefault('search', self.search)
        kwargs.setdefault('filters', flt)
        kwargs.setdefault('extra_args', dict(self.extra_args))

        return ViewArgs(**kwargs)


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

    column_editable_list = None
    """
        Collection of the columns which can be edited from the list view.

        For example::

            class MyModelView(BaseModelView):
                column_editable_list = ('name', 'last_name')
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
                name = StringField('Name')

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

            from wtforms.validators import required
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

        Changing the format of a DateTimeField will require changes to both form_widget_args and form_args.

        Example::

            form_args = dict(
                start=dict(format='%Y-%m-%d %I:%M %p') # changes how the input is parsed by strptime (12 hour time)
            )
            form_widget_args = dict(
                start={'data-date-format': u'yyyy-mm-dd HH:ii P', 'data-show-meridian': 'True'} # changes how the DateTimeField displays the time
            )
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
                 name=None, category=None, endpoint=None, url=None, static_folder=None,
                 menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
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
            :param menu_class_name:
                Optional class name for the menu item.
            :param menu_icon_type:
                Optional icon. Possible icon types:

                 - `flask.ext.admin.consts.ICON_TYPE_GLYPH` - Bootstrap glyph icon
                 - `flask.ext.admin.consts.ICON_TYPE_IMAGE` - Image relative to Flask static directory
                 - `flask.ext.admin.consts.ICON_TYPE_IMAGE_URL` - Image with full URL
            :param menu_icon_value:
                Icon glyph name or URL, depending on `menu_icon_type` setting
        """

        # If name not provided, it is model name
        if name is None:
            name = '%s' % self._prettify_class_name(model.__name__)

        # If endpoint not provided, it is model name
        if endpoint is None:
            endpoint = model.__name__.lower()

        super(BaseModelView, self).__init__(name, category, endpoint, url, static_folder,
                                            menu_class_name=menu_class_name,
                                            menu_icon_type=menu_icon_type,
                                            menu_icon_value=menu_icon_value)

        self.model = model

        # Actions
        self.init_actions()

        # Scaffolding
        self._refresh_cache()

    # Caching
    def _refresh_forms_cache(self):
        # Forms
        self._form_ajax_refs = self._process_ajax_references()

        if self.form_widget_args is None:
            self.form_widget_args = {}

        self._create_form_class = self.get_create_form()
        self._edit_form_class = self.get_edit_form()
        self._delete_form_class = self.get_delete_form()

        # List View In-Line Editing
        if self.column_editable_list:
            self._list_form_class = self.get_list_form()
        else:
            self.column_editable_list = {}

    def _refresh_filters_cache(self):
        self._filters = self.get_filters()

        if self._filters:
            self._filter_groups = OrderedDict()
            self._filter_args = {}

            for i, flt in enumerate(self._filters):
                if flt.name not in self._filter_groups:
                    self._filter_groups[flt.name] = []

                self._filter_groups[flt.name].append({
                    'index': i,
                    'arg': self.get_filter_arg(i, flt),
                    'operation': as_unicode(flt.operation()),
                    'options': flt.get_options(self) or None,
                    'type': flt.data_type
                })

                self._filter_args[self.get_filter_arg(i, flt)] = (i, flt)
        else:
            self._filter_groups = None
            self._filter_args = None

    def _refresh_form_rules_cache(self):
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
        self._refresh_forms_cache()

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

        # Type formatters
        if self.column_type_formatters is None:
            self.column_type_formatters = dict(typefmt.BASE_FORMATTERS)

        if self.column_descriptions is None:
            self.column_descriptions = dict()

        # Filters
        self._refresh_filters_cache()

        # Form rendering rules
        self._refresh_form_rules_cache()

    # Primary key
    def get_pk_value(self, model):
        """
            Return PK value from a model object.
        """
        raise NotImplementedError()

    # List view
    def scaffold_list_columns(self):
        """
            Return list of the model field names. Must be implemented in
            the child class.

            Expected return format is list of tuples with field name and
            display text. For example::

                ['name', 'first_name', 'last_name']
        """
        raise NotImplementedError('Please implement scaffold_list_columns method')

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
        raise NotImplementedError('Please implement scaffold_sortable_columns method')

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

    def handle_filter(self, filter):
        """
            Postprocess (add joins, etc) for a filter.

            :param filter:
                Filter object to postprocess
        """
        return filter

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
                    collection.append(self.handle_filter(n))
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
            name = ('%s %s' % (flt.name, as_unicode(flt.operation()))).lower()
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
        raise NotImplementedError('Please implement scaffold_form method')

    def scaffold_list_form(self, custom_fieldlist=ListEditableFieldList,
                           validators=None):
        """
            Create form for the `index_view` using only the columns from
            `self.column_editable_list`.

            :param validators:
                `form_args` dict with only validators
                {'name': {'validators': [required()]}}
            :param custom_fieldlist:
                A WTForm FieldList class. By default, `ListEditableFieldList`.

            Must be implemented in the child class.
        """
        raise NotImplementedError('Please implement scaffold_list_form method')

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

    def get_list_form(self):
        """
            Get form class for the editable list view.

            Uses only validators from `form_args` to build the form class.

            Allows overriding the editable list view field/widget. For example::

                from flask.ext.admin.model.fields import ListEditableFieldList
                from flask.ext.admin.model.widgets import XEditableWidget

                class CustomWidget(XEditableWidget):
                    def get_kwargs(self, subfield, kwargs):
                        if subfield.type == 'TextAreaField':
                            kwargs['data-type'] = 'textarea'
                            kwargs['data-rows'] = '20'
                        # elif: kwargs for other fields

                        return kwargs

                class CustomFieldList(ListEditableFieldList):
                    widget = CustomWidget()

                class MyModelView(BaseModelView):
                    def get_list_form(self):
                        return self.scaffold_list_form(CustomFieldList)
        """
        if self.form_args:
            # get only validators, other form_args can break FieldList wrapper
            validators = dict(
                (key, {'validators': value["validators"]})
                for key, value in iteritems(self.form_args)
                if value.get("validators")
            )
        else:
            validators = None

        return self.scaffold_list_form(validators=validators)

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

    def get_delete_form(self):
        """
            Create form class for model delete view.

            Override to implement customized behavior.
        """
        class DeleteForm(self.form_base_class):
            id = HiddenField(validators=[Required()])
            url = HiddenField()

        return DeleteForm

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

    def delete_form(self):
        """
            Instantiate model delete form and return it.

            Override to implement custom behavior.
            
            The delete form originally used a GET request, so delete_form
            accepts both GET and POST request for backwards compatibility.
        """
        if request.form:
            return self._delete_form_class(request.form)
        elif request.args:
            # allow request.args for backward compatibility
            return self._delete_form_class(request.args)
        else:
            return self._delete_form_class()

    def list_form(self, obj=None):
        """
            Instantiate model editing form for list view and return it.

            Override to implement custom behavior.
        """
        return self._list_form_class(get_form_data(), obj=obj)

    def validate_form(self, form):
        """
            Validate the form on submit.

            :param form:
                Form to validate
        """
        return validate_form_on_submit(form)

    # Helpers
    def is_sortable(self, name):
        """
            Verify if column is sortable.

            Not case-sensitive.

            :param name:
                Column name.
        """
        return name.lower() in (x.lower() for x in self._sortable_columns)

    def is_editable(self, name):
        """
            Verify if column is editable.

            :param name:
                Column name.
        """
        return name in self.column_editable_list

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
        raise NotImplementedError('Please implement get_list method')

    def get_one(self, id):
        """
            Return one model by its id.

            Must be implemented in the child class.

            :param id:
                Model id
        """
        raise NotImplementedError('Please implement get_one method')

    # Exception handler
    def handle_view_exception(self, exc):
        if isinstance(exc, ValidationError):
            flash(as_unicode(exc))
            return True

        if self._debug:
            raise

        return False

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

    def on_form_prefill (self, form, id):
        """
            Perform additional actions to pre-fill the edit form.

            Called from edit_view, if the current action is rendering
            the form rather than receiving client side input, after
            default pre-filling has been performed.

            By default does nothing.

            You only need to override this if you have added custom
            fields that depend on the database contents in a way that
            Flask-admin can't figure out by itself. Fields that were
            added by name of a normal column or relationship should
            work out of the box.

            :param form:
                Form instance
            :param id:
                id of the object that is going to be edited
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
        raise NotImplementedError()

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
        raise NotImplementedError()

    def delete_model(self, model):
        """
            Delete model.

            Returns `True` if operation succeeded.

            Must be implemented in the child class.

            :param model:
                Model instance
        """
        raise NotImplementedError()

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
                        filters.append((pos, (idx, flt.name, value)))
                    else:
                        flash(gettext('Invalid Filter Value: %(value)s', value=value))

            # Sort filters
            return [v[1] for v in sorted(filters, key=lambda n: n[0])]

        return None

    def _get_list_extra_args(self):
        """
            Return arguments from query string.
        """
        return ViewArgs(page=request.args.get('page', 0, type=int),
                        sort=request.args.get('sort', None, type=int),
                        sort_desc=request.args.get('desc', None, type=int),
                        search=request.args.get('search', None),
                        filters=self._get_list_filter_args())

    # URL generation helpers
    def _get_list_url(self, view_args):
        """
            Generate page URL with current page, sort column and
            other parameters.

            :param view:
                View name
            :param view_args:
                ViewArgs object with page number, filters, etc.
        """
        page = view_args.page or None
        desc = 1 if view_args.sort_desc else None

        kwargs = dict(page=page, sort=view_args.sort, desc=desc, search=view_args.search)
        kwargs.update(view_args.extra_args)

        if view_args.filters:
            for i, pair in enumerate(view_args.filters):
                idx, flt_name, value = pair

                key = 'flt%d_%s' % (i, self.get_filter_arg(idx, self._filters[idx]))
                kwargs[key] = value

        return self.get_url('.index_view', **kwargs)

    # Actions
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

        type_fmt = None
        for typeobj, formatter in self.column_type_formatters.items():
            if isinstance(value, typeobj):
                type_fmt = formatter
                break
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
        raise NotImplementedError()

    # Views
    @expose('/')
    def index_view(self):
        """
            List view
        """
        if self.column_editable_list:
            form = self.list_form()
        else:
            form = None

        if self.can_delete:
            delete_form = self.delete_form()
        else:
            delete_form = None

        # Grab parameters from URL
        view_args = self._get_list_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(view_args.sort)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get count and data
        count, data = self.get_list(view_args.page, sort_column, view_args.sort_desc,
                                    view_args.search, view_args.filters)

        # Calculate number of pages
        num_pages = count // self.page_size
        if count % self.page_size != 0:
            num_pages += 1

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_list_url(view_args.clone(page=p))

        def sort_url(column, invert=False):
            desc = None

            if invert and not view_args.sort_desc:
                desc = 1

            return self._get_list_url(view_args.clone(sort=column, sort_desc=desc))

        # Actions
        actions, actions_confirmation = self.get_actions_list()

        clear_search_url = self._get_list_url(view_args.clone(page=0,
                                                              sort=view_args.sort,
                                                              sort_desc=view_args.sort_desc,
                                                              search=None,
                                                              filters=None))

        return self.render(
            self.list_template,
            data=data,
            form=form,
            delete_form=delete_form,

            # List
            list_columns=self._list_columns,
            sortable_columns=self._sortable_columns,
            editable_columns=self.column_editable_list,

            # Pagination
            count=count,
            pager_url=pager_url,
            num_pages=num_pages,
            page=view_args.page,

            # Sorting
            sort_column=view_args.sort,
            sort_desc=view_args.sort_desc,
            sort_url=sort_url,

            # Search
            search_supported=self._search_supported,
            clear_search_url=clear_search_url,
            search=view_args.search,

            # Filters
            filters=self._filters,
            filter_groups=self._filter_groups,
            active_filters=view_args.filters,

            # Actions
            actions=actions,
            actions_confirmation=actions_confirmation,

            # Misc
            enumerate=enumerate,
            get_pk_value=self.get_pk_value,
            get_value=self.get_list_value,
            return_url=self._get_list_url(view_args),
        )

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        """
            Create model view
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_create:
            return redirect(return_url)

        form = self.create_form()

        if self.validate_form(form):
            if self.create_model(form):
                if '_add_another' in request.form:
                    flash(gettext('Record was successfully created.'))
                    return redirect(request.url)
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
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            return redirect(return_url)

        form = self.edit_form(obj=model)

        if self.validate_form(form):
            if self.update_model(form, model):
                if '_continue_editing' in request.form:
                    flash(gettext('Record was successfully saved.'))
                    return redirect(request.url)
                else:
                    return redirect(return_url)

        if request.method == 'GET':
            self.on_form_prefill(form, id)

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
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_delete:
            return redirect(return_url)

        form = self.delete_form()

        if self.validate_form(form):
             # id is Required()
            id = form.id.data

            model = self.get_one(id)

            if model is None:
                return redirect(return_url)

            # message is flashed from within delete_model if it fails
            if self.delete_model(model):
                flash(gettext('Record was successfully deleted.'))
                return redirect(return_url)
        else:
            flash_errors(form, message='Failed to delete record. %(error)s')

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

    @expose('/ajax/update/', methods=('POST',))
    def ajax_update(self):
        """
            Edits a single column of a record in list view.
        """
        if not self.column_editable_list:
            abort(404)

        record = None
        form = self.list_form()

        # prevent validation issues due to submitting a single field
        # delete all fields except the field being submitted
        for field in form:
            # only the submitted field has a positive last_index
            if getattr(field, 'last_index', 0):
                record = self.get_one(str(field.last_index))
            elif field.name == 'csrf_token':
                pass
            else:
                form.__delitem__(field.name)

        if record is None:
            return gettext('Failed to update record. %(error)s', error=''), 500

        if self.validate_form(form):
            if self.update_model(form, record):
                # Success
                return gettext('Record was successfully saved.')
            else:
                # Error: No records changed, or problem saving to database.
                msgs = ", ".join([msg for msg in get_flashed_messages()])
                return gettext('Failed to update record. %(error)s',
                               error=msgs), 500
        else:
            for field in form:
                for error in field.errors:
                    # return validation error to x-editable
                    if isinstance(error, list):
                        return ", ".join(error), 500
                    else:
                        return error, 500
