import logging

from flask import flash

from flask.ext.admin.babel import gettext, ngettext, lazy_gettext
from flask.ext.admin.model import BaseModelView

import mongoengine
from bson.objectid import ObjectId

from flask.ext.admin.actions import action
from flask.ext.admin.form import BaseForm
from .filters import FilterConverter, BaseMongoEngineFilter
from .form import model_form, CustomModelConverter
from .typefmt import DEFAULT_FORMATTERS
from .tools import parse_like_term


SORTABLE_FIELDS = set((
    mongoengine.StringField,
    mongoengine.IntField,
    mongoengine.FloatField,
    mongoengine.BooleanField,
    mongoengine.DateTimeField,
    mongoengine.ObjectIdField,
    mongoengine.DecimalField,
    mongoengine.ReferenceField,
    mongoengine.EmailField,
    mongoengine.UUIDField
    ))


class ModelView(BaseModelView):
    """
        MongoEngine model scaffolding.
    """

    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of
        :class:`flask.ext.admin.contrib.mongoengine.filters.BaseFilter`
        classes.

        For example::

            class MyModelView(BaseModelView):
                column_filters = ('user', 'email')

        or::

            class MyModelView(BaseModelView):
                column_filters = (BooleanEqualFilter(User.name, 'Name'))
    """

    model_form_converter = CustomModelConverter
    """
        Model form conversion class. Use this to implement custom
        field conversion logic.

        For example::

            class MyModelConverter(AdminModelConverter):
                pass


            class MyAdminView(ModelView):
                model_form_converter = MyModelConverter
    """

    filter_converter = FilterConverter()
    """
        Field to filter converter.

        Override this attribute to use non-default converter.
    """

    column_type_formatters = DEFAULT_FORMATTERS
    """
        Customized type formatters for MongoEngine backend
    """

    def __init__(self, model, name=None,
                 category=None, endpoint=None, url=None):
        """
            Constructor

            :param model:
                Model class
            :param name:
                Display name
            :param category:
                Display category
            :param endpoint:
                Endpoint
            :param url:
                Custom URL
        """
        self._search_fields = []

        super(ModelView, self).__init__(model, name, category, endpoint, url)

        self._primary_key = self.scaffold_pk()

    def _get_model_fields(self, model=None):
        """
            Inspect model and return list of model fields

            :param model:
                Model to inspect
        """
        if model is None:
            model = self.model

        return sorted(model._fields.iteritems(), key=lambda n: n[1].creation_counter)

    def scaffold_pk(self):
        # MongoEngine models have predefined 'id' as a key
        return 'id'

    def get_pk_value(self, model):
        """
            Return primary key value from the model instance

            :param model:
                Model instance
        """
        return model.pk

    def scaffold_list_columns(self):
        """
            Scaffold list columns
        """
        columns = []

        for n, f in self._get_model_fields():
            # Verify type
            field_class = type(f)

            if (field_class == mongoengine.ListField and
                isinstance(f.field, mongoengine.EmbeddedDocumentField)):
                continue

            if field_class == mongoengine.EmbeddedDocumentField:
                continue

            if self.column_display_pk or field_class != mongoengine.ObjectIdField:
                columns.append(n)

        return columns

    def scaffold_sortable_columns(self):
        """
            Return sortable columns dictionary (name, field)
        """
        columns = {}

        for n, f in self._get_model_fields():
            if type(f) in SORTABLE_FIELDS:
                if self.column_display_pk or type(f) != mongoengine.ObjectIdField:
                    columns[n] = f

        return columns

    def init_search(self):
        """
            Init search
        """
        if self.column_searchable_list:
            for p in self.column_searchable_list:
                if isinstance(p, basestring):
                    p = self.model._fields.get(p)

                if p is None:
                    raise Exception('Invalid search field')

                field_type = type(p)

                # Check type
                if (field_type != mongoengine.StringField):
                        raise Exception('Can only search on text columns. ' +
                                        'Failed to setup search for "%s"' % p)

                self._search_fields.append(p)

        return bool(self._search_fields)

    def scaffold_filters(self, name):
        """
            Return filter object(s) for the field

            :param name:
                Either field name or field instance
        """
        if isinstance(name, basestring):
            attr = self.model._fields.get(name)
        else:
            attr = name

        if attr is None:
            raise Exception('Failed to find field for filter: %s' % name)

        # Find name
        visible_name = None

        if not isinstance(name, basestring):
            visible_name = self.get_column_name(attr.name)

        if not visible_name:
            visible_name = self.get_column_name(name)

        # Convert filter
        type_name = type(attr).__name__
        flt = self.filter_converter.convert(type_name,
                                            attr,
                                            visible_name)

        return flt

    def is_valid_filter(self, filter):
        """
            Validate if it is valid MongoEngine filter

            :param filter:
                Filter object
        """
        return isinstance(filter, BaseMongoEngineFilter)

    def scaffold_form(self):
        # TODO: Fix base_class
        form_class = model_form(self.model,
                        base_class=BaseForm,
                        only=self.form_columns,
                        exclude=self.form_excluded_columns,
                        field_args=self.form_args,
                        converter=self.model_form_converter())

        return form_class

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True):
        """
            Get list of objects from MongoEngine

            :param page:
                Page number
            :param sort_column:
                Sort column
            :param sort_desc:
                Sort descending
            :param search:
                Search criteria
            :param filters:
                List of applied fiters
            :param execute:
                Run query immediately or not
        """
        query = self.model.objects

        # Filters
        if self._filters:
            for flt, value in filters:
                f = self._filters[flt]
                query = f.apply(query, value)

        # Search
        if self._search_supported and search:
            # TODO: Unfortunately, MongoEngine contains bug which
            # prevents running complex Q queries and, as a result,
            # Flask-Admin does not support per-word searching like
            # in other backends
            op, term = parse_like_term(search)

            criteria = None

            for field in self._search_fields:
                flt = {'%s__%s' % (field.name, op): term}
                q = mongoengine.Q(**flt)

                if criteria is None:
                    criteria = q
                else:
                    criteria |= q

            query = query.filter(criteria)

        # Get count
        count = query.count()

        # Sorting
        if sort_column:
            query = query.order_by('%s%s' % ('-' if sort_desc else '', sort_column))

        # Pagination
        if page is not None:
            query = query.skip(page * self.page_size)

        query = query.limit(self.page_size)

        if execute:
            query = query.all()

        return count, query

    def get_one(self, id):
        """
            Return single model instance by ID

            :param id:
                Model ID
        """
        return self.model.objects.with_id(id)

    def create_model(self, form):
        """
            Create model helper

            :param form:
                Form instance
        """
        try:
            model = self.model()
            form.populate_obj(model)
            self.on_model_change(form, model)
            model.save()
            return True
        except Exception, ex:
            flash(gettext('Failed to create model. %(error)s', error=str(ex)),
                'error')
            logging.exception('Failed to create model')
            return False

    def update_model(self, form, model):
        """
            Update model helper

            :param form:
                Form instance
            :param model:
                Model instance to update
        """
        try:
            form.populate_obj(model)
            self.on_model_change(form, model)
            model.save()
            return True
        except Exception, ex:
            flash(gettext('Failed to update model. %(error)s', error=str(ex)),
                'error')
            logging.exception('Failed to update model')
            return False

    def delete_model(self, model):
        """
            Delete model helper

            :param model:
                Model instance
        """
        try:
            self.on_model_delete(model)
            model.delete()
            return True
        except Exception, ex:
            flash(gettext('Failed to delete model. %(error)s', error=str(ex)),
                'error')
            logging.exception('Failed to delete model')
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
            count = 0

            all_ids = [ObjectId(pk) for pk in ids]
            for obj in self.model.objects.in_bulk(all_ids).values():
                obj.delete()
                count += 1

            flash(ngettext('Model was successfully deleted.',
                           '%(count)s models were successfully deleted.',
                           count,
                           count=count))
        except Exception, ex:
            flash(gettext('Failed to delete models. %(error)s', error=str(ex)),
                'error')
