from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.interfaces import MANYTOONE
from sqlalchemy.sql.expression import desc

from wtforms.ext.sqlalchemy.orm import model_form, ModelConverter
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from flask import flash

from flaskext import wtf

from flask.ext.adminex.model import BaseModelView


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


class ModelView(BaseModelView):
    def __init__(self, model, session, name=None, category=None, endpoint=None, url=None):
        self.session = session

        super(ModelView, self).__init__(model, name, category, endpoint, url)

    # Public API
    def get_list_columns(self):
        columns = self.list_columns

        if columns is None:
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
        return model_form(self.model, wtf.Form, self.form_columns, converter=AdminModelConverter(self.session))

    # Database-related API
    def get_list(self, page, sort_column, sort_desc):
        query = self.session.query(self.model)

        count = query.count()

        if sort_column is not None:
            # Validate first
            if sort_column >= 0 and sort_column < len(self.list_columns):
                if sort_desc:
                    query = query.order_by(desc(self.list_columns[sort_column][0]))
                else:
                    query = query.order_by(self.list_columns[sort_column][0])

        if page is not None:
            if page < 1:
                page = 1

            query = query.offset((page - 1) * self.page_size)

        query = query.limit(self.page_size)

        return count, query.all()

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
