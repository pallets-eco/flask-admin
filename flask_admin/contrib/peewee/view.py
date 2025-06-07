import logging
import typing as t

from flask import flash
from peewee import CharField
from peewee import Expression
from peewee import Field
from peewee import ForeignKeyField
from peewee import JOIN
from peewee import ModelSelect
from peewee import PrimaryKeyField
from peewee import TextField
from typing_extensions import TypeGuard
from wtforms import Form

from flask_admin._compat import string_types
from flask_admin.actions import action
from flask_admin.babel import gettext
from flask_admin.babel import lazy_gettext
from flask_admin.babel import ngettext
from flask_admin.contrib.peewee import filters
from flask_admin.model import BaseModelView
from flask_admin.model.filters import BaseFilter
from flask_admin.model.form import create_editable_list_form
from flask_admin.model.form import InlineFormAdmin

from ..._types import T_FIELD_ARGS_VALIDATORS
from ..._types import T_FILTER
from ..._types import T_PEEWEE_MODEL
from ..._types import T_WIDGET
from .ajax import create_ajax_loader
from .ajax import QueryAjaxModelLoader
from .form import CustomModelConverter
from .form import get_form
from .form import InlineModelConverter
from .form import save_inline
from .tools import get_meta_fields
from .tools import get_primary_key
from .tools import parse_like_term

# Set up logger
log = logging.getLogger("flask-admin.peewee")


