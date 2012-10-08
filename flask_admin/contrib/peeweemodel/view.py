from flask import flash

from flask.ext.admin import form
from flask.ext.admin.babel import gettext, ngettext, lazy_gettext
from flask.ext.admin.model import BaseModelView

from peewee import PrimaryKeyField, ForeignKeyField, Field, CharField, TextField
from wtfpeewee.orm import model_form

from flask.ext.admin.actions import action
from flask.ext.admin.contrib.peeweemodel import filters
from .form import CustomModelConverter, contribute_inline, save_inline
from .tools import get_primary_key


class ModelView(BaseModelView):
    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of :class:`flask.ext.admin.contrib.sqlamodel.filters.BaseFilter` classes.

        For example::

            class MyModelView(BaseModelView):
                column_filters = ('user', 'email')

        or::

            class MyModelView(BaseModelView):
                column_filters = (BooleanEqualFilter(User.name, 'Name'))
    """

    model_form_converter = CustomModelConverter
    """
        Model form conversion class. Use this to implement custom field conversion logic.

        For example::

            class MyModelConverter(AdminModelConverter):
                pass


            class MyAdminView(ModelView):
                model_form_converter = MyModelConverter
    """

    filter_converter = filters.FilterConverter()
    """
        Field to filter converter.

        Override this attribute to use non-default converter.
    """

    fast_mass_delete = False
    """
        If set to `False` and user deletes more than one model using actions,
        all models will be read from the database and then deleted one by one
        giving SQLAlchemy chance to manually cleanup any dependencies (many-to-many
        relationships, etc).

        If set to True, will run DELETE statement which is somewhat faster, but
        might leave corrupted data if you forget to configure DELETE CASCADE
        for your model.
    """

    inline_models = None
    """
        Inline related-model editing for models with parent to child relation.

        Accept enumerable with one of the values:

        1. Child model class::

            class MyModelView(ModelView):
                inline_models = (Post,)

        2. Child model class and additional options::

            class MyModelView(ModelView):
                inline_models = [(Post, dict(form_columns=['title']))]

        3. Django-like ``InlineFormAdmin`` class instance::

            class MyInlineModelForm(InlineFormAdmin):
                form_columns = ('title', 'date')

            class MyModelView(ModelView):
                inline_models = (MyInlineModelForm(MyInlineModel),)
    """

    def __init__(self, model, name=None,
                 category=None, endpoint=None, url=None):
        self._search_fields = []

        super(ModelView, self).__init__(model, name, category, endpoint, url)

        self._primary_key = self.scaffold_pk()

    def _get_model_fields(self, model=None):
        if model is None:
            model = self.model

        return model._meta.get_sorted_fields()

    def scaffold_pk(self):
        return get_primary_key(self.model)

    def get_pk_value(self, model):
        return getattr(model, self._primary_key)

    def scaffold_list_columns(self):
        columns = []

        for n, f in self._get_model_fields():
            # Filter by name
            if (self.excluded_list_columns and
                n in self.excluded_list_columns):
                continue

            # Verify type
            field_class = type(f)

            if field_class == ForeignKeyField:
                columns.append(n)
            elif self.list_display_pk or field_class != PrimaryKeyField:
                columns.append(n)

        return columns

    def scaffold_sortable_columns(self):
        columns = dict()

        for n, f in self._get_model_fields():
            if self.list_display_pk or type(f) != PrimaryKeyField:
                columns[n] = f

        return columns

    def init_search(self):
        if self.searchable_columns:
            for p in self.searchable_columns:
                if isinstance(p, basestring):
                    p = getattr(self.model, p)

                field_type = type(p)

                # Check type
                if (field_type != CharField and
                    field_type != TextField):
                        raise Exception('Can only search on text columns. ' +
                                        'Failed to setup search for "%s"' % p)

                self._search_fields.append(p)

        return bool(self._search_fields)

    def scaffold_filters(self, name):
        if isinstance(name, basestring):
            attr = getattr(self.model, name, None)
        else:
            attr = name

        if attr is None:
            raise Exception('Failed to find field for filter: %s' % name)

        # Check if field is in different model
        if attr.model != self.model:
            visible_name = '%s / %s' % (self.get_column_name(attr.model.__name__),
                                        self.get_column_name(attr.name))
        else:
            if not isinstance(name, basestring):
                visible_name = self.get_column_name(attr.name)
            else:
                visible_name = self.get_column_name(name)

        type_name = type(attr).__name__
        flt = self.filter_converter.convert(type_name,
                                            attr,
                                            visible_name)

        return flt

    def is_valid_filter(self, filter):
        return isinstance(filter, filters.BasePeeweeFilter)

    def scaffold_form(self):
        form_class = model_form(self.model,
                        base_class=form.BaseForm,
                        only=self.form_columns,
                        exclude=self.excluded_form_columns,
                        field_args=self.form_args,
                        converter=self.model_form_converter())

        if self.inline_models:
            form_class = contribute_inline(self.model, form_class, self.inline_models)

        return form_class

    def _handle_join(self, query, field, joins):
        if field.model != self.model:
            model_name = field.model.__name__

            if model_name not in joins:
                query = query.join(field.model)
                joins.add(model_name)

        return query

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True):
        query = self.model.select()

        joins = set()

        # Search
        if self._search_supported and search:
            terms = search.split(' ')

            for term in terms:
                if not term:
                    continue

                stmt = None
                for field in self._search_fields:
                    query = self._handle_join(query, field, joins)

                    q = field ** term

                    if stmt is None:
                        stmt = q
                    else:
                        stmt |= q

                query = query.where(stmt)

        # Filters
        if self._filters:
            for flt, value in filters:
                f = self._filters[flt]

                query = self._handle_join(query, f.column, joins)
                query = self._filters[flt].apply(query, value)

        # Get count
        count = query.count()

        # Apply sorting
        if sort_column is not None:
            sort_field = self._sortable_columns[sort_column]

            if isinstance(sort_field, basestring):
                query = query.order_by((sort_field, sort_desc and 'desc' or 'asc'))
            elif isinstance(sort_field, Field):
                if sort_field.model != self.model:
                    query = self._handle_join(query, sort_field, joins)

                    query = query.order_by((sort_field.model, sort_field.name, sort_desc and 'desc' or 'asc'))
                else:
                    query = query.order_by((sort_column, sort_desc and 'desc' or 'asc'))

        # Pagination
        if page is not None:
            query = query.offset(page * self.page_size)

        query = query.limit(self.page_size)

        if execute:
            query = query.execute()

        return count, query

    def get_one(self, id):
        return self.model.get(**{self._primary_key: id})

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            model.save()

            # For peewee have to save inline forms after model was saved
            save_inline(form, model)

            self.on_model_change(form, model)

            return True
        except Exception, ex:
            flash(gettext('Failed to create model. %(error)s', error=str(ex)), 'error')
            return False

    def update_model(self, form, model):
        try:
            form.populate_obj(model)
            model.save()

            # For peewee have to save inline forms after model was saved
            save_inline(form, model)

            self.on_model_change(form, model)

            return True
        except Exception, ex:
            flash(gettext('Failed to update model. %(error)s', error=str(ex)), 'error')
            return False

    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            model.delete_instance(recursive=True)
            return True
        except Exception, ex:
            flash(gettext('Failed to delete model. %(error)s', error=str(ex)), 'error')
            return False

    # Default model actions
    def is_action_allowed(self, name):
        # Check delete action permission
        if name == 'delete' and not self.can_delete:
            return False

        return super(ModelView, self).is_action_allowed(name)

    @action('delete',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete selected models?'))
    def action_delete(self, ids):
        try:
            model_pk = getattr(self.model, self._primary_key)

            if self.fast_mass_delete:
                count = self.model.delete().where(model_pk << ids).execute()
            else:
                count = 0

                query = self.model.select().filter(model_pk << ids)

                for m in query:
                    m.delete_instance(recursive=True)
                    count += 1

            flash(ngettext('Model was successfully deleted.',
                           '%(count)s models were successfully deleted.',
                           count,
                           count=count))
        except Exception, ex:
            flash(gettext('Failed to delete models. %(error)s', error=str(ex)), 'error')
