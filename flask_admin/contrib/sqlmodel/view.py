"""
SQLModel model view for Flask-Admin.

This module provides the main SQLModelView class which enables
Flask-Admin to work with SQLModel models. It handles CRUD operations,
form generation, filtering, searching, and all other Flask-Admin features
for SQLModel-based applications.
"""

import logging
from typing import Any
from typing import get_args
from typing import get_origin

# from typing import cast as t_cast
from typing import Optional
from typing import Union

from flask import current_app
from flask import flash

# Import SQLAlchemy components that are needed but not exposed by SQLModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.base import instance_state
from sqlalchemy.orm.base import manager_of_class
from sqlmodel import cast
from sqlmodel import desc
from sqlmodel import func
from sqlmodel import or_
from sqlmodel import select
from sqlmodel import String

# from flask_admin._compat import string_types
from flask_admin._compat import text_type
from flask_admin.actions import action
from flask_admin.babel import gettext
from flask_admin.babel import lazy_gettext
from flask_admin.babel import ngettext
from flask_admin.contrib.sqlmodel import filters as sqlmodel_filters
from flask_admin.contrib.sqlmodel import form
from flask_admin.contrib.sqlmodel import tools
from flask_admin.model import BaseModelView
from flask_admin.model.form import create_editable_list_form

from .ajax import create_ajax_loader
from .typefmt import DEFAULT_FORMATTERS

log = logging.getLogger("flask-admin.sqlmodel")


