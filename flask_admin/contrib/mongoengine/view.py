import logging

from flask import request, flash, abort, Response

from flask_admin import expose
from flask_admin.babel import gettext, ngettext, lazy_gettext
from flask_admin.model import BaseModelView
from flask_admin.model.form import create_editable_list_form
from flask_admin._compat import iteritems, string_types

import mongoengine
import gridfs
from mongoengine.connection import get_db
from bson.objectid import ObjectId

from flask_admin.actions import action
from .filters import FilterConverter, BaseMongoEngineFilter
from .form import get_form, CustomModelConverter
from .typefmt import DEFAULT_FORMATTERS
from .tools import parse_like_term
from .helpers import format_error
from .ajax import process_ajax_references, create_ajax_loader
from .subdoc import convert_subdocuments

# Set up logger
log = logging.getLogger("flask-admin.mongo")


SORTABLE_FIELDS = set((
    mongoengine.StringField,
    mongoengine.IntField,
    mongoengine.FloatField,
    mongoengine.BooleanField,
    mongoengine.DateTimeField,
    mongoengine.ComplexDateTimeField,
    mongoengine.ObjectIdField,
    mongoengine.DecimalField,
    mongoengine.ReferenceField,
    mongoengine.EmailField,
    mongoengine.UUIDField,
    mongoengine.URLField
))


