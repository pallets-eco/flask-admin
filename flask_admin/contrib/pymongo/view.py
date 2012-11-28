import logging

import pymongo
from bson.objectid import ObjectId

from flask import flash
from jinja2 import contextfunction

from flask.ext.admin.babel import gettext, ngettext, lazy_gettext
from flask.ext.admin.model import BaseModelView
from flask.ext.admin.actions import action

from .filters import BasePyMongoFilter
from .tools import parse_like_term


class ModelView(BaseModelView):
    """
        MongoEngine model scaffolding.
    """

    column_filters = None
    """
        Collection of the column filters.

        Should contain instances of
        :class:`flask.ext.admin.contrib.pymongo.filters.BasePyMongoFilter`
        classes.

        For example::

            class MyModelView(BaseModelView):
                column_filters = (BooleanEqualFilter(User.name, 'Name'),)
    """

    def __init__(self, coll,
                 name=None, category=None, endpoint=None, url=None):
        """
            Constructor

            :param coll:
                MongoDB collection object
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

        if name is None:
            name = self._prettify_name(coll.name)

        if endpoint is None:
            endpoint = ('%sview' % coll.name).lower()

        super(ModelView, self).__init__(None, name, category, endpoint, url)

        self.coll = coll

    def scaffold_pk(self):
        return '_id'

    def get_pk_value(self, model):
        """
            Return primary key value from the model instance

            :param model:
                Model instance
        """
        return model.get('_id')

    def scaffold_list_columns(self):
        """
            Scaffold list columns
        """
        raise NotImplemented()

    def scaffold_sortable_columns(self):
        """
            Return sortable columns dictionary (name, field)
        """
        return []

    def init_search(self):
        """
            Init search
        """
        if self.column_searchable_list:
            for p in self.column_searchable_list:
                if not isinstance(p, basestring):
                    raise ValueError('Expected string')

                # TODO: Validation?

                self._search_fields.append(p)

        return bool(self._search_fields)

    def scaffold_filters(self, attr):
        """
            Return filter object(s) for the field

            :param name:
                Either field name or field instance
        """
        raise NotImplemented()

    def is_valid_filter(self, filter):
        """
            Validate if it is valid MongoEngine filter

            :param filter:
                Filter object
        """
        return isinstance(filter, BasePyMongoFilter)

    def scaffold_form(self):
        raise NotImplemented()

    @contextfunction
    def get_list_value(self, context, model, name):
        """
            Returns value to be displayed in list view

            :param context:
                :py:class:`jinja2.runtime.Context`
            :param model:
                Model instance
            :param name:
                Field name
        """
        column_fmt = self.column_formatters.get(name)
        if column_fmt is not None:
            return column_fmt(context, model, name)

        value = model.get(name)

        type_fmt = self.column_type_formatters.get(type(value))
        if type_fmt is not None:
            value = type_fmt(value)

        return value

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
        query = {}

        # Filters
        if self._filters:
            data = []

            for flt, value in filters:
                f = self._filters[flt]
                data = f.apply(data, value)

            if data:
                if len(data) == 1:
                    query = data[0]
                else:
                    query['$AND'] = data

        # Search
        if self._search_supported and search:
            values = search.split(' ')

            queries = []

            # Construct inner querie
            for value in values:
                if not value:
                    continue

                regex = parse_like_term(value)

                stmt = []
                for field in self._search_fields:
                    stmt.append({field: {'$regex': regex}})

                if stmt:
                    if len(stmt) == 1:
                        queries.append(stmt[0])
                    else:
                        queries.append({'$or': stmt})

            # Construct final query
            if queries:
                if len(queries) == 1:
                    final = queries[0]
                else:
                    final = {'$and': queries}

                if query:
                    query = {'$and': [query, final]}
                else:
                    query = final

        # Get count
        count = self.coll.find(query).count()

        # Sorting
        sort_by = None

        if sort_column:
            sort_by = [(sort_column, pymongo.DESCENDING if sort_desc else pymongo.ASCENDING)]

        # Pagination
        skip = None

        if page is not None:
            skip = page * self.page_size

        results = self.coll.find(query, sort=sort_by, skip=skip, limit=self.page_size)

        if execute:
            results = list(results)

        return count, results

    def get_one(self, id):
        """
            Return single model instance by ID

            :param id:
                Model ID
        """
        # TODO: Validate if it is valid ID
        return self.coll.find_one({'_id': ObjectId(id)})

    def edit_form(self, obj):
        """
            Create edit form from the MongoDB document
        """
        return self._edit_form_class(**obj)

    def create_model(self, form):
        """
            Create model helper

            :param form:
                Form instance
        """
        try:
            model = form.data
            self.on_model_change(form, model)
            self.coll.insert(model)
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
            model.update(form.data)
            self.on_model_change(form, model)

            pk = self.get_pk_value(model)
            self.coll.update({'_id': pk}, model)
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
            pk = self.get_pk_value(model)

            if not pk:
                raise ValueError('Document does not have _id')

            self.on_model_delete(model)
            self.coll.remove({'_id': pk})
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

            # TODO: Optimize me
            for pk in ids:
                self.coll.remove({'_id': ObjectId(pk)})
                count += 1

            flash(ngettext('Model was successfully deleted.',
                           '%(count)s models were successfully deleted.',
                           count,
                           count=count))
        except Exception, ex:
            flash(gettext('Failed to delete models. %(error)s', error=str(ex)),
                'error')
