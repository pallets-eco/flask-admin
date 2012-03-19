from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.interfaces import MANYTOONE
from sqlalchemy.sql.expression import desc
from sqlalchemy import exc

from wtforms.ext.sqlalchemy.orm import model_form, ModelConverter
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from flask import request, render_template, url_for, redirect, flash

from flaskext import wtf

from flask.ext.adminex import BaseView, expose


class AdminModelConverter(ModelConverter):
    def __init__(self, session):
        super(AdminModelConverter, self).__init__()

        self.session = session

    def convert(self, model, mapper, prop, field_args):
        if isinstance(prop, RelationshipProperty):
            kwargs = {
                'validators': [],
                'filters': [],
                'default': None
            }

            if field_args:
                kwargs.update(field_args)

            if prop.direction is MANYTOONE:
                def query_factory():
                    return self.session.query(prop.argument)

                return QuerySelectField(query_factory=query_factory, **kwargs)
        else:
            # Ignore pk/fk
            if isinstance(prop, ColumnProperty):
                column = prop.columns[0]

                if column.foreign_keys or column.primary_key:
                    return None

            return super(AdminModelConverter, self).convert(model, mapper, prop, field_args)


class ModelView(BaseView):
    # Permissions
    can_create = True
    can_edit = True
    can_delete = True

    # Templates
    list_template = 'admin/model/list.html'
    edit_template = 'admin/model/edit.html'
    create_template = 'admin/model/edit.html'

    # Various settings
    page_size = 3

    def __init__(self, model, session, name=None, category=None, endpoint=None, url=None):
        # If name not provided, it is modelname
        if name is None:
            name = '%s' % self._prettify_name(model.__name__)

        # If endpoint not provided, it is modelname + 'view'
        if endpoint is None:
            endpoint = ('%sview' % model.__name__).lower()

        super(ModelView, self).__init__(name, category, endpoint, url)

        self.session = session
        self.model = model

        # Scaffolding
        self.list_columns = self.get_list_columns()

        self.create_form = self.scaffold_create_form()
        self.edit_form = self.scaffold_edit_form()

    # Public API
    def get_list_columns(self):
        mapper = self.model._sa_class_manager.mapper

        columns = []

        for p in mapper.iterate_properties:
            if isinstance(p, RelationshipProperty):
                if p.direction is MANYTOONE:
                    columns.append(p.key)
            elif isinstance(p, ColumnProperty):
                # TODO: Check for multiple columns
                column = p.columns[0]

                if column.foreign_keys or column.primary_key:
                    continue

                columns.append(p.key)

        return [(c, self.prettify_name(c)) for c in columns]

    def scaffold_form(self):
        return model_form(self.model, wtf.Form, None, converter=AdminModelConverter(self.session))

    def scaffold_create_form(self):
        return self.scaffold_form()

    def scaffold_edit_form(self):
        return self.scaffold_form()

    # Database-related API
    def get_query(self):
        return self.session.query(self.model)

    def get_one(self, id):
        return self.session.query(self.model).get(id)

    # Model handlers
    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            self.session.add(model)
            self.session.commit()
            return True
        except Exception, ex:
            # TODO: Error logging
            flash('Failed to create model. ' + str(ex), 'error')
            return False

    def update_model(self, form, model):
        try:
            form.populate_obj(model)
            self.session.commit()
            return True
        except Exception, ex:
            flash('Failed to update model. ' + str(ex), 'error')
            return False

    def delete_model(self, model):
        self.session.delete(model)
        self.session.commit()

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
        data = self.get_query()

        page, sort, sort_desc = self._get_extra_args()

        # Sorting
        if sort is not None:
            # Validate first
            if sort >= 0 and sort < len(self.list_columns):
                if sort_desc:
                    data = data.order_by(desc(self.list_columns[sort][0]))
                else:
                    data = data.order_by(self.list_columns[sort][0])

        # Paging
        count = data.count()
        num_pages = count / self.page_size
        if count % self.page_size != 0:
            num_pages += 1

        if page is not None:
            if page < 1:
                page = 1

            data = data.offset((page - 1) * self.page_size)

        data = data.limit(self.page_size)

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
