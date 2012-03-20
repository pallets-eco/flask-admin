from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.interfaces import MANYTOONE
from sqlalchemy.orm.attributes import InstrumentedAttribute
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

            return super(AdminModelConverter, self).convert(model, mapper,
                                                            prop, field_args)


class ModelView(BaseModelView):
    def __init__(self, model, session,
                 name=None, category=None, endpoint=None, url=None):
        self.session = session

        super(ModelView, self).__init__(model, name, category, endpoint, url)

    # Public API
    def scaffold_list_columns(self):
        columns = []

        mapper = self.model._sa_class_manager.mapper

        for p in mapper.iterate_properties:
            if isinstance(p, RelationshipProperty):
                if p.direction is MANYTOONE:
                    columns.append(p.key)
            elif isinstance(p, ColumnProperty):
                # TODO: Check for multiple columns
                column = p.columns[0]

                if column.foreign_keys or column.primary_key:
                    continue

                columns.append((p.key, self.prettify_name(p.key)))

        return columns

    def scaffold_sortable_columns(self):
        columns = dict()

        mapper = self.model._sa_class_manager.mapper

        for p in mapper.iterate_properties:
            if isinstance(p, RelationshipProperty):
                if p.direction is MANYTOONE:
                    # TODO: Detect PK
                    columns[p.key] = '%s.id' % p.target.name
            elif isinstance(p, ColumnProperty):
                # TODO: Check for multiple columns
                column = p.columns[0]

                if column.foreign_keys or column.primary_key:
                    continue

                columns[p.key] = p.key

        return columns

    def scaffold_form(self):
        return model_form(self.model,
                          wtf.Form,
                          self.form_columns,
                          converter=AdminModelConverter(self.session))

    # Database-related API
    def get_list(self, page, sort_column, sort_desc):
        query = self.session.query(self.model)

        count = query.count()

        # Sorting
        column = self._get_column_by_idx(sort_column)
        if column is not None:
            name = column[0]

            if name in self._sortable_columns:
                sort_field = self._sortable_columns[name]

                # Try to handle it as a string
                if isinstance(sort_field, basestring):
                    # Create automatic join if string contains dot
                    if '.' in sort_field:
                        parts = sort_field.split('.', 1)
                        query = query.join(parts[0])
                elif isinstance(sort_field, InstrumentedAttribute):
                    query = query.join(sort_field.parententity)
                else:
                    sort_field = None

                if sort_field is not None:
                    if sort_desc:
                        query = query.order_by(desc(sort_field))
                    else:
                        query = query.order_by(sort_field)

        # Pagination
        if page is not None:
            query = query.offset(page * self.page_size)

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