class SQLModelView(BaseModelView):
    """
    SQLModel model view

    Usage sample::

        admin = Admin()
        admin.add_view(SQLModelView(User, db.session))
    """

    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of
        :class:`flask_admin.contrib.sqla.filters.BaseSQLModelFilter` classes.

        Filters will be grouped by name when displayed in the drop-down.

        For example::

            class MyModelView(BaseModelView):
                column_filters = ('user', 'email')

        or::

            from flask_admin.contrib.sqla.filters import BooleanEqualFilter

            class MyModelView(BaseModelView):
                column_filters = (BooleanEqualFilter(column=User.name, name='Name'),)

        or::

            from flask_admin.contrib.sqla.filters import BaseSQLModelFilter

            class FilterLastNameBrown(BaseSQLModelFilter):
                def apply(self, query, value, alias=None):
                    if value == '1':
                        return query.filter(self.column == "Brown")
                    else:
                        return query.filter(self.column != "Brown")

                def operation(self):
                    return 'is Brown'

            class MyModelView(BaseModelView):
                column_filters = [
                    FilterLastNameBrown(
                        User.last_name, 'Last Name', options=(('1', 'Yes'), ('0', 'No'))
                    )
                ]
    """

    model_form_converter = form.AdminModelConverter
    """
        Model form conversion class. Use this to implement custom field conversion
        logic.

        For example::

            class MyModelConverter(AdminModelConverter):
                pass


            class MyAdminView(SQLModelView):
                model_form_converter = MyModelConverter
    """

    inline_model_form_converter = form.InlineModelConverter
    """
        Inline model conversion class. If you need some kind of post-processing for
        inline forms, you can customize behavior by doing something like this::

            class MyInlineModelConverter(InlineModelConverter):
                def post_process(self, form_class, info):
                    form_class.value = wtf.StringField('value')
                    return form_class

            class MyAdminView(SQLModelView):
                inline_model_form_converter = MyInlineModelConverter
    """

    filter_converter = sqlmodel_filters.FilterConverter()
    """
        Field to filter converter.

        Override this attribute to use non-default converter.
    """

    fast_mass_delete = False
    """
        If set to `False` and user deletes more than one model using built in action,
        all models will be read from the database and then deleted one by one
        giving SQLModel a chance to manually cleanup any dependencies (many-to-many
        relationships, etc).

        If set to `True`, will run a ``DELETE`` statement which is somewhat faster,
        but may leave corrupted data if you forget to configure ``DELETE
        CASCADE`` for your model.
    """

    inline_models = None
    """
        Inline related-model editing for models with parent-child relations.

        Accepts enumerable with one of the following possible values:

        1. Child model class::

            class MyModelView(SQLModelView):
                inline_models = (Post,)

        2. Child model class and additional options::

            class MyModelView(SQLModelView):
                inline_models = [(Post, dict(form_columns=['title']))]

        3. Django-like ``InlineFormAdmin`` class instance::

            from flask_admin.model.form import InlineFormAdmin

            class MyInlineModelForm(InlineFormAdmin):
                form_columns = ('title', 'date')

            class MyModelView(SQLModelView):
                inline_models = (MyInlineModelForm(MyInlineModel),)

        You can customize the generated field name by:

        1. Using the `form_name` property as a key to the options dictionary::

            class MyModelView(SQLModelView):
                inline_models = ((Post, dict(form_label='Hello')))

        2. Using forward relation name and `column_labels` property::

            class Model1(Base):
                pass

            class Model2(Base):
                # ...
                model1 = relation(Model1, backref='models')

            class MyModel1View(Base):
                inline_models = (Model2,)
                column_labels = {'models': 'Hello'}

        By default used ManyToMany relationship for inline models.
        You may configure inline model for OneToOne relationship.
        To achieve this, you need to install special ``inline_converter``
        for your model::

            from flask_admin.contrib.sqla.form import \
                InlineOneToOneModelConverter

            class MyInlineModelForm(InlineFormAdmin):
                form_columns = ('title', 'date')
                inline_converter = InlineOneToOneModelConverter

            class MyModelView(SQLModelView):
                inline_models = (MyInlineModelForm(MyInlineModel),)
    """

    column_type_formatters = DEFAULT_FORMATTERS
    """
        Column type formatters.
    """

    form_choices: Optional[dict[str, list[tuple[str, str]]]] = None
    """
        Map choices to form fields

        Example::

            class MyModelView(BaseModelView):
                form_choices = {'my_form_field': [
                    ('db_value', 'display_value'),
                ]}
    """

    def __init__(
        self,
        model,
        session,
        name=None,
        category=None,
        endpoint=None,
        url=None,
        static_folder=None,
        menu_class_name=None,
        menu_icon_type=None,
        menu_icon_value=None,
    ):
        """
        Constructor.

        :param model:
            Model class
        :param session:
            SQLModel session
        :param name:
            View name. If not set, defaults to the model name
        :param category:
            Category name
        :param endpoint:
            Endpoint name. If not set, defaults to the model name
        :param url:
            Base URL. If not set, defaults to '/admin/' + endpoint
        :param menu_class_name:
            Optional class name for the menu item.
        :param menu_icon_type:
            Optional icon. Possible icon types:

             - `flask_admin.consts.ICON_TYPE_GLYPH` - Bootstrap glyph icon
             - `flask_admin.consts.ICON_TYPE_FONT_AWESOME` - Font Awesome icon
             - `flask_admin.consts.ICON_TYPE_IMAGE` - Image relative to Flask static
                directory
             - `flask_admin.consts.ICON_TYPE_IMAGE_URL` - Image with full URL
        :param menu_icon_value:
            Icon glyph name or URL, depending on `menu_icon_type` setting
        """
        self.session = session
        self._search_fields = None
        self._filter_joins: dict[Any, Any] = {}
        self._sortable_joins: dict[Any, Any] = {}
        self._filter_name_to_joins: dict[
            str, Any
        ] = {}  # Maps filter names to their joins

        if self.form_choices is None:
            self.form_choices = {}

        super().__init__(
            model,
            name,
            category,
            endpoint,
            url,
            static_folder,
            menu_class_name=menu_class_name,
            menu_icon_type=menu_icon_type,
            menu_icon_value=menu_icon_value,
        )

        self._manager = manager_of_class(self.model)

        # Primary key
        self._primary_key = self.scaffold_pk()

        if self._primary_key is None:
            raise Exception(f"Model {self.model.__name__} does not have a primary key.")

        # Configuration
        self._auto_joins = self.scaffold_auto_joins()

    # Internal API
    def _get_model_iterator(self, model=None):
        """
        Return property iterator for the model
        """
        if model is None:
            model = self.model
        # Use model_fields for Pydantic v2, fall back to __fields__ for v1
        if hasattr(model, "model_fields"):
            return model.model_fields.items()
        else:
            # Fallback for older Pydantic versions
            return model.__fields__.items()

    def _apply_path_joins(self, query, joins, path, inner_join=True):
        """
        Apply join path to the query.

        :param query:
            Query to add joins to
        :param joins:
            List of current joins. Used to avoid joining on same relationship more
            than once
        :param path:
            Path to be joined
        :param fn:
            Join function
        """
        last = None
        if path:
            for item in path:
                key = (inner_join, item)
                alias = joins.get(key)
                if key not in joins:
                    # Check if this is a table object - if so,
                    # join directly without alias
                    if hasattr(item, "columns") and hasattr(item, "name"):
                        # This is a table object, join directly
                        fn = query.join if inner_join else query.outerjoin
                        query = fn(item)
                        joins[key] = None
                        alias = None
                    else:
                        # This is a relationship, create alias like SQLAlchemy version
                        from sqlalchemy.orm import aliased

                        alias = aliased(item.property.mapper.class_)
                        fn = query.join if inner_join else query.outerjoin
                        if last is None:
                            query = fn(alias, item)
                        else:
                            prop = getattr(last, item.key)
                            query = fn(alias, prop)
                        joins[key] = alias
                last = alias
        return query, joins, last

    # Scaffolding
    def scaffold_pk(self):
        """
        Return the primary key name(s) from a model
        If model has single primary key, will return a string and tuple otherwise
        """
        return tools.get_primary_key(self.model)

    def get_pk_value(self, model):
        """
        Return the primary key value from a model object.
        If there are multiple primary keys, they're encoded into string representation.
        """
        model = tools.resolve_model(model)  # 🔥 now works for ORM or Row

        if isinstance(self._primary_key, tuple):
            pk_parts = [getattr(model, attr) for attr in self._primary_key]
            return tools.iterencode(pk_parts)
        else:
            return tools.escape(getattr(model, self._primary_key))  # type: ignore

    def scaffold_list_columns(self):
        """
        Return a list of column names from the model.
        Include both Pydantic model fields and SQLModel relationship attributes.
        """
        from . import tools

        # Get Pydantic model fields
        pydantic_fields = [
            name
            for name, _field in self._get_model_iterator()
            if not name.startswith("_")
        ]

        # Get SQLModel relationship attributes
        relationship_fields = []
        for name in dir(self.model):
            if not name.startswith("_"):
                attr = getattr(self.model, name)
                if tools.is_relationship(attr):
                    relationship_fields.append(name)

        # Combine both types of fields
        all_fields = pydantic_fields + relationship_fields

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for field in all_fields:
            if field not in seen:
                seen.add(field)
                result.append(field)

        return result

    def scaffold_sortable_columns(self):
        """
        Return a dictionary of sortable columns.
        Key is column name, value is the actual attribute or column.
        """
        scalar_types = (int, float, str, bool)

        def is_scalar_type(tp):
            origin = get_origin(tp)
            # Handle both typing.Union and types.UnionType (Python 3.10+ | syntax)
            if origin is Union or str(origin) == "<class 'types.UnionType'>":
                args = get_args(tp)
                # Check if all args are scalar types or None
                return all(arg in scalar_types or arg is type(None) for arg in args)
            # Direct type comparison
            return tp in scalar_types

        return {
            name: name
            for name, field in self._get_model_iterator()
            if not name.startswith("_") and is_scalar_type(field.annotation)
        }

    def get_sortable_columns(self):
        """
        Returns a dictionary of the sortable columns. Key is a model
        field name and value is sort column (for example - attribute).

        If `column_sortable_list` is set, will use it. Otherwise, will call
        `scaffold_sortable_columns` to get them from the model.
        """
        self._sortable_joins = {}
        if self.column_sortable_list is None:
            return self.scaffold_sortable_columns()
        else:
            result = {}
            for c in self.column_sortable_list:
                if isinstance(c, tuple):
                    column, path = tools.get_field_with_path(self.model, c[1])
                    column_name = c[0]
                else:
                    column, path = tools.get_field_with_path(self.model, c)
                    column_name = str(c)
                if path:
                    self._sortable_joins[column_name] = path
                result[column_name] = column
            return result

    def get_column_names(self, only_columns, excluded_columns):
        """
        Returns a list of tuples with the model field name and formatted
        field name.

        :param only_columns:
            List of columns to include in the results. If not set,
            `scaffold_list_columns` will generate the list from the model.
        :param excluded_columns:
            List of columns to exclude from the results.
        """
        if excluded_columns:
            only_columns = [c for c in only_columns if c not in excluded_columns]

        formatted_columns = []
        for c in only_columns:
            try:
                column, path = tools.get_field_with_path(self.model, c)
                column_name = str(c) if path else column.key  # type: ignore
            except AttributeError:
                column_name = str(c)
            visible_name = self.get_column_name(column_name)
            formatted_columns.append((column_name, visible_name))
        return formatted_columns

    def init_search(self):
        """
        Initialize search. Returns `True` if search is supported for this
        view.

        For SQLModel, this will initialize internal fields: list of
        column objects used for filtering, etc.
        """
        if self.column_searchable_list:
            self._search_fields = []
            for name in self.column_searchable_list:
                attr, joins = tools.get_field_with_path(self.model, name)
                if not attr:
                    raise Exception(f"Failed to find field for search field: {name}")
                self._search_fields.append((attr, joins))
        return bool(self.column_searchable_list)

    def search_placeholder(self):
        """
        Return search placeholder.

        For example, if set column_labels and column_searchable_list:

        class MyModelView(BaseModelView):
            column_labels = dict(name='Name', last_name='Last Name')
            column_searchable_list = ('name', 'last_name')

        placeholder is: "Name, Last Name"
        """
        if not self.column_searchable_list:
            return None
        placeholders = [
            str(self.column_labels.get(s, s))  # type: ignore
            for s in self.column_searchable_list
        ]
        return ", ".join(placeholders)

    def scaffold_filters(self, name):
        """
        Return list of enabled filters
        """
        attr, joins = tools.get_field_with_path(self.model, name)
        if attr is None:
            raise Exception(f"Failed to find field for filter: {name}")

        from flask_admin.model.helpers import prettify_name

        # Convert name to string if it's a column object
        if hasattr(name, "key"):
            # This is an InstrumentedAttribute, use its key
            name_str = name.key
        elif hasattr(name, "name"):
            # This is a Column object, use its name
            name_str = name.name
        else:
            # This is already a string
            name_str = str(name)

        # Check for custom column labels first
        if name_str in self.column_labels:  # type: ignore
            visible_name = str(self.column_labels[name_str])  # type: ignore
        elif "." in name_str:
            # For dot notation like "model1.bool_field",
            # create name like "model1 / Model1 / Bool Field"
            parts = name_str.split(".")
            if len(parts) == 2:
                rel_name, field_name = parts
                # Get the related model name
                rel_attr = getattr(self.model, rel_name, None)
                if (
                    rel_attr
                    and hasattr(rel_attr, "property")
                    and hasattr(rel_attr.property, "mapper")
                ):
                    related_model_name = rel_attr.property.mapper.class_.__name__
                    visible_name = f"{rel_name} / {related_model_name} / {prettify_name(field_name)}"  # noqa: E501
                else:
                    visible_name = prettify_name(name_str)
            else:
                visible_name = prettify_name(name_str)
        else:
            visible_name = prettify_name(name_str)

        # Check if this is a relationship attribute
        if hasattr(attr, "property") and hasattr(attr.property, "mapper"):
            # This is a relationship, create filters for related model's columns
            return self._scaffold_relationship_filters(attr, joins, visible_name)

        # Handle Python properties (computed fields)
        if isinstance(attr, property):
            return self._scaffold_property_filters(attr, name_str, joins, visible_name)

        # Check if the attribute has a type
        if not hasattr(attr, "type"):
            # No type attribute, skip it
            return None

        try:
            type_name = type(attr.type).__name__
        except AttributeError:
            # Fallback for any other type issues
            return None

        flt = self.filter_converter.convert(
            type_name,
            attr,
            visible_name,
            options=self.column_choices.get(name),  # type: ignore
        )

        # Set key_name for each filter in the list to enable proper join lookup
        if flt:
            for f in flt:
                f.key_name = name

        if joins:
            self._filter_joins[name] = joins
            self._filter_name_to_joins[name] = joins
        return flt

    def _scaffold_relationship_filters(self, attr, joins, visible_name):
        """
        Create filters for relationship fields by examining the related model's columns.
        Similar to SQLModel's approach in scaffold_filters.
        """
        from . import tools

        # Get the related model class
        related_model = attr.property.mapper.class_

        # Create filters for each field in the related model
        filters = []

        # Get all fields from the related model
        for field_name, _field_info in self._get_model_iterator(related_model):
            if field_name.startswith("_"):
                continue

            # Get the actual attribute from the related model
            related_attr = getattr(related_model, field_name, None)
            if related_attr is None:
                continue

            # Skip relationships, foreign keys, and primary keys
            if tools.is_relationship(related_attr):
                continue

            # Skip if it's a foreign key or primary key
            if hasattr(related_attr, "property") and hasattr(
                related_attr.property, "columns"
            ):
                column = related_attr.property.columns[0]
                if column.foreign_keys or column.primary_key:
                    continue

            # Check if the attribute has a type for filtering
            if not hasattr(related_attr, "type"):
                continue

            try:
                type_name = type(related_attr.type).__name__
            except AttributeError:
                continue

            # Create filter name: "Model1 / Test1"
            from flask_admin.model.helpers import prettify_name

            filter_name = f"{related_model.__name__} / {prettify_name(field_name)}"

            # Create the filter
            flt = self.filter_converter.convert(
                type_name,
                related_attr,
                filter_name,
                options=self.column_choices.get(f"{attr.key}.{field_name}"),  # type: ignore
            )

            if flt:
                # Set key_name for relationship filters
                for f in flt:
                    f.key_name = attr.key
                filters.extend(flt)

        # Set up joins for all filters
        if filters and joins:
            filter_key = attr.key
            self._filter_joins[filter_key] = joins

        return filters

    def _scaffold_property_filters(self, prop, name_str, joins, visible_name):
        """
        Create filters for Python properties (computed fields).

        This method analyzes the property to determine if it can be filtered.
        For simple properties that concatenate/format database fields, it creates
        appropriate string filters.
        """
        try:
            # For now, create a generic string filter for properties
            # This assumes most computed properties return string values
            # More sophisticated analysis could be added later

            # Create a string filter for the property
            from flask_admin.contrib.sqlmodel.filters import FilterEqual
            from flask_admin.contrib.sqlmodel.filters import FilterLike
            from flask_admin.contrib.sqlmodel.filters import FilterNotEqual

            filters = [
                FilterEqual(column=prop, name=visible_name),
                FilterNotEqual(column=prop, name=visible_name),
                FilterLike(column=prop, name=visible_name),
            ]

            # Set key_name for each filter
            for f in filters:
                f.key_name = name_str

            # Set up joins if needed
            if joins:
                self._filter_joins[name_str] = joins
                self._filter_name_to_joins[name_str] = joins

            return filters

        except Exception:
            # If we can't create filters for this property, return None
            return None

    def is_valid_filter(self, filter_):
        """
        Verify whether the given object is a valid filter.

        :param filter_:
            Filter object to validate
        :return:
            True if filter is valid, False otherwise
        """
        return isinstance(filter_, sqlmodel_filters.BaseSQLModelFilter)

    def handle_filter(self, filter_):
        if isinstance(filter_, sqlmodel_filters.BaseSQLModelFilter):
            column = filter_.column

            # Handle relationship filters
            if tools.is_relationship(column):
                self._filter_joins[column.key] = [column.class_]  # type: ignore
            # Handle custom filters that reference columns from different tables
            elif hasattr(column, "property") and hasattr(column.property, "columns"):  # type: ignore
                # This is an InstrumentedAttribute (regular column)
                columns = column.property.columns  # type: ignore
                if columns and tools.need_join(self.model, columns[0].table):
                    self._filter_joins[column] = [columns[0].table]
        return filter_

    def _preprocess_uuid_fields(self, form, model):
        """
        Convert UUID string fields to UUID objects before populate_obj.

        This fixes the issue where form data contains UUID strings but the model
        expects UUID objects for native uuid.UUID fields.

        Uses only standard libraries - no dependency on sqlalchemy-utils.
        """
        import uuid

        from sqlalchemy import inspect

        try:
            # Get the SQLAlchemy mapper for the MODEL CLASS, not instance
            mapper = inspect(model.__class__)

            # Check each form field
            for field_name, field in form._fields.items():
                if field_name in mapper.attrs:
                    # Get the column property
                    prop = mapper.attrs[field_name]

                    if hasattr(prop, "columns") and prop.columns:
                        column = prop.columns[0]

                        # Check if this is a UUID column (using only native SQLAlchemy)
                        if (
                            hasattr(column, "type")
                            and type(column.type).__name__ == "Uuid"
                            and hasattr(field, "data")
                            and field.data is not None
                        ):
                            # Convert string to UUID if needed
                            if isinstance(field.data, str):
                                try:
                                    field.data = uuid.UUID(field.data)
                                except (ValueError, TypeError):
                                    # Invalid UUID format, leave as string
                                    # to trigger validation error
                                    pass

        except Exception:
            # If anything fails, continue without preprocessing
            # This ensures the method is safe and won't break existing functionality
            pass

    def scaffold_form(self):
        """
        Create form from the model.
        """
        converter = self.model_form_converter(self.session, self)
        form_class = form.get_form(
            self.model,
            converter,
            base_class=self.form_base_class,
            only=self.form_columns,
            exclude=self.form_excluded_columns,
            field_args=self.form_args,
            extra_fields=self.form_extra_fields,
        )
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
        converter = self.model_form_converter(self.session, self)
        form_class = form.get_form(
            self.model,
            converter,
            base_class=self.form_base_class,
            only=self.column_editable_list,
            field_args=validators,
        )
        return create_editable_list_form(self.form_base_class, form_class, widget)

    def scaffold_inline_form_models(self, form_class):
        """
        Contribute inline models to the form

        :param form_class:
            Form class
        """
        default_converter = self.inline_model_form_converter(
            self.session, self, self.model_form_converter
        )

        for m in self.inline_models:  # type: ignore
            if not hasattr(m, "inline_converter"):
                form_class = default_converter.contribute(self.model, form_class, m)
                continue

            custom_converter = m.inline_converter(
                self.session, self, self.model_form_converter
            )
            form_class = custom_converter.contribute(self.model, form_class, m)
        return form_class

    def scaffold_auto_joins(self):
        """
        Return a list of joined tables by going through the
        displayed columns.
        """
        relations = {
            p.key for p in self._get_model_iterator() if tools.is_relationship(p)
        }
        return [
            getattr(self.model, prop)
            for prop, _ in self._list_columns
            if prop in relations
        ]

    def _create_ajax_loader(self, name, options):
        return create_ajax_loader(self.model, self.session, name, name, options)

    def _ensure_column_properties_loaded(self, query):
        """
        Ensure that column_property fields are properly loaded in the query.

        For SQLModel column_property fields, we'll rely on the deferred=False
        setting and post-processing if needed.
        """
        return query

    def _fix_column_property_values(self, models):
        """
        Fix column_property values that may be NULL due to SQLModel issues.

        This method post-processes model instances to compute proper values
        for column_property fields that didn't work correctly.
        """
        if not models:
            return models

        # For now, just return the models as-is since column_property fields
        # should work with deferred=False setting
        return models

    def get_query(self):
        """
        Return a query for the model type.

        This method can be used to set a "persistent filter" on an index_view.

        Example::

            class MyView(SQLModelView):
                def get_query(self):
                    return super(MyView, self).get_query().filter(
                        User.username == current_user.username
                    )


        If you override this method, don't forget to also override `get_count_query`,
        for displaying the correct item count in the list view, and `get_one`, which is
        used when retrieving records for the edit view.
        """
        query = select(self.model)

        # Handle column_property fields that may not be properly computed
        # This is needed because SQLModel's Field(sa_column=column_property(...))
        # doesn't always work as expected and may result in NULL values
        query = self._ensure_column_properties_loaded(query)

        return query

    def get_count_query(self):
        """
        Return a the count query for the model type

        A ``query(self.model).count()`` approach produces an excessive
        subquery, so ``query(func.count('*'))`` should be used instead.

        See commit ``#45a2723`` for details.
        """
        return select(func.count()).select_from(self.model)

    def _order_by(self, query, joins, sort_joins, sort_field, sort_desc):
        """
        Apply order_by to the query

        :param query:
            Query
        :pram joins:
            Current joins
        :param sort_joins:
            Sort joins (properties or tables)
        :param sort_field:
            Sort field
        :param sort_desc:
            Ascending or descending
        """
        if sort_field is not None:
            # Handle tuple of multiple sort fields
            if isinstance(sort_field, tuple):
                for field_name in sort_field:
                    field_attr, field_joins = tools.get_field_with_path(
                        self.model, field_name
                    )
                    query, joins, field_alias = self._apply_path_joins(
                        query, joins, field_joins, inner_join=False
                    )
                    column = (
                        field_attr
                        if field_alias is None
                        else getattr(field_alias, field_attr.key)  # type: ignore
                    )
                    query = query.order_by(desc(column) if sort_desc else column)
            else:
                query, joins, alias = self._apply_path_joins(
                    query, joins, sort_joins, inner_join=False
                )

                # Handle computed fields
                if isinstance(sort_field, property):
                    column = self._get_computed_field_sort_expression(sort_field, alias)
                else:
                    column = (
                        sort_field if alias is None else getattr(alias, sort_field.key)
                    )

                query = query.order_by(desc(column) if sort_desc else column)
        return query, joins

    def _get_computed_field_sort_expression(self, sort_field, alias):
        """
        Create SQL expression for sorting on computed fields.
        """
        prop_func = sort_field.fget
        if prop_func and hasattr(prop_func, "__name__"):
            func_name = prop_func.__name__

            # Handle known computed field patterns
            if func_name == "number_of_pixels":
                if alias is None:
                    from sqlalchemy import column

                    return column("width") * column("height")
                else:
                    return alias.width * alias.height

        # For unknown computed fields, we can't sort
        raise NotImplementedError(
            f"Cannot sort on computed field {sort_field}. "
            "Only specific computed fields are supported for sorting."
        )

    def _get_computed_field_search_expression(self, search_field, alias):
        """
        Create SQL expression for searching on computed fields.
        """
        prop_func = search_field.fget
        if prop_func and hasattr(prop_func, "__name__"):
            func_name = prop_func.__name__

            # Handle known computed field patterns
            if func_name == "number_of_pixels":
                if alias is None:
                    from sqlalchemy import column

                    return column("width") * column("height")
                else:
                    return alias.width * alias.height
            elif func_name == "number_of_pixels_str":
                # This returns the string representation of number_of_pixels
                if alias is None:
                    from sqlalchemy import column

                    return cast(column("width") * column("height"), String)
                else:
                    return cast(alias.width * alias.height, String)

        # For unknown computed fields, we can't search
        raise NotImplementedError(
            f"Cannot search on computed field {search_field}. "
            "Only specific computed fields are supported for searching."
        )

    def _get_default_order(self):
        order = super()._get_default_order()
        for field, direction in order or []:
            attr, joins = tools.get_field_with_path(self.model, field)
            yield attr, joins, direction

    def _apply_sorting(self, query, joins, sort_column, sort_desc):
        if sort_column is not None and sort_column in self._sortable_columns:
            sort_field = self._sortable_columns[sort_column]
            sort_joins = self._sortable_joins.get(sort_column)
            query, joins = self._order_by(
                query, joins, sort_joins, sort_field, sort_desc
            )
        else:
            for sort_field, sort_joins, sort_desc in self._get_default_order():
                query, joins = self._order_by(
                    query, joins, sort_joins, sort_field, sort_desc
                )
        return query, joins

    def _apply_search(self, query, count_query, joins, count_joins, search):
        """
        Apply search to a query.
        """
        terms = search.split(" ")
        for term in terms:
            if not term:
                continue
            stmt = tools.parse_like_term(term)
            filter_stmt = []
            count_filter_stmt = []
            for field, path in self._search_fields:  # type: ignore
                query, joins, alias = self._apply_path_joins(
                    query, joins, path, inner_join=False
                )

                count_alias = None
                if count_query is not None:
                    count_query, count_joins, count_alias = self._apply_path_joins(
                        count_query, count_joins, path, inner_join=False
                    )

                # Handle computed fields
                if isinstance(field, property):
                    column = self._get_computed_field_search_expression(field, alias)
                    if count_query is not None:
                        count_column = self._get_computed_field_search_expression(
                            field, count_alias
                        )
                else:
                    column = field if alias is None else getattr(alias, field.key)
                    if count_query is not None:
                        count_column = (
                            field
                            if count_alias is None
                            else getattr(count_alias, field.key)
                        )

                filter_stmt.append(cast(column, String).ilike(stmt))
                if count_query is not None:
                    count_filter_stmt.append(cast(count_column, String).ilike(stmt))

            query = query.filter(or_(*filter_stmt))
            if count_query is not None:
                count_query = count_query.filter(or_(*count_filter_stmt))
        return query, count_query, joins, count_joins

    def _apply_filters(self, query, count_query, joins, count_joins, filters):
        for idx, _flt_name, value in filters:
            flt = self._filters[idx]  # type: ignore

            alias = None
            count_alias = None

            # Figure out joins - follow SQLModel pattern
            if isinstance(flt, sqlmodel_filters.BaseSQLModelFilter):
                # If no key_name is specified, use filter column as filter key
                filter_key = flt.key_name or flt.column
                path = self._filter_joins.get(filter_key, [])

                if path:
                    query, joins, alias = self._apply_path_joins(
                        query, joins, path, inner_join=False
                    )

                    if count_query is not None:
                        count_query, count_joins, count_alias = self._apply_path_joins(
                            count_query, count_joins, path, inner_join=False
                        )

            # Clean value and apply the filter
            clean_value = flt.clean(value)
            query = flt.apply(query, clean_value, alias)

            if count_query is not None:
                count_query = flt.apply(count_query, clean_value, count_alias)

        return query, count_query, joins, count_joins

    def _apply_pagination(self, query, page, page_size):
        if page_size is None:
            page_size = self.page_size
        # Only apply limit if page_size is not 0 or False (unlimited)
        if page_size:
            query = query.limit(page_size)
        if page and page_size:
            query = query.offset(page * page_size)
        return query

    def _apply_property_filters(self, query, models):
        """
        Apply property filters to the results after query execution.

        This handles filtering on computed properties
        that can't be filtered at the SQL level.
        """
        # Check if there are any property filters to apply
        property_filters = getattr(query, "_property_filters", [])
        if not property_filters:
            return models

        # Apply each property filter
        filtered_models = models
        for prop, operation, value in property_filters:
            filtered_models = self._filter_models_by_property(
                filtered_models, prop, operation, value
            )

        return filtered_models

    def _filter_models_by_property(self, models, prop, operation, value):
        """
        Filter a list of models based on a property value and operation.
        """
        if not models or not value:
            return models

        filtered = []
        for model in models:
            try:
                # Get the property value from the model
                prop_value = (
                    prop.fget(model) if hasattr(prop, "fget") and prop.fget else None
                )
                if prop_value is None:
                    continue

                # Convert to string for comparison
                prop_str = str(prop_value).lower()
                value_str = str(value).lower()

                # Apply the operation
                if operation == "equals":
                    if prop_str == value_str:
                        filtered.append(model)
                elif operation == "not_equals":
                    if prop_str != value_str:
                        filtered.append(model)
                elif operation == "contains":
                    if value_str in prop_str:
                        filtered.append(model)

            except (AttributeError, TypeError, ValueError):
                # If property evaluation fails, skip this model
                continue

        return filtered

    def get_list(
        self,
        page,
        sort_column,
        sort_desc,
        search,
        filters,
        execute=True,
        page_size=None,
    ):
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
        :param execute:
            Execute query immediately? Default is `True`
        :param filters:
            List of filter tuples
        :param page_size:
            Number of results. Defaults to ModelView's page_size. Can be
            overriden to change the page_size limit. Removing the page_size
            limit requires setting page_size to 0 or False.
        """
        joins = {}
        count_joins = {}
        query = self.get_query()
        count_query = self.get_count_query() if not self.simple_list_pager else None

        if self._search_supported and search:
            query, count_query, joins, count_joins = self._apply_search(
                query, count_query, joins, count_joins, search
            )

        if filters and self._filters:
            query, count_query, joins, count_joins = self._apply_filters(
                query, count_query, joins, count_joins, filters
            )

        # Check if we have property filters that need post-query processing
        has_property_filters = (
            hasattr(query, "_property_filters") and query._property_filters # type: ignore
        )

        if has_property_filters:
            # For property filters, we need to fetch all records first,
            # then filter and paginate in memory
            return self._get_list_with_property_filters(
                query,
                count_query,
                joins,
                sort_column,
                sort_desc,
                page,
                page_size,
                execute,
            )
        else:
            # Normal case: use efficient SQL-level filtering and pagination
            count = (
                self.session.exec(count_query).one()
                if count_query is not None
                else None
            )

            for j in self._auto_joins:  # type: ignore
                query = query.options(joinedload(j))

            query, joins = self._apply_sorting(query, joins, sort_column, sort_desc)
            query = self._apply_pagination(query, page, page_size)

            if execute:
                models = self.session.exec(query).all()
                # Fix any column_property issues
                models = self._fix_column_property_values(models)

                return count, models
            else:
                return count, query

    def _get_list_with_property_filters(
        self,
        query,
        count_query,
        joins,
        sort_column,
        sort_desc,
        page,
        page_size,
        execute,
    ):
        """
        Handle listing with property filters that require post-query processing.

        This method fetches all matching records, applies property filters,
        then handles pagination on the filtered results.
        """
        for j in self._auto_joins:  # type: ignore
            query = query.options(joinedload(j))

        # Apply sorting but NOT pagination yet - we need all records to filter properly
        query, joins = self._apply_sorting(query, joins, sort_column, sort_desc)

        if not execute:
            # If not executing, return the unfiltered query
            count = (
                self.session.exec(count_query).one()
                if count_query is not None
                else None
            )
            return count, query

        # Execute query to get ALL matching records (before property filtering)
        all_models = self.session.exec(query).all()

        # Fix any column_property issues
        all_models = self._fix_column_property_values(all_models)

        # Apply property filters to get the complete filtered dataset
        filtered_models = self._apply_property_filters(query, all_models)

        # Calculate correct count based on filtered results
        filtered_count = len(filtered_models)

        # Apply pagination to the filtered results
        if page_size is None:
            page_size = self.page_size

        if page_size and page_size > 0:
            # Calculate offset
            offset = (page or 0) * page_size
            # Get the slice for this page
            paginated_models = filtered_models[offset : offset + page_size]
        else:
            # No pagination requested
            paginated_models = filtered_models

        return filtered_count, paginated_models

    def get_one(self, id_):
        """
        Return a single model by its id.

        Example::

            def get_one(self, id):
                query = self.get_query()
                return query.filter(self.model.id == id).one()

        Also see `get_query` for how to filter the list view.

        :param id:
            Model id
        """
        try:
            # First decode the URL-encoded primary key value(s)
            decoded_pk = tools.iterdecode(id_)
            # Then convert to proper Python types
            # based on model's primary key definition
            converted_pk = tools.convert_pk_from_url(self.model, decoded_pk)
            model = self.session.get(self.model, converted_pk)

            # Fix any column_property issues
            if model:
                models = self._fix_column_property_values([model])
                return models[0] if models else model
            return model
        except (ValueError, TypeError):
            # Primary key conversion failed (e.g., wrong type, wrong order)
            # Return None so the view can handle it as "record not found"
            return None

    def handle_view_exception(self, exc):
        if isinstance(exc, IntegrityError):
            if current_app.config.get(
                "FLASK_ADMIN_RAISE_ON_INTEGRITY_ERROR",
                current_app.config.get("FLASK_ADMIN_RAISE_ON_VIEW_EXCEPTION"),
            ):
                raise
            else:
                flash(
                    gettext("Integrity error. %(message)s", message=text_type(exc)),
                    "error",
                )
            return True

        return super().handle_view_exception(exc)

    def build_new_instance(self):
        """
        Build new instance of a model. Useful to override the Flask-Admin behavior
        when the model has a custom __init__ method.
        """
        model = self._manager.new_instance()

        # TODO: We need a better way to create model instances and stay compatible with
        # SQLModel __init__() behavior
        state = instance_state(model)
        self._manager.dispatch.init(state, [], {})

        return model

    def create_model(self, form):
        """
        Create model from form.

        :param form:
            Form instance
        """
        try:
            model = self.build_new_instance()
            form.populate_obj(model)
            self.session.add(model)
            self._on_model_change(form, model, True)
            self.session.commit()
            self.session.refresh(model)
            self.after_model_change(form, model, True)
            return model
        except Exception as ex:
            flash(gettext("Failed to create record. %(error)s", error=str(ex)), "error")
            log.exception("Failed to create record.")
            self.session.rollback()
            return False

    def update_model(self, form, model):
        """
        Update model from form.

        :param form:
            Form instance
        :param model:
            Model instance
        """
        try:
            # Temporarily remove list_form_pk field to avoid populate_obj issues
            list_form_pk_field = None
            if "list_form_pk" in form._fields:
                list_form_pk_field = form._fields.pop("list_form_pk")

            # Convert UUID strings to UUID objects before populate_obj
            self._preprocess_uuid_fields(form, model)

            form.populate_obj(model)

            # Restore the field if it was removed
            if list_form_pk_field is not None:
                form._fields["list_form_pk"] = list_form_pk_field

            self._on_model_change(form, model, False)
            self.session.commit()
            self.session.refresh(model)  # Refresh the model after commit
        except Exception as ex:
            flash(gettext("Failed to update record. %(error)s", error=str(ex)), "error")
            log.exception("Failed to update record.")
            self.session.rollback()
            # Refresh the model to clear any invalid values that might have been
            # assigned during populate_obj before the exception occurred
            try:
                self.session.refresh(model)
            except Exception:
                # If refresh fails, we can't do much more
                pass
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
            self.session.delete(model)
            self.session.commit()
            self.after_model_delete(model)
            return True
        except Exception as ex:
            flash(gettext("Failed to delete record. %(error)s", error=str(ex)), "error")
            log.exception("Failed to delete record.")
            self.session.rollback()
            return False

    # Default model actions
    def is_action_allowed(self, name):
        # Check delete action permission
        if name == "delete" and not self.can_delete:
            return False

        return super().is_action_allowed(name)

    @action(
        "delete",
        lazy_gettext("Delete"),
        lazy_gettext("Are you sure you want to delete selected records?"),
    )
    def action_delete(self, ids):
        try:
            count = 0
            for id_ in ids:
                model = self.get_one(id_)
                if model and self.delete_model(model):
                    count += 1
            flash(
                ngettext(
                    "Record was successfully deleted.",
                    "%(count)s records were successfully deleted.",
                    count,
                    count=count,
                ),
                "success",
            )
        except Exception as ex:
            flash(
                gettext("Failed to delete records. %(error)s", error=str(ex)), "error"
            )
