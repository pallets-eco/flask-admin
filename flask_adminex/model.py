from flask import request, url_for, redirect

from .base import BaseView, expose


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

    create_template = 'admin/model/edit.html'
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

    form_columns = None
    """
        Collection of the model field names for the form. If set to `None` will
        get them from the model.

        For example:

            class MyModelView(BaseModelView):
                list_columns = ('name', 'email')
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
        self._list_columns = self.get_list_columns()
        self._sortable_columns = self.get_sortable_columns()

        self._create_form_class = self.get_create_form()
        self._edit_form_class = self.get_edit_form()

    # Public API
    def scaffold_list_columns(self):
        """
            Return list of the model field names. Must be implemented in
            the child class.

            Expected return format is list of tuples with field name and
            display text. For example::

                ['name', 'first_name', 'last_name']
        """
        raise NotImplemented('Please implement scaffold_list_columns method')

    def get_list_columns(self):
        """
            Returns list of the model field names. If `list_columns` was
            set, returns it. Otherwise calls `scaffold_list_columns`
            to generate list from the model.
        """
        result = []

        if self.list_columns is None:
            columns = self.scaffold_list_columns()
        else:
            columns = self.list_columns

        for c in columns:
            if self.rename_columns and c in self.rename_columns:
                result.append((c, self.rename_columns[c]))
            else:
                result.append((c, self.prettify_name(c)))

        return result

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

    def scaffold_form(self):
        """
            Create `form.BaseForm` inherited class from the model. Must be implemented in
            the child class.
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
    def get_list(self, page, sort_field, sort_desc):
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

        return page, sort, sort_desc

    def _get_url(self, view, page, sort, sort_desc):
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
        """
        return url_for(view, page=page, sort=sort, desc=sort_desc)

    # Views
    @expose('/')
    def index_view(self):
        """
            List view
        """
        # Grab parameters from URL
        page, sort_idx, sort_desc = self._get_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(sort_idx)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get count and data
        count, data = self.get_list(page, sort_column, sort_desc)

        # Calculate number of pages
        num_pages = count / self.page_size
        if count % self.page_size != 0:
            num_pages += 1

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_url('.index_view', p, sort_idx, sort_desc)

        def sort_url(column, invert=False):
            desc = None

            if invert and not sort_desc:
                desc = 1

            return self._get_url('.index_view', page, column, desc)

        def get_value(obj, field):
            return getattr(obj, field, None)

        return self.render(self.list_template,
                               data=data,
                               # List
                               list_columns=self._list_columns,
                               sortable_columns=self._sortable_columns,
                               # Stuff
                               get_value=get_value,
                               return_url=self._get_url('.index_view', page, sort_idx, sort_desc),
                               # Pagination
                               pager_url=pager_url,
                               num_pages=num_pages,
                               page=page,
                               # Sorting
                               sort_column=sort_idx,
                               sort_desc=sort_desc,
                               sort_url=sort_url
                               )

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        """
            Create model view
        """
        return_url = request.args.get('return')

        if not self.can_create:
            return redirect(return_url or url_for('.index_view'))

        form = self.create_form(request.form)

        if form.validate_on_submit():
            if self.create_model(form):
                return redirect(return_url or url_for('.index_view'))

        return self.render(self.create_template, form=form)

    @expose('/edit/<int:id>/', methods=('GET', 'POST'))
    def edit_view(self, id):
        """
            Edit model view
        """
        return_url = request.args.get('return')

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
        return_url = request.args.get('return')

        # TODO: Use post
        if not self.can_delete:
            return redirect(return_url or url_for('.index_view'))

        model = self.get_one(id)

        if model:
            self.delete_model(model)

        return redirect(return_url or url_for('.index_view'))