class ModelView(BaseModelView):
    column_filters: t.Optional[t.Collection[t.Union[str, BaseFilter]]] = None
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

    model_form_converter: type[CustomModelConverter] = CustomModelConverter
    """
        Model form conversion class. Use this to implement custom field conversion
        logic.

        For example::

            class MyModelConverter(AdminModelConverter):
                pass


            class MyAdminView(ModelView):
                model_form_converter = MyModelConverter
    """

    inline_model_form_converter: type[InlineModelConverter] = InlineModelConverter
    """
        Inline model conversion class. If you need some kind of post-processing for
        inline forms, you can customize behavior by doing something like this::

            class MyInlineModelConverter(AdminModelConverter):
                def post_process(self, form_class, info):
                    form_class.value = TextField('value')
                    return form_class

            class MyAdminView(ModelView):
                inline_model_form_converter = MyInlineModelConverter
    """

    filter_converter: filters.FilterConverter = filters.FilterConverter()
    """
        Field to filter converter.

        Override this attribute to use non-default converter.
    """

    fast_mass_delete: bool = False
    """
        If set to `False` and user deletes more than one model using actions,
        all models will be read from the database and then deleted one by one
        giving Peewee chance to manually cleanup any dependencies (many-to-many
        relationships, etc).

        If set to True, will run DELETE statement which is somewhat faster, but
        might leave corrupted data if you forget to configure DELETE CASCADE
        for your model.
    """

    inline_models: t.Optional[
        t.Union[
            t.Sequence[t.Union[InlineFormAdmin, T_PEEWEE_MODEL]],
            tuple[T_PEEWEE_MODEL, dict[str, t.Any]],
        ]
    ] = None
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

    def __init__(
        self,
        model: type[T_PEEWEE_MODEL],
        name: t.Optional[str] = None,
        category: t.Optional[str] = None,
        endpoint: t.Optional[str] = None,
        url: t.Optional[str] = None,
        static_folder: t.Optional[str] = None,
        menu_class_name: t.Optional[str] = None,
        menu_icon_type: t.Optional[str] = None,
        menu_icon_value: t.Optional[str] = None,
    ) -> None:
        self._search_fields: list = []

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
        self.model: type[T_PEEWEE_MODEL]
        self._primary_key = self.scaffold_pk()

    def _get_model_fields(
        self, model: t.Optional[T_PEEWEE_MODEL] = None
    ) -> t.Generator[tuple[str, Field], t.Any, None]:
        if model is None:
            model = self.model

        return ((field.name, field) for field in get_meta_fields(model))

    def scaffold_pk(self) -> str:
        return get_primary_key(self.model)

    def get_pk_value(self, model: type[T_PEEWEE_MODEL]) -> t.Any:
        if self.model._meta.composite_key:
            return tuple(
                [
                    getattr(model, field_name)
                    for field_name in self.model._meta.primary_key.field_names
                ]
            )
        return getattr(model, self._primary_key)

    def scaffold_list_columns(self) -> list[str]:
        columns = []

        for n, f in self._get_model_fields():
            if isinstance(f, ForeignKeyField):
                columns.append(n)
            elif self.column_display_pk or not isinstance(f, PrimaryKeyField):
                columns.append(n)

        return columns

    def scaffold_sortable_columns(self) -> dict[str, Field]:  # type: ignore[override]
        columns = dict()

        for n, f in self._get_model_fields():
            if self.column_display_pk or not isinstance(f, PrimaryKeyField):
                columns[n] = f

        return columns

    def init_search(self) -> bool:
        if self.column_searchable_list:
            for p in self.column_searchable_list:
                if isinstance(p, string_types):
                    p = getattr(self.model, p)

                # Check type
                if not isinstance(p, (CharField, TextField)):
                    raise Exception(
                        f"Can only search on text columns. "
                        f'Failed to setup search for "{p}"'
                    )

                self._search_fields.append(p)

        return bool(self._search_fields)

    def scaffold_filters(
        self, name: t.Union[str, BaseFilter]
    ) -> t.Optional[list[BaseFilter]]:
        if isinstance(name, string_types):
            attr = getattr(self.model, name, None)
        else:
            attr = name

        if attr is None:
            raise Exception(f"Failed to find field for filter: {name}")

        # Check if field is in different model
        model_class = None
        try:
            model_class = attr.model_class
        except AttributeError:
            model_class = attr.model

        if model_class != self.model:
            visible_name = (
                f"{self.get_column_name(model_class.__name__)}"
                f" / {self.get_column_name(attr.name)}"
            )
        else:
            if not isinstance(name, string_types):
                visible_name = self.get_column_name(attr.name)
            else:
                visible_name = self.get_column_name(name)

        type_name = type(attr).__name__
        flt = self.filter_converter.convert(type_name, attr, visible_name)

        return flt

    def is_valid_filter(
        self,
        filter: t.Union[filters.BasePeeweeFilter, t.Any],
    ) -> TypeGuard[filters.BasePeeweeFilter]:
        return isinstance(filter, filters.BasePeeweeFilter)

    def scaffold_form(self) -> type[Form]:
        form_class = get_form(
            self.model,
            self.model_form_converter(self),
            base_class=self.form_base_class,
            only=self.form_columns,
            exclude=self.form_excluded_columns,
            field_args=self.form_args,
            # Allow child to specify pk, so inline_models
            # can be ModelViews. But don't auto-generate
            # pk field if form_columns is empty -- allow
            # default behaviour in that case.
            allow_pk=bool(self.form_columns),
            extra_fields=self.form_extra_fields,
        )

        if self.inline_models:
            form_class = self.scaffold_inline_form_models(form_class)

        return form_class

    def scaffold_list_form(
        self,
        widget: t.Optional[type[T_WIDGET]] = None,
        validators: t.Optional[dict[str, T_FIELD_ARGS_VALIDATORS]] = None,
    ) -> type[Form]:
        """
        Create form for the `index_view` using only the columns from
        `self.column_editable_list`.

        :param widget:
            WTForms widget class. Defaults to `XEditableWidget`.
        :param validators:
            `form_args` dict with only validators
            {'name': {'validators': [required()]}}
        """
        form_class = get_form(
            self.model,
            self.model_form_converter(self),
            base_class=self.form_base_class,
            only=self.column_editable_list,
            field_args=validators,
        )

        return create_editable_list_form(self.form_base_class, form_class, widget)

    def scaffold_inline_form_models(self, form_class: type[Form]) -> type[Form]:
        converter = self.model_form_converter(self)
        inline_converter = self.inline_model_form_converter(self)

        for m in self.inline_models:  # type: ignore[union-attr]
            form_class = inline_converter.contribute(
                converter, self.model, form_class, m
            )

        return form_class

    # AJAX foreignkey support
    def _create_ajax_loader(
        self, name: str, options: t.Union[dict[str, t.Any], list, tuple]
    ) -> QueryAjaxModelLoader:
        return create_ajax_loader(self.model, name, name, options)

    def _handle_join(
        self, query: ModelSelect, field: t.Any, joins: set[str]
    ) -> ModelSelect:
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

    def _order_by(
        self, query: ModelSelect, joins: set[str], order: list[tuple[str, bool]]
    ) -> tuple[ModelSelect, set[str]]:
        clauses = []
        for sort_field, sort_desc in order:
            query, joins, clause = self._sort_clause(
                query, joins, sort_field, sort_desc
            )
            clauses.append(clause)
        query = query.order_by(*clauses)
        return query, joins

    def _sort_clause(
        self, query: ModelSelect, joins: set[str], sort_field: str, sort_desc: bool
    ) -> tuple[ModelSelect, set[str], Expression]:
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

    def get_query(self) -> ModelSelect:
        return self.model.select()

    def get_list(  # type: ignore[override]
        self,
        page: t.Optional[int],
        sort_column: t.Optional[str],
        sort_desc: t.Optional[bool],
        search: t.Optional[str],
        filters: t.Optional[t.Sequence[T_FILTER]],
        execute: bool = True,
        page_size: t.Optional[int] = None,
    ) -> tuple[t.Optional[int], t.Union[list, ModelSelect]]:
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

        joins: set[str] = set()

        # Search
        if self._search_supported and search:
            values = search.split(" ")

            for value in values:
                if not value:
                    continue

                term = parse_like_term(value)

                stmt = None
                for field in self._search_fields:
                    query = self._handle_join(query, field, joins)

                    q = field**term

                    if stmt is None:
                        stmt = q
                    else:
                        stmt |= q

                query = query.where(stmt)

        # Filters
        if self._filters:
            for flt, _flt_name, value in filters:  # type: ignore[union-attr]
                f = self._filters[flt]

                query = self._handle_join(query, f.column, joins)  # type: ignore[attr-defined]
                query = f.apply(query, f.clean(value))

        # Get count
        count = query.count() if not self.simple_list_pager else None

        # Apply sorting
        order: t.Optional[list[tuple[str, bool]]]
        if sort_column is not None:
            sort_field = t.cast(str, self._sortable_columns[sort_column])
            order = [(sort_field, sort_desc)]  # type: ignore[list-item]
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
            query = list(query.execute())  # type: ignore[assignment]

        return count, query

    def get_one(self, id: t.Any) -> t.Any:
        if self.model._meta.composite_key:
            return self.model.get(
                **dict(zip(self.model._meta.primary_key.field_names, id))
            )
        return self.model.get(**{self._primary_key: id})

    def create_model(self, form: Form) -> t.Union[bool, T_PEEWEE_MODEL]:
        try:
            model = self.model()
            form.populate_obj(model)
            self._on_model_change(form, model, True)
            model.save(force_insert=True)

            # For peewee have to save inline forms after model was saved
            save_inline(form, model)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(
                    gettext("Failed to create record. %(error)s", error=str(ex)),
                    "error",
                )
                log.exception("Failed to create record.")

            return False
        else:
            self.after_model_change(form, model, True)

        return model

    def update_model(self, form: Form, model: T_PEEWEE_MODEL) -> t.Optional[bool]:
        try:
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            model.save()

            # For peewee have to save inline forms after model was saved
            save_inline(form, model)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(
                    gettext("Failed to update record. %(error)s", error=str(ex)),
                    "error",
                )
                log.exception("Failed to update record.")

            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def delete_model(self, model: T_PEEWEE_MODEL) -> bool:
        try:
            self.on_model_delete(model)
            model.delete_instance(recursive=True)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(
                    gettext("Failed to delete record. %(error)s", error=str(ex)),
                    "error",
                )
                log.exception("Failed to delete record.")

            return False
        else:
            self.after_model_delete(model)

        return True

    # Default model actions
    def is_action_allowed(self, name: str) -> bool:
        # Check delete action permission
        if name == "delete" and not self.can_delete:
            return False

        return super().is_action_allowed(name)

    @action(
        "delete",
        lazy_gettext("Delete"),
        lazy_gettext("Are you sure you want to delete selected records?"),
    )
    def action_delete(self, ids: t.Any) -> None:
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
            if not self.handle_view_exception(ex):
                flash(
                    gettext("Failed to delete records. %(error)s", error=str(ex)),
                    "error",
                )
