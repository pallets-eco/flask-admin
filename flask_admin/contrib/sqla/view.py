import logging

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import desc
from sqlalchemy import Column, Boolean, func, or_

from flask import flash

from flask.ext.admin._compat import string_types
from flask.ext.admin.babel import gettext, ngettext, lazy_gettext
from flask.ext.admin.model import BaseModelView
from flask.ext.admin.actions import action
from flask.ext.admin._backwards import ObsoleteAttr

from flask.ext.admin.contrib.sqla import form, filters, tools
from .typefmt import DEFAULT_FORMATTERS
from .tools import is_inherited_primary_key, get_column_for_current_model, get_query_for_ids
from .ajax import create_ajax_loader


# Set up logger
log = logging.getLogger("flask-admin.sqla")


class ModelView(BaseModelView):
    """
        SQLAlchemy model view

        Usage sample::

            admin = Admin()
            admin.add_view(ModelView(User, db.session))
    """

    column_auto_select_related = ObsoleteAttr('column_auto_select_related',
                                              'auto_select_related',
                                              True)
    """
        Enable automatic detection of displayed foreign keys in this view
        and perform automatic joined loading for related models to improve
        query performance.

        Please note that detection is not recursive: if `__unicode__` method
        of related model uses another model to generate string representation, it
        will still make separate database call.
    """

    column_select_related_list = ObsoleteAttr('column_select_related',
                                             'list_select_related',
                                              None)
    """
        List of parameters for SQLAlchemy `subqueryload`. Overrides `column_auto_select_related`
        property.

        For example::

            class PostAdmin(ModelView):
                column_select_related_list = ('user', 'city')

        You can also use properties::

            class PostAdmin(ModelView):
                column_select_related_list = (Post.user, Post.city)

        Please refer to the `subqueryload` on list of possible values.
    """

    column_display_all_relations = ObsoleteAttr('column_display_all_relations',
                                                'list_display_all_relations',
                                                False)
    """
        Controls if list view should display all relations, not only many-to-one.
    """

    column_searchable_list = ObsoleteAttr('column_searchable_list',
                                          'searchable_columns',
                                          None)
    """
        Collection of the searchable columns. Only text-based columns
        are searchable (`String`, `Unicode`, `Text`, `UnicodeText`).

        Example::

            class MyModelView(ModelView):
                column_searchable_list = ('name', 'email')

        You can also pass columns::

            class MyModelView(ModelView):
                column_searchable_list = (User.name, User.email)

        The following search rules apply:

        - If you enter *ZZZ* in the UI search field, it will generate *ILIKE '%ZZZ%'*
          statement against searchable columns.

        - If you enter multiple words, each word will be searched separately, but
          only rows that contain all words will be displayed. For example, searching
          for 'abc def' will find all rows that contain 'abc' and 'def' in one or
          more columns.

        - If you prefix your search term with ^, it will find all rows
          that start with ^. So, if you entered *^ZZZ*, *ILIKE 'ZZZ%'* will be used.

        - If you prefix your search term with =, it will perform an exact match.
          For example, if you entered *=ZZZ*, the statement *ILIKE 'ZZZ'* will be used.
    """

    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of :class:`flask.ext.admin.contrib.sqla.filters.BaseFilter` classes.

        For example::

            class MyModelView(BaseModelView):
                column_filters = ('user', 'email')

        or::

            class MyModelView(BaseModelView):
                column_filters = (BooleanEqualFilter(User.name, 'Name'))
    """

    model_form_converter = form.AdminModelConverter
    """
        Model form conversion class. Use this to implement custom field conversion logic.

        For example::

            class MyModelConverter(AdminModelConverter):
                pass


            class MyAdminView(ModelView):
                model_form_converter = MyModelConverter
    """

    inline_model_form_converter = form.InlineModelConverter
    """
        Inline model conversion class. If you need some kind of post-processing for inline
        forms, you can customize behavior by doing something like this::

            class MyInlineModelConverter(AdminModelConverter):
                def post_process(self, form_class, info):
                    form_class.value = wtf.TextField('value')
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
        If set to `False` and user deletes more than one model using built in action,
        all models will be read from the database and then deleted one by one
        giving SQLAlchemy a chance to manually cleanup any dependencies (many-to-many
        relationships, etc).

        If set to `True`, will run a `DELETE` statement which is somewhat faster,
        but may leave corrupted data if you forget to configure `DELETE
        CASCADE` for your model.
    """

    inline_models = None
    """
        Inline related-model editing for models with parent-child relations.

        Accepts enumerable with one of the following possible values:

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

        You can customize the generated field name by:

        1. Using the `form_name` property as a key to the options dictionary:

            class MyModelView(ModelView):
                inline_models = ((Post, dict(form_label='Hello')))

        2. Using forward relation name and `column_labels` property:

            class Model1(Base):
                pass

            class Model2(Base):
                # ...
                model1 = relation(Model1, backref='models')

            class MyModel1View(Base):
                inline_models = (Model2,)
                column_labels = {'models': 'Hello'}
    """

    column_type_formatters = DEFAULT_FORMATTERS

    form_choices = None
    """
        Map choices to form fields

        Example::

            class MyModelView(BaseModelView):
                form_choices = {'my_form_field': [
                    ('db_value', 'display_value'),
                ]
    """

    form_optional_types = (Boolean,)
    """
        List of field types that should be optional if column is not nullable.

        Example::

            class MyModelView(BaseModelView):
                form_optional_types = (Boolean, Unicode)
    """

    def __init__(self, model, session,
                 name=None, category=None, endpoint=None, url=None):
        """
            Constructor.

            :param model:
                Model class
            :param session:
                SQLAlchemy session
            :param name:
                View name. If not set, defaults to the model name
            :param category:
                Category name
            :param endpoint:
                Endpoint name. If not set, defaults to the model name
            :param url:
                Base URL. If not set, defaults to '/admin/' + endpoint
        """
        self.session = session

        self._search_fields = None
        self._search_joins = dict()

        self._filter_joins = dict()

        if self.form_choices is None:
            self.form_choices = {}

        super(ModelView, self).__init__(model, name, category, endpoint, url)

        # Primary key
        self._primary_key = self.scaffold_pk()

        if self._primary_key is None:
            raise Exception('Model %s does not have primary key.' % self.model.__name__)

        # Configuration
        if not self.column_select_related_list:
            self._auto_joins = self.scaffold_auto_joins()
        else:
            self._auto_joins = self.column_select_related_list

    # Internal API
    def _get_model_iterator(self, model=None):
        """
            Return property iterator for the model
        """
        if model is None:
            model = self.model

        return model._sa_class_manager.mapper.iterate_properties

    # Scaffolding
    def scaffold_pk(self):
        """
            Return the primary key name from a model
            PK can be a single value or a tuple if multiple PKs exist
        """
        return tools.get_primary_key(self.model)

    def get_pk_value(self, model):
        """
            Return the PK value from a model object.
            PK can be a single value or a tuple if multiple PKs exist
        """
        try:
            return getattr(model, self._primary_key)
        except TypeError:
            v = []
            for attr in self._primary_key:
                v.append(getattr(model, attr))
            return tuple(v)

    def scaffold_list_columns(self):
        """
            Return a list of columns from the model.
        """
        columns = []

        for p in self._get_model_iterator():
            # Verify type
            if hasattr(p, 'direction'):
                if self.column_display_all_relations or p.direction.name == 'MANYTOONE':
                    columns.append(p.key)
            elif hasattr(p, 'columns'):
                column_inherited_primary_key = False

                if len(p.columns) != 1:
                    if is_inherited_primary_key(p):
                        column = get_column_for_current_model(p)
                    else:
                        raise TypeError('Can not convert multiple-column properties (%s.%s)' % (self.model, p.key))
                else:
                    # Grab column
                    column = p.columns[0]

                # An inherited primary key has a foreign key as well
                if column.foreign_keys and not is_inherited_primary_key(p):
                    continue

                if not self.column_display_pk and column.primary_key:
                    continue

                columns.append(p.key)

        return columns

    def scaffold_sortable_columns(self):
        """
            Return a dictionary of sortable columns.
            Key is column name, value is sort column/field.
        """
        columns = dict()

        for p in self._get_model_iterator():
            if hasattr(p, 'columns'):
                # Sanity check
                if len(p.columns) > 1:
                    # Multi-column properties are not supported
                    continue

                column = p.columns[0]

                # Can't sort on primary or foreign keys by default
                if column.foreign_keys:
                    continue

                if not self.column_display_pk and column.primary_key:
                    continue

                columns[p.key] = column

        return columns

    def _get_columns_for_field(self, field):
        if isinstance(field, string_types):
            attr = getattr(self.model, field, None)

            if field is None:
                raise Exception('Field %s was not found.' % field)
        else:
            attr = field

        if (not attr or
            not hasattr(attr, 'property') or
            not hasattr(attr.property, 'columns') or
            not attr.property.columns):
                raise Exception('Invalid field %s: does not contains any columns.' % field)

        return attr.property.columns

    def _need_join(self, table):
        return table not in self.model._sa_class_manager.mapper.tables

    def init_search(self):
        """
            Initialize search. Returns `True` if search is supported for this
            view.

            For SQLAlchemy, this will initialize internal fields: list of
            column objects used for filtering, etc.
        """
        if self.column_searchable_list:
            self._search_fields = []
            self._search_joins = dict()

            for p in self.column_searchable_list:
                for column in self._get_columns_for_field(p):
                    column_type = type(column.type).__name__

                    if not self.is_text_column_type(column_type):
                        raise Exception('Can only search on text columns. ' +
                                        'Failed to setup search for "%s"' % p)

                    self._search_fields.append(column)

                    # If it belongs to different table - add a join
                    if self._need_join(column.table):
                        self._search_joins[column.table.name] = column.table

        return bool(self.column_searchable_list)

    def is_text_column_type(self, name):
        """
            Verify if the provided column type is text-based.

            :returns:
                ``True`` for ``String``, ``Unicode``, ``Text``, ``UnicodeText``
        """
        if name:
            name = name.lower()

        return name in ('string', 'unicode', 'text', 'unicodetext')

    def scaffold_filters(self, name):
        """
            Return list of enabled filters
        """

        join_tables = []
        if isinstance(name, string_types):
            model = self.model

            for attribute in name.split('.'):
                value = getattr(model, attribute)
                if (hasattr(value, 'property') and
                    hasattr(value.property, 'direction')):
                    model = value.property.mapper.class_
                    table = model.__table__

                    if self._need_join(table):
                        join_tables.append(table)

                attr = value
        else:
            attr = name

        if attr is None:
            raise Exception('Failed to find field for filter: %s' % name)

        # Figure out filters for related column
        if hasattr(attr, 'property') and hasattr(attr.property, 'direction'):
            filters = []

            for p in self._get_model_iterator(attr.property.mapper.class_):
                if hasattr(p, 'columns'):
                    # TODO: Check for multiple columns
                    column = p.columns[0]

                    if column.foreign_keys or column.primary_key:
                        continue

                    visible_name = '%s / %s' % (self.get_column_name(attr.prop.table.name),
                                                self.get_column_name(p.key))

                    type_name = type(column.type).__name__
                    flt = self.filter_converter.convert(type_name,
                                                        column,
                                                        visible_name)

                    if flt:
                        table = column.table

                        if join_tables:
                            self._filter_joins[table.name] = join_tables
                        elif self._need_join(table.name):
                            self._filter_joins[table.name] = [table.name]
                        filters.extend(flt)

            return filters
        else:
            columns = self._get_columns_for_field(attr)

            if len(columns) > 1:
                raise Exception('Can not filter more than on one column for %s' % name)

            column = columns[0]

            if self._need_join(column.table) and name not in self.column_labels:
                visible_name = '%s / %s' % (
                    self.get_column_name(column.table.name),
                    self.get_column_name(column.name)
                )
            else:
                if not isinstance(name, string_types):
                    visible_name = self.get_column_name(name.property.key)
                else:
                    visible_name = self.get_column_name(name)

            type_name = type(column.type).__name__

            if join_tables:
                self._filter_joins[column.table.name] = join_tables

            flt = self.filter_converter.convert(
                type_name,
                column,
                visible_name,
                options=self.column_choices.get(name),
            )

            if flt and not join_tables and self._need_join(column.table):
                self._filter_joins[column.table.name] = [column.table]

            return flt

    def is_valid_filter(self, filter):
        """
            Verify that the provided filter object is derived from the
            SQLAlchemy-compatible filter class.

            :param filter:
                Filter object to verify.
        """
        return isinstance(filter, filters.BaseSQLAFilter)

    def scaffold_form(self):
        """
            Create form from the model.
        """
        converter = self.model_form_converter(self.session, self)
        form_class = form.get_form(self.model, converter,
                                   base_class=self.form_base_class,
                                   only=self.form_columns,
                                   exclude=self.form_excluded_columns,
                                   field_args=self.form_args,
                                   extra_fields=self.form_extra_fields)

        if self.inline_models:
            form_class = self.scaffold_inline_form_models(form_class)

        return form_class

    def scaffold_inline_form_models(self, form_class):
        """
            Contribute inline models to the form

            :param form_class:
                Form class
        """
        inline_converter = self.inline_model_form_converter(self.session,
                                                            self,
                                                            self.model_form_converter)

        for m in self.inline_models:
            form_class = inline_converter.contribute(self.model, form_class, m)

        return form_class

    def scaffold_auto_joins(self):
        """
            Return a list of joined tables by going through the
            displayed columns.
        """
        if not self.column_auto_select_related:
            return []

        relations = set()

        for p in self._get_model_iterator():
            if hasattr(p, 'direction'):
                # Check if it is pointing to same model
                if p.mapper.class_ == self.model:
                    continue

                if p.direction.name in ['MANYTOONE', 'MANYTOMANY']:
                    relations.add(p.key)

        joined = []

        for prop, name in self._list_columns:
            if prop in relations:
                joined.append(getattr(self.model, prop))

        return joined

    # AJAX foreignkey support
    def _create_ajax_loader(self, name, options):
        return create_ajax_loader(self.model, self.session, name, name, options)

    # Database-related API
    def get_query(self):
        """
            Return a query for the model type.

            If you override this method, don't forget to override `get_count_query` as well.
        """
        return self.session.query(self.model)

    def get_count_query(self):
        """
            Return a the count query for the model type
        """
        return self.session.query(func.count('*')).select_from(self.model)

    def _order_by(self, query, joins, sort_field, sort_desc):
        """
            Apply order_by to the query

            :param query:
                Query
            :param joins:
                Joins set
            :param sort_field:
                Sort field
            :param sort_desc:
                Ascending or descending
        """
        # TODO: Preprocessing for joins
        # Try to handle it as a string
        if isinstance(sort_field, string_types):
            # Create automatic join against a table if column name
            # contains dot.
            if '.' in sort_field:
                parts = sort_field.split('.', 1)

                if parts[0] not in joins:
                    query = query.join(parts[0])
                    joins.add(parts[0])
        elif isinstance(sort_field, InstrumentedAttribute):
            # SQLAlchemy 0.8+ uses 'parent' as a name
            mapper = getattr(sort_field, 'parent', None)
            if mapper is None:
                # SQLAlchemy 0.7.x uses parententity
                mapper = getattr(sort_field, 'parententity', None)

            if mapper is not None:
                table = mapper.tables[0]

                if self._need_join(table) and table.name not in joins:
                    query = query.outerjoin(table)
                    joins.add(table.name)
        elif isinstance(sort_field, Column):
            pass
        else:
            raise TypeError('Wrong argument type')

        if sort_field is not None:
            if sort_desc:
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(sort_field)

        return query, joins

    def _get_default_order(self):
        order = super(ModelView, self)._get_default_order()

        if order is not None:
            field, direction = order

            if isinstance(field, string_types):
                field = getattr(self.model, field)

            return field, direction

        return None

    def get_list(self, page, sort_column, sort_desc, search, filters, execute=True):
        """
            Return models from the database.

            :param page:
                Page number
            :param sort_column:
                Sort column name
            :param sort_desc:
                Descending or ascending sort
            :param search:
                Search query
            :param execute:
                Execute query immediately? Default is `True`
            :param filters:
                List of filter tuples
        """

        # Will contain names of joined tables to avoid duplicate joins
        joins = set()

        query = self.get_query()
        count_query = self.get_count_query()

        # Apply search criteria
        if self._search_supported and search:
            # Apply search-related joins
            if self._search_joins:
                for jn in self._search_joins.values():
                    query = query.join(jn)
                    count_query = count_query.join(jn)

                joins = set(self._search_joins.keys())

            # Apply terms
            terms = search.split(' ')

            for term in terms:
                if not term:
                    continue

                stmt = tools.parse_like_term(term)
                filter_stmt = [c.ilike(stmt) for c in self._search_fields]
                query = query.filter(or_(*filter_stmt))
                count_query = count_query.filter(or_(*filter_stmt))

        # Apply filters
        if filters and self._filters:
            for idx, value in filters:
                flt = self._filters[idx]

                # Figure out joins
                tbl = flt.column.table.name

                join_tables = self._filter_joins.get(tbl, [])

                for table in join_tables:
                    if table.name not in joins:
                        query = query.join(table)
                        count_query = count_query.join(table)
                        joins.add(table.name)

                # Apply filter
                query = flt.apply(query, value)
                count_query = flt.apply(count_query, value)

        # Calculate number of rows
        count = count_query.scalar()

        # Auto join
        for j in self._auto_joins:
            query = query.options(joinedload(j))

        # Sorting
        if sort_column is not None:
            if sort_column in self._sortable_columns:
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

        # Execute if needed
        if execute:
            query = query.all()

        return count, query

    def get_one(self, id):
        """
            Return a single model by its id.

            :param id:
                Model id
        """
        return self.session.query(self.model).get(id)

    # Model handlers
    def create_model(self, form):
        """
            Create model from form.

            :param form:
                Form instance
        """
        try:
            model = self.model()
            form.populate_obj(model)
            self.session.add(model)
            self._on_model_change(form, model, True)
            self.session.commit()
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to create model. %(error)s', error=str(ex)), 'error')
            log.exception('Failed to create model')
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, True)

        return True

    def update_model(self, form, model):
        """
            Update model from form.

            :param form:
                Form instance
            :param model:
                Model instance
        """
        try:
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            self.session.commit()
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to update model. %(error)s', error=str(ex)), 'error')
            log.exception('Failed to update model')
            self.session.rollback()

            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def delete_model(self, model):
        """
            Delete model.

            :param model:
                Model to delete
        """
        try:
            self.on_model_delete(model)
            self.session.flush()
            self.session.delete(model)
            self.session.commit()
            return True
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to delete model. %(error)s', error=str(ex)), 'error')
            log.exception('Failed to delete model')
            self.session.rollback()
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

            query = get_query_for_ids(self.get_query(), self.model, ids)

            if self.fast_mass_delete:
                count = query.delete(synchronize_session=False)
            else:
                count = 0

                for m in query.all():
                    self.session.delete(m)
                    count += 1

            self.session.commit()

            flash(ngettext('Model was successfully deleted.',
                           '%(count)s models were successfully deleted.',
                           count,
                           count=count))
        except Exception as ex:
            if self._debug:
                raise

            flash(gettext('Failed to delete models. %(error)s', error=str(ex)), 'error')