class ModelView(BaseModelView):
    """
        MongoEngine model scaffolding.
    """

    column_filters = None
    """
        Collection of the column filters.

        Can contain either field names or instances of
        :class:`flask_admin.contrib.mongoengine.filters.BaseMongoEngineFilter`
        classes.

        Filters will be grouped by name when displayed in the drop-down.

        For example::

            class MyModelView(BaseModelView):
                column_filters = ('user', 'email')

        or::

            from flask_admin.contrib.mongoengine.filters import BooleanEqualFilter

            class MyModelView(BaseModelView):
                column_filters = (BooleanEqualFilter(column=User.name, name='Name'),)

        or::

            from flask_admin.contrib.mongoengine.filters import BaseMongoEngineFilter

            class FilterLastNameBrown(BaseMongoEngineFilter):
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
        Model form conversion class. Use this to implement custom
        field conversion logic.

        Custom class should be derived from the
        `flask_admin.contrib.mongoengine.form.CustomModelConverter`.

        For example::

            class MyModelConverter(AdminModelConverter):
                pass


            class MyAdminView(ModelView):
                model_form_converter = MyModelConverter
    """

    object_id_converter = ObjectId
    """
        Mongodb ``_id`` value conversion function. Default is `bson.ObjectId`.
        Use this if you are using String, Binary and etc.

        For example::

            class MyModelView(BaseModelView):
                object_id_converter = int

        or::

            class MyModelView(BaseModelView):
                object_id_converter = str
    """

    filter_converter = FilterConverter()
    """
        Field to filter converter.

        Override this attribute to use a non-default converter.
    """

    column_type_formatters = DEFAULT_FORMATTERS
    """
        Customized type formatters for MongoEngine backend
    """

    allowed_search_types = (mongoengine.StringField,
                            mongoengine.URLField,
                            mongoengine.EmailField,
                            mongoengine.ReferenceField)
    """
        List of allowed search field types.
    """

    form_subdocuments = None
    """
        Subdocument configuration options.

        This field accepts dictionary, where key is field name and value is either dictionary or instance of the
        `flask_admin.contrib.mongoengine.EmbeddedForm`.

        Consider following example::

            class Comment(db.EmbeddedDocument):
                name = db.StringField(max_length=20, required=True)
                value = db.StringField(max_length=20)

            class Post(db.Document):
                text = db.StringField(max_length=30)
                data = db.EmbeddedDocumentField(Comment)

            class MyAdmin(ModelView):
                form_subdocuments = {
                    'data': {
                        'form_columns': ('name',)
                    }
                }

        In this example, `Post` model has child `Comment` subdocument. When generating form for `Comment` embedded
        document, Flask-Admin will only create `name` field.

        It is also possible to use class-based embedded document configuration::

            class CommentEmbed(EmbeddedForm):
                form_columns = ('name',)

            class MyAdmin(ModelView):
                form_subdocuments = {
                    'data': CommentEmbed()
                }

        Arbitrary depth nesting is supported::

            class SomeEmbed(EmbeddedForm):
                form_excluded_columns = ('test',)

            class CommentEmbed(EmbeddedForm):
                form_columns = ('name',)
                form_subdocuments = {
                    'inner': SomeEmbed()
                }

            class MyAdmin(ModelView):
                form_subdocuments = {
                    'data': CommentEmbed()
                }

        There's also support for forms embedded into `ListField`. All you have
        to do is to create nested rule with `None` as a name. Even though it
        is slightly confusing, but that's how Flask-MongoEngine creates
        form fields embedded into ListField::

            class Comment(db.EmbeddedDocument):
                name = db.StringField(max_length=20, required=True)
                value = db.StringField(max_length=20)

            class Post(db.Document):
                text = db.StringField(max_length=30)
                data = db.ListField(db.EmbeddedDocumentField(Comment))

            class MyAdmin(ModelView):
                form_subdocuments = {
                    'data': {
                        'form_subdocuments': {
                            None: {
                                'form_columns': ('name',)
                            }
                        }

                    }
                }
    """

    def __init__(self, model, name=None,
                 category=None, endpoint=None, url=None, static_folder=None,
                 menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
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

        super(ModelView, self).__init__(model, name, category, endpoint, url, static_folder,
                                        menu_class_name=menu_class_name,
                                        menu_icon_type=menu_icon_type,
                                        menu_icon_value=menu_icon_value)

        self._primary_key = self.scaffold_pk()

    def _refresh_cache(self):
        """
            Refresh cache.
        """
        # Process subdocuments
        if self.form_subdocuments is None:
            self.form_subdocuments = {}

        self._form_subdocuments = convert_subdocuments(self.form_subdocuments)

        # Cache other properties
        super(ModelView, self)._refresh_cache()

    def _process_ajax_references(self):
        """
            AJAX endpoint is exposed by top-level admin view class, but
            subdocuments might have AJAX references too.

            This method will recursively go over subdocument configuration
            and will precompute AJAX references for them ensuring that
            subdocuments can also use AJAX to populate their ReferenceFields.
        """
        references = super(ModelView, self)._process_ajax_references()
        return process_ajax_references(references, self)

    def _get_model_fields(self, model=None):
        """
            Inspect model and return list of model fields

            :param model:
                Model to inspect
        """
        if model is None:
            model = self.model

        return sorted(iteritems(model._fields), key=lambda n: n[1].creation_counter)

    def scaffold_pk(self):
        # MongoEngine models have predefined 'id' as a key
        return 'id'

    def get_pk_value(self, model):
        """
            Return the primary key value from the model instance

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
            Return a dictionary of sortable columns (name, field)
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
                if isinstance(p, string_types):
                    p = self.model._fields.get(p)

                if p is None:
                    raise Exception('Invalid search field')

                field_type = type(p)

                # Check type
                if (field_type not in self.allowed_search_types):
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
        if isinstance(name, string_types):
            attr = self.model._fields.get(name)
        else:
            attr = name

        if attr is None:
            raise Exception('Failed to find field for filter: %s' % name)

        # Find name
        visible_name = None

        if not isinstance(name, string_types):
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
            Validate if the provided filter is a valid MongoEngine filter

            :param filter:
                Filter object
        """
        return isinstance(filter, BaseMongoEngineFilter)

    def scaffold_form(self):
        """
            Create form from the model.
        """
        form_class = get_form(self.model,
                              self.model_form_converter(self),
                              base_class=self.form_base_class,
                              only=self.form_columns,
                              exclude=self.form_excluded_columns,
                              field_args=self.form_args,
                              extra_fields=self.form_extra_fields)

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
        form_class = get_form(self.model,
                              self.model_form_converter(self),
                              base_class=self.form_base_class,
                              only=self.column_editable_list,
                              field_args=validators)

        return create_editable_list_form(self.form_base_class, form_class,
                                         widget)

    # AJAX foreignkey support
    def _create_ajax_loader(self, name, opts):
        return create_ajax_loader(self.model, name, name, opts)

    def get_query(self):
        """
        Returns the QuerySet for this view.  By default, it returns all the
        objects for the current model.
        """
        return self.model.objects

    def _search(self, query, search_term):
        # TODO: Unfortunately, MongoEngine contains bug which
        # prevents running complex Q queries and, as a result,
        # Flask-Admin does not support per-word searching like
        # in other backends
        op, term = parse_like_term(search_term)

        criteria = None

        for field in self._search_fields:
            if type(field) == mongoengine.ReferenceField:
                import re
                regex = re.compile('.*%s.*' % term)
            else:
                regex = term
            flt = {'%s__%s' % (field.name, op): regex}
            q = mongoengine.Q(**flt)

            if criteria is None:
                criteria = q
            else:
                criteria |= q

        return query.filter(criteria)

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
                List of applied filters
            :param execute:
                Run query immediately or not
            :param page_size:
                Number of results. Defaults to ModelView's page_size. Can be
                overriden to change the page_size limit. Removing the page_size
                limit requires setting page_size to 0 or False.
        """
        query = self.get_query()

        # Filters
        if self._filters:
            for flt, flt_name, value in filters:
                f = self._filters[flt]
                query = f.apply(query, f.clean(value))

        # Search
        if self._search_supported and search:
            query = self._search(query, search)

        # Get count
        count = query.count() if not self.simple_list_pager else None

        # Sorting
        if sort_column:
            query = query.order_by('%s%s' % ('-' if sort_desc else '', sort_column))
        else:
            order = self._get_default_order()

            if order:
                keys = ['%s%s' % ('-' if desc else '', col)
                        for (col, desc) in order]
                query = query.order_by(*keys)

        # Pagination
        if page_size is None:
            page_size = self.page_size

        if page_size:
            query = query.limit(page_size)

        if page and page_size:
            query = query.skip(page * page_size)

        if execute:
            query = query.all()

        return count, query

    def get_one(self, id):
        """
            Return a single model instance by its ID

            :param id:
                Model ID
        """
        try:
            return self.get_query().filter(pk=id).first()
        except mongoengine.ValidationError as ex:
            flash(gettext('Failed to get model. %(error)s',
                          error=format_error(ex)),
                  'error')
            return None

    def create_model(self, form):
        """
            Create model helper

            :param form:
                Form instance
        """
        try:
            model = self.model()
            form.populate_obj(model)
            self._on_model_change(form, model, True)
            model.save()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s',
                              error=format_error(ex)),
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
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            model.save()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to update record. %(error)s',
                              error=format_error(ex)),
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
            self.on_model_delete(model)
            model.delete()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete record. %(error)s',
                              error=format_error(ex)),
                      'error')
                log.exception('Failed to delete record.')

            return False
        else:
            self.after_model_delete(model)

        return True

    # FileField access API
    @expose('/api/file/')
    def api_file_view(self):
        pk = request.args.get('id')
        coll = request.args.get('coll')
        db = request.args.get('db', 'default')

        if not pk or not coll or not db:
            abort(404)

        fs = gridfs.GridFS(get_db(db), coll)

        data = fs.get(self.object_id_converter(pk))
        if not data:
            abort(404)

        return Response(data.read(),
                        content_type=data.content_type,
                        headers={'Content-Length': data.length})

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

            all_ids = [self.object_id_converter(pk) for pk in ids]
            for obj in self.get_query().in_bulk(all_ids).values():
                count += self.delete_model(obj)

            flash(ngettext('Record was successfully deleted.',
                           '%(count)s records were successfully deleted.',
                           count,
                           count=count), 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete records. %(error)s', error=str(ex)),
                      'error')
