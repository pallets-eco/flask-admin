from flask import request, url_for, render_template, redirect

from .base import BaseView, expose


class BaseModelView(BaseView):
    # Permissions
    can_create = True
    can_edit = True
    can_delete = True

    # Templates
    list_template = 'admin/model/list.html'
    edit_template = 'admin/model/edit.html'
    create_template = 'admin/model/edit.html'

    # Customizations
    list_columns = None
    form_columns = None

    # Various settings
    page_size = 20

    def __init__(self, model, name=None, category=None, endpoint=None, url=None):
        # If name not provided, it is modelname
        if name is None:
            name = '%s' % self._prettify_name(model.__name__)

        # If endpoint not provided, it is modelname + 'view'
        if endpoint is None:
            endpoint = ('%sview' % model.__name__).lower()

        super(BaseModelView, self).__init__(name, category, endpoint, url)

        self.model = model

        # Scaffolding
        self.list_columns = self.get_list_columns()

        self.create_form = self.scaffold_create_form()
        self.edit_form = self.scaffold_edit_form()

    # Public API
    def get_list_columns(self):
        raise NotImplemented('Please implement get_list_columns method')

    def scaffold_form(self):
        raise NotImplemented('Please implement scaffold_form method')

    def scaffold_create_form(self):
        return self.scaffold_form()

    def scaffold_edit_form(self):
        return self.scaffold_form()

    # Database-related API
    def get_list(self, page, sort_field, sort_desc):
        raise NotImplemented('Please implement get_list method')

    def get_one(self, id):
        raise NotImplemented('Please implement get_one method')

    # Model handlers
    def create_model(self, form):
        raise NotImplemented()

    def update_model(self, form, model):
        raise NotImplemented()

    def delete_model(self, model):
        raise NotImplemented()

    # Various helpers
    def prettify_name(self, name):
        return ' '.join(x.capitalize() for x in name.split('_'))

    # URL generation helper
    def _get_extra_args(self):
        page = request.args.get('page', None, type=int)
        sort = request.args.get('sort', None, type=int)
        sort_desc = request.args.get('desc', None, type=int)

        return page, sort, sort_desc

    def _get_url(self, view, page, sort, sort_desc):
        return url_for(view, page=page, sort=sort, desc=sort_desc)

    # Views
    @expose('/')
    def index_view(self):
        # Grab parameters from URL
        page, sort, sort_desc = self._get_extra_args()

        # Get count and data
        count, data = self.get_list(page, sort, sort_desc)

        # Calculate number of pages
        num_pages = count / self.page_size
        if count % self.page_size != 0:
            num_pages += 1

        # Various URL generation helpers
        def pager_url(p):
            return self._get_url('.index_view', p, sort, sort_desc)

        def sort_url(column, invert=False):
            desc = None

            if invert and not sort_desc:
                desc = 1

            return self._get_url('.index_view', page, column, desc)

        return render_template(self.list_template,
                               view=self,
                               data=data,
                               # Return URL
                               return_url=self._get_url('.index_view', page, sort, sort_desc),
                               # Pagination
                               pager_url=pager_url,
                               num_pages=num_pages,
                               page=page,
                               # Sorting
                               sort_column=sort,
                               sort_desc=sort_desc,
                               sort_url=sort_url
                               )

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        return_url = request.args.get('return')

        if not self.can_create:
            return redirect(return_url or url_for('.index_view'))

        form = self.create_form(request.form)

        if form.validate_on_submit():
            if self.create_model(form):
                return redirect(return_url or url_for('.index_view'))

        return render_template(self.create_template, view=self, form=form)

    @expose('/edit/<int:id>/', methods=('GET', 'POST'))
    def edit_view(self, id):
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

        return render_template(self.edit_template,
                               view=self,
                               form=form,
                               return_url=return_url or url_for('.index_view'))

    @expose('/delete/<int:id>/')
    def delete_view(self, id):
        return_url = request.args.get('return')

        # TODO: Use post
        if not self.can_delete:
            return redirect(return_url or url_for('.index_view'))

        model = self.get_one(id)

        if model:
            self.delete_model(model)

        return redirect(return_url or url_for('.index_view'))
