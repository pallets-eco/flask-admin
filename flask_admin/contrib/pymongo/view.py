import logging

import pymongo
from bson import ObjectId
from bson.errors import InvalidId

from flask import flash

from flask_admin._compat import string_types
from flask_admin.babel import gettext, ngettext, lazy_gettext
from flask_admin.model import BaseModelView
from flask_admin.actions import action
from flask_admin.helpers import get_form_data

from .filters import BasePyMongoFilter
from .tools import parse_like_term

# Set up logger
log = logging.getLogger("flask-admin.pymongo")


class ModelView(BaseModelView):
    """
        MongoEngine model scaffolding.
    """

    column_filters = None
    """
        Collection of the column filters.

        Should contain instances of
        :class:`flask_admin.contrib.pymongo.filters.BasePyMongoFilter` classes.

        Filters will be grouped by name when displayed in the drop-down.

        For example::

            from flask_admin.contrib.pymongo.filters import BooleanEqualFilter

            class MyModelView(BaseModelView):
                column_filters = (BooleanEqualFilter(column=User.name, name='Name'),)

        or::

            from flask_admin.contrib.pymongo.filters import BasePyMongoFilter

            class FilterLastNameBrown(BasePyMongoFilter):
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

    def __init__(self, coll,
                 name=None, category=None, endpoint=None, url=None,
                 menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
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
            :param menu_class_name:
                Optional class name for the menu item.
            :param menu_icon_type:
                Optional icon. Possible icon types:

                 - `flask_admin.consts.ICON_TYPE_GLYPH` - Bootstrap glyph icon
                 - `flask_admin.consts.ICON_TYPE_FONT_AWESOME` - Font Awesome icon
                 - `flask_admin.consts.ICON_TYPE_IMAGE` - Image relative to Flask static directory
                 - `flask_admin.consts.ICON_TYPE_IMAGE_URL` - Image with full URL
            :param menu_icon_value:
                Icon glyph name or URL, depending on `menu_icon_type` setting
        """
        self._search_fields = []

        if name is None:
            name = self._prettify_name(coll.name)

        if endpoint is None:
            endpoint = ('%sview' % coll.name).lower()

        super(ModelView, self).__init__(None, name, category, endpoint, url,
                                        menu_class_name=menu_class_name,
                                        menu_icon_type=menu_icon_type,
                                        menu_icon_value=menu_icon_value)

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
        raise NotImplementedError()

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
                if not isinstance(p, string_types):
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
        raise NotImplementedError()

    def is_valid_filter(self, filter):
        """
            Validate if it is valid MongoEngine filter

            :param filter:
                Filter object
        """
        return isinstance(filter, BasePyMongoFilter)

    def scaffold_form(self):
        raise NotImplementedError()

    def _get_field_value(self, model, name):
        """
            Get unformatted field value from the model
        """
        return model.get(name)

    def _search(self, query, search_term):
        values = search_term.split(' ')

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

        return query

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):
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
            :param page_size:
                Number of results. Defaults to ModelView's page_size. Can be
                overriden to change the page_size limit. Removing the page_size
                limit requires setting page_size to 0 or False.
        """
        query = {}

        # Filters
        if self._filters:
            data = []

            for flt, flt_name, value in filters:
                f = self._filters[flt]
                data = f.apply(data, f.clean(value))

            if data:
                if len(data) == 1:
                    query = data[0]
                else:
                    query['$and'] = data

        # Search
        if self._search_supported and search:
            query = self._search(query, search)

        # Get count
        count = self.coll.find(query).count() if not self.simple_list_pager else None

        # Sorting
        sort_by = None

        if sort_column:
            sort_by = [(sort_column, pymongo.DESCENDING if sort_desc else pymongo.ASCENDING)]
        else:
            order = self._get_default_order()

            if order:
                sort_by = [(col, pymongo.DESCENDING if desc else pymongo.ASCENDING)
                           for (col, desc) in order]

        # Pagination
        if page_size is None:
            page_size = self.page_size

        skip = 0

        if page and page_size:
            skip = page * page_size

        results = self.coll.find(query, sort=sort_by, skip=skip, limit=page_size)

        if execute:
            results = list(results)

        return count, results

    def _get_valid_id(self, id):
        try:
            return ObjectId(id)
        except InvalidId:
            return id

    def get_one(self, id):
        """
            Return single model instance by ID

            :param id:
                Model ID
        """
        return self.coll.find_one({'_id': self._get_valid_id(id)})

    def edit_form(self, obj):
        """
            Create edit form from the MongoDB document
        """
        return self._edit_form_class(get_form_data(), **obj)

    def create_model(self, form):
        """
            Create model helper

            :param form:
                Form instance
        """
        try:
            model = form.data
            self._on_model_change(form, model, True)
            self.coll.insert(model)
        except Exception as ex:
            flash(gettext('Failed to create record. %(error)s', error=str(ex)),
                  'error')
            log.exception('Failed to create record.')
            return False
        else:
            self.after_model_change(form, model, True)

        return model

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
            self._on_model_change(form, model, False)

            pk = self.get_pk_value(model)
            self.coll.update({'_id': pk}, model)
        except Exception as ex:
            flash(gettext('Failed to update record. %(error)s', error=str(ex)),
                  'error')
            log.exception('Failed to update record.')
            return False
        else:
            self.after_model_change(form, model, False)

        return True

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
        except Exception as ex:
            flash(gettext('Failed to delete record. %(error)s', error=str(ex)),
                  'error')
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
            count = 0

            # TODO: Optimize me
            for pk in ids:
                if self.delete_model(self.get_one(pk)):
                    count += 1

            flash(ngettext('Record was successfully deleted.',
                           '%(count)s records were successfully deleted.',
                           count,
                           count=count), 'success')
        except Exception as ex:
            flash(gettext('Failed to delete records. %(error)s', error=str(ex)), 'error')
