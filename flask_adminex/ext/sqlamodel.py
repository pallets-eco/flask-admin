from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.interfaces import MANYTOONE
from sqlalchemy import exc

from wtforms.ext.sqlalchemy.orm import model_form, ModelConverter
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from flask import request, render_template, url_for, redirect

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

        return columns

    def scaffold_form(self):
        return model_form(self.model, wtf.Form, None, converter=AdminModelConverter(self.session))

    def scaffold_create_form(self):
        return self.scaffold_form()

    def scaffold_edit_form(self):
        return self.scaffold_form()

    # Database-related API
    def get_list(self):
        return self.session.query(self.model)

    def get_one(self, id):
        return self.session.query(self.model).get(id)

    # Model handlers
    def create_model(self, form):
        # TODO: Error handling
        model = self.model()
        form.populate_obj(model)
        self.session.add(model)
        self.session.commit()

    def update_model(self, form, model):
        form.populate_obj(model)
        self.session.commit()

    def delete_model(self, model):
        self.session.delete(model)
        self.session.commit()

    # Views
    @expose('/')
    def index_view(self):
        data = self.get_list()
        return render_template(self.list_template, view=self, data=data)

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        if not self.can_create:
            return redirect(url_for('.index_view'))

        form = self.create_form(request.form)

        if form.validate_on_submit():
            self.create_model(form)
            return redirect(url_for('.index_view'))

        return render_template(self.create_template, view=self, form=form)

    @expose('/edit/<int:id>/', methods=('GET', 'POST'))
    def edit_view(self, id):
        if not self.can_edit:
            return redirect(url_for('.index_view'))

        model = self.get_one(id)

        if model is None:
            return redirect(url_for('.index_view'))

        form = self.edit_form(request.form, model)

        if form.validate_on_submit():
            self.update_model(form, model)
            return redirect(url_for('.index_view'))

        return render_template(self.edit_template, view=self, form=form)

    @expose('/delete/<int:id>/')
    def delete_view(self, id):
        # TODO: Use post
        if not self.can_delete:
            return redirect(url_for('.index_view'))

        model = self.get_one(id)

        if model:
            self.delete_model(model)

        return redirect(url_for('.index_view'))
