import logging

from flask import flash

from flask_admin._compat import string_types
from flask_admin.babel import gettext, ngettext, lazy_gettext
from flask_admin.model import BaseModelView
from flask_admin.model.form import create_editable_list_form

from peewee import JOIN, PrimaryKeyField, ForeignKeyField, Field, CharField, TextField

from flask_admin.actions import action
from flask_admin.contrib.peewee import filters

from .form import get_form, CustomModelConverter, InlineModelConverter, save_inline
from .tools import get_meta_fields, get_primary_key, parse_like_term
from .ajax import create_ajax_loader

# Set up logger
log = logging.getLogger("flask-admin.peewee")


class ModelView(BaseModelView):
    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of
        :class:`flask_admin.contrib.peewee.filters.BasePeeweeFilter` classes.

        Filters will be grouped by name when displayed in the drop-down.

        For example::

            class MyModelView(BaseModelView):
                column_filters = ('user', 'email')

        or::

            from flask_admin.contrib.peewee.filters import BooleanEqualFilter

            class MyModelView(BaseModelView):
                column_filters = (BooleanEqualFilter(column=User.name, name='Name'),)

        or::

            from flask_admin.contrib.peewee.filters import BasePeeweeFilter

            class FilterLastNameBrown(BasePeeweeFilter):
                def apply(self, query, value):
                    if value == '1':
                        return query.filter(self.column == "Brown")
                    else:
                        return query.filter(self.column != "Brown")

                def operation(self):
                    return 'is Brown'

            class MyModelView(BaseModelView):
                column_filters = [
                    FilterLastNameBrown(
                        column=User.last_name, name='Last Name',
                        options=(('1', 'Yes'), ('0', 'No'))
                    )
                ]
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

            from flask_admin.model.form import InlineFormAdmin

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
                 category=None, endpoint=None, url=None, static_folder=None,
                 menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
        self._search_fields = []

        super(ModelView, self).__init__(model, name, category, endpoint, url, static_folder,
                                        menu_class_name=menu_class_name,
                                        menu_icon_type=menu_icon_type,
                                        menu_icon_value=menu_icon_value)

        self._primary_key = self.scaffold_pk()

    def _get_model_fields(self, model=None):
        if model is None:
            model = self.model

        return (
            (field.name, field)
            for field in get_meta_fields(model))

    def scaffold_pk(self):
        return get_primary_key(self.model)

    def get_pk_value(self, model):
        if self.model._meta.composite_key:
            return tuple([
                model._data[field_name]
                for field_name in self.model._meta.primary_key.field_names])
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

                # Check type
                if not isinstance(p, (CharField, TextField)):
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
        model_class = None
        try:
            model_class = attr.model_class
        except AttributeError:
            model_class = attr.model

        if model_class != self.model:
            visible_name = '%s / %s' % (self.get_column_name(model_class.__name__),
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
                              # Allow child to specify pk, so inline_models
                              # can be ModelViews. But don't auto-generate
                              # pk field if form_columns is empty -- allow
                              # default behaviour in that case.
                              allow_pk=bool(self.form_columns),
                              extra_fields=self.form_extra_fields)

        if self.inline_models:
            form_class = self.scaffold_inline_form_models(form_class)

        return form_class

    def scaffold_list_form(self, widget=None, validators=None):
        """
            Create form for the `index_view` using only the columns from
            `self.column_editable_list`.

            :param widget:
                WTForms widget class. Defaults to `XEditableWidget`.
            :param validators:
                `form_args` dict with only validators
                {'name': {'validators': [required()]}}
        """
        form_class = get_form(self.model, self.model_form_converter(self),
                              base_class=self.form_base_class,
                              only=self.column_editable_list,
                              field_args=validators)

        return create_editable_list_form(self.form_base_class, form_class,
                                         widget)

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
        model_class = None
        try:
            model_class = field.model_class
        except AttributeError:
            model_class = field.model
        if model_class != self.model:
            model_name = model_class.__name__

            if model_name not in joins:
                query = query.join(model_class, JOIN.LEFT_OUTER)
                joins.add(model_name)
        return query

    def _order_by(self, query, joins, order):
        clauses = []
        for sort_field, sort_desc in order:
            query, joins, clause = self._sort_clause(
                query, joins, sort_field, sort_desc)
            clauses.append(clause)
        query = query.order_by(*clauses)
        return query, joins

    def _sort_clause(self, query, joins, sort_field, sort_desc):
        if isinstance(sort_field, string_types):
            field = getattr(self.model, sort_field)
        elif isinstance(sort_field, Field):
            model_class = None
            try:
                model_class = sort_field.model_class
            except AttributeError:
                model_class = sort_field.model
            if model_class != self.model:
                query = self._handle_join(query, sort_field, joins)
            field = sort_field
        clause = field.desc() if sort_desc else field.asc()
        return query, joins, clause

    def get_query(self):
        return self.model.select()

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):
        """
            Return records from the database.

            :param page:
                Page number
            :param sort_column:
                Sort column name
            :param sort_desc:
                Descending or ascending sort
            :param search:
                Search query
            :param filters:
                List of filter tuples
            :param execute:
                Execute query immediately? Default is `True`
            :param page_size:
                Number of results. Defaults to ModelView's page_size. Can be
                overriden to change the page_size limit. Removing the page_size
                limit requires setting page_size to 0 or False.
        """

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
            for flt, flt_name, value in filters:
                f = self._filters[flt]

                query = self._handle_join(query, f.column, joins)
                query = f.apply(query, f.clean(value))

        # Get count
        count = query.count() if not self.simple_list_pager else None

        # Apply sorting
        if sort_column is not None:
            sort_field = self._sortable_columns[sort_column]
            order = [(sort_field, sort_desc)]
            query, joins = self._order_by(query, joins, order)
        else:
            order = self._get_default_order()
            if order:
                query, joins = self._order_by(query, joins, order)

        # Pagination
        if page_size is None:
            page_size = self.page_size

        if page_size:
            query = query.limit(page_size)

        if page and page_size:
            query = query.offset(page * page_size)

        if execute:
            query = list(query.execute())

        return count, query

    def get_one(self, id):
        if self.model._meta.composite_key:
            return self.model.get(**dict(zip(self.model._meta.primary_key.field_names, id)))
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
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to create record.')

            return False
        else:
            self.after_model_change(form, model, True)

        return model

    def update_model(self, form, model):
        try:
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            model.save()

            # For peewee have to save inline forms after model was saved
            save_inline(form, model)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to update record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to update record.')

            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            model.delete_instance(recursive=True)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to delete record.')

            return False
        else:
            self.after_model_delete(model)

        return True

    # Default model actions
    def is_action_allowed(self, name):
        # Check delete action permission
        if name == 'delete' and not self.can_delete:
            return False

        return super(ModelView, self).is_action_allowed(name)

    @action('delete',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete selected records?'))
    def action_delete(self, ids):
        try:
            model_pk = getattr(self.model, self._primary_key)

            if self.fast_mass_delete:
                count = self.model.delete().where(model_pk << ids).execute()
            else:
                count = 0

                query = self.model.select().filter(model_pk << ids)

                for m in query:
                    self.on_model_delete(m)
                    m.delete_instance(recursive=True)
                    count += 1

            flash(ngettext('Record was successfully deleted.',
                           '%(count)s records were successfully deleted.',
                           count,
                           count=count), 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete records. %(error)s', error=str(ex)), 'error')
