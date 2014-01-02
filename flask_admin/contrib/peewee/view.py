import logging

from flask import flash

from flask.ext.admin._compat import string_types
from flask.ext.admin.babel import gettext, ngettext, lazy_gettext
from flask.ext.admin.model import BaseModelView

from peewee import PrimaryKeyField, ForeignKeyField, Field, CharField, TextField

from flask.ext.admin.actions import action
from flask.ext.admin.contrib.peewee import filters

from .form import get_form, CustomModelConverter, InlineModelConverter, save_inline
from .tools import get_primary_key, parse_like_term
from .ajax import create_ajax_loader

# Set up logger
log = logging.getLogger("flask-admin.peewee")


class ModelView(BaseModelView):
    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of
        :class:`flask.ext.admin.contrib.peewee.filters.BaseFilter` classes.

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

    inline_model_form_converter = InlineModelConverter
    """
        Inline model conversion class. If you need some kind of post-processing for inline
        forms, you can customize behavior by doing something like this::

            class MyInlineModelConverter(AdminModelConverter):
                def post_process(self, form_class, info):
                    form_class.value = TextField('value')
                    return form_class

            class MyAdminView(ModelView):
                inline_model_form_converter = MyInlineModelConverter
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
        giving Peewee chance to manually cleanup any dependencies (many-to-many
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

        You can customize generated field name by:

        1. Using `form_name` property as option:

            class MyModelView(ModelView):
                inline_models = ((Post, dict(form_label='Hello')))

        2. Using field's related_name:

            class Model1(Base):
                # ...
                pass

            class Model2(Base):
                # ...
                model1 = ForeignKeyField(related_name="model_twos")

            class MyModel1View(Base):
                inline_models = (Model2,)
                column_labels = {'model_ones': 'Hello'}
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
            # Verify type
            field_class = type(f)

            if field_class == ForeignKeyField:
                columns.append(n)
            elif self.column_display_pk or field_class != PrimaryKeyField:
                columns.append(n)

        return columns

    def scaffold_sortable_columns(self):
        columns = dict()

        for n, f in self._get_model_fields():
            if self.column_display_pk or type(f) != PrimaryKeyField:
                columns[n] = f

        return columns

    def init_search(self):
        if self.column_searchable_list:
            for p in self.column_searchable_list:
                if isinstance(p, string_types):
                    p = getattr(self.model, p)

                field_type = type(p)

                # Check type
                if (field_type != CharField and field_type != TextField):
                        raise Exception('Can only search on text columns. ' +
                                        'Failed to setup search for "%s"' % p)

                self._search_fields.append(p)

        return bool(self._search_fields)

    def scaffold_filters(self, name):
        if isinstance(name, string_types):
            attr = getattr(self.model, name, None)
        else:
            attr = name

        if attr is None:
            raise Exception('Failed to find field for filter: %s' % name)

        # Check if field is in different model
        if attr.model_class != self.model:
            visible_name = '%s / %s' % (self.get_column_name(attr.model_class.__name__),
                                        self.get_column_name(attr.name))
        else:
            if not isinstance(name, string_types):
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
        form_class = get_form(self.model, self.model_form_converter(self),
                              base_class=self.form_base_class,
                              only=self.form_columns,
                              exclude=self.form_excluded_columns,
                              field_args=self.form_args,
                              extra_fields=self.form_extra_fields)

        if self.inline_models:
            form_class = self.scaffold_inline_form_models(form_class)

        return form_class

    def scaffold_inline_form_models(self, form_class):
        converter = self.model_form_converter(self)
        inline_converter = self.inline_model_form_converter(self)

        for m in self.inline_models:
            form_class = inline_converter.contribute(converter,
                                                     self.model,
                                                     form_class,
                                                     m)

        return form_class

    # AJAX foreignkey support
    def _create_ajax_loader(self, name, options):
        return create_ajax_loader(self.model, name, name, options)

    def _handle_join(self, query, field, joins):
        if field.model_class != self.model:
            model_name = field.model_class.__name__

            if model_name not in joins:
                query = query.join(field.model_class)
                joins.add(model_name)

        return query

    def _order_by(self, query, joins, sort_field, sort_desc):
        if isinstance(sort_field, string_types):
            field = getattr(self.model, sort_field)
            query = query.order_by(field.desc() if sort_desc else field.asc())
        elif isinstance(sort_field, Field):
            if sort_field.model_class != self.model:
                query = self._handle_join(query, sort_field, joins)

            query = query.order_by(sort_field.desc() if sort_desc else sort_field.asc())

        return query, joins

    def get_query(self):
        return self.model.select()

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True):
        query = self.get_query()

        joins = set()

        # Search
        if self._search_supported and search:
            values = search.split(' ')

            for value in values:
                if not value:
                    continue

                term = parse_like_term(value)

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
                query = f.apply(query, value)

        # Get count
        count = query.count()

        # Apply sorting
        if sort_column is not None:
            sort_field = self._sortable_columns[sort_column]

            query, joins = self._order_by(query, joins, sort_field, sort_desc)
        else:
            order = self._get_default_order()

            if order:
                query, joins = self._order_by(query, joins, order[0], order[1])

        # Pagination
        if page is not None:
            query = query.offset(page * self.page_size)

        query = query.limit(self.page_size)

        if execute:
            query = list(query.execute())

        return count, query

    def get_one(self, id):
        return self.model.get(**{self._primary_key: id})

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            self._on_model_change(form, model, True)
            model.save()

            # For peewee have to save inline forms after model was saved
            save_inline(form, model)
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to create model. %(error)s', error=str(ex)), 'error')
            log.exception('Failed to create model')
            return False
        else:
            self.after_model_change(form, model, True)

        return True

    def update_model(self, form, model):
        try:
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            model.save()

            # For peewee have to save inline forms after model was saved
            save_inline(form, model)
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to update model. %(error)s', error=str(ex)), 'error')
            log.exception('Failed to update model')
            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            model.delete_instance(recursive=True)
            return True
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to delete model. %(error)s', error=str(ex)), 'error')
            log.exception('Failed to delete model')
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
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to delete models. %(error)s', error=str(ex)), 'error')
