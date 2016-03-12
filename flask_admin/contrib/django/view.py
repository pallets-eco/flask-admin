# coding:utf-8
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.fields import TextField, CharField

from filters import FilterConverter, parse_like_term, DjangoDbModelsFilter
from flask_admin._compat import string_types
from flask_admin.model import BaseModelView
from form import get_form, CustomModelConverter


class ModelView(BaseModelView):

    filter_converter = FilterConverter()
    model_form_converter = CustomModelConverter

    def __init__(self, model, name=None,
                 category=None, endpoint=None, url=None, static_folder=None,
                 menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
        self._search_fields = []

        super(ModelView, self).__init__(model, name, category, endpoint, url, static_folder,
                                        menu_class_name=menu_class_name,
                                        menu_icon_type=menu_icon_type,
                                        menu_icon_value=menu_icon_value)

    def get_pk_value(self, model):
        return model.id

    def _get_list_url(self, view_args):
        """
            Generate page URL with current page, sort column and
            other parameters.
            :param view:
                View name
            :param view_args:
                ViewArgs object with page number, filters, etc.
        """
        page = view_args.page or None
        desc = 1 if view_args.sort_desc else None

        kwargs = dict(page=page, sort=view_args.sort, desc=desc, search=view_args.search)
        kwargs.update(view_args.extra_args)

        if view_args.filters:
            for i, pair in enumerate(view_args.filters):
                idx, flt_name, value = pair

                key = 'flt%d_%s' % (i, self.get_filter_arg(idx, self._filters[idx]))
                kwargs[key] = value

        return self.get_url('.index_view', **kwargs)

    def get_list(self, page, sort_column, sort_desc, search, filters, execute=True, page_size=None):
        view_args = self._get_list_extra_args()
        query = self.get_query()
        query = query.filter()

        # Filters
        if self._filters:
            for flt, flt_name, value in filters:
                f = self._filters[flt]
                query = f.apply(query, f.clean(value))

        # Search
        if self._search_supported and search:
            query = self._search(query, search)

        # Get count
        count = len(query) if not self.simple_list_pager else None

        # Sorting
        if sort_column:
            query = query.order_by('%s%s' % ('-' if sort_desc else '', sort_column))
        else:
            order = self._get_default_order()

            if order:
                query = query.order_by('%s%s' % ('-' if order[1] else '', order[0]))

        # Pagination
        if page_size is None:
            page_size = self.page_size

            # index start by 1
        page += 1

        if execute and page and page_size:
            p = Paginator(query, page_size)
            query = p.page(page).object_list

        return count, query

    def get_query(self):
        """
        Returns the QuerySet for this view.  By default, it returns all the
        objects for the current model.
        """
        return self.model.objects

    def get_one(self, id):
        """
            Return a single model instance by its ID

            :param id:
                Model ID
        """
        return self.get_query().filter(pk=id).first()

    def get_column_name(self, field):
        """
            Return a human-readable column name.

            :param field:
                Model field name.
        """
        column_labels = dict([(f.column, f.verbose_name.decode('utf-8'))
                             for f in self.model._meta.concrete_fields])
        if self.column_labels:
            self.column_labels.update(column_labels)
        else:
            self.column_labels = column_labels
        if self.column_labels and field in self.column_labels:
            return self.column_labels[field]
        else:
            return self._prettify_name(field)

    # List view

    def scaffold_list_columns(self):
        """
            Return list of the model field names. Must be implemented in
            the child class.

            Expected return format is list of tuples with field name and
            display text. For example::

                ['name', 'first_name', 'last_name']
        """
        return [field.column for field in self.model._meta.concrete_fields][1:]

    def scaffold_sortable_columns(self):
        """
            Returns dictionary of sortable columns. Must be implemented in
            the child class.

            Expected return format is a dictionary, where keys are field names and
            values are property names.
        """
        columns = {}

        return columns

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

    def is_valid_filter(self, filter):
        """
            Validate if the provided filter is a valid django filter
            :param filter:
                Filter object
        """
        return isinstance(filter, DjangoDbModelsFilter)

    def scaffold_filters(self, name):
        '''
        Return filter object(s) for the field
        :param name:
            Either field name or field instance
        '''

        if isinstance(name, string_types):
            for field in self.model._meta.fields:
                if field.attname == name:
                    attr = field
                    break
        else:
            attr = name

        if attr is None:
            raise Exception('Failed to find field for filter: %s' % name)

        # Find name
        visible_name = None
        if not isinstance(name, string_types):
            visible_name = self.get_column_name(attr.attname)

        if not visible_name:
            visible_name = self.get_column_name(name)
        # Convert filter
        type_name = type(attr).__name__
        flt = self.filter_converter.convert(type_name,
                                            attr,
                                            visible_name)

        return flt
        """
        return [DateTimeBetweenFilter(name, name)]
        """

    def init_search(self):
        if self.column_searchable_list:
            for p in self.column_searchable_list:
                if isinstance(p, string_types):
                    for v in self.model._meta.fields:
                        if v.name == p:
                            m = v
                            field_type = type(m)
                            if field_type in (CharField, TextField):
                                self._search_fields.append(m)
                            else:
                                raise Exception('Can only search on text columns. ' +
                                                'Failed to setup search for "%s"' % m)

        return bool(self._search_fields)

    def _search(self, query, search_term):

        op, term = parse_like_term(search_term)

        criteria = None

        for field in self._search_fields:
            flt = {'%s__%s' % (field.name, op): term}
            q = Q(**flt)

            if criteria is None:
                criteria = q
            else:
                criteria |= q

        return query.filter(criteria)

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
            print('Failed to create record. %s' % ex)

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
            print('Failed to update record.%s' % ex)

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
            print 'Failed to delete record.', ex

            return False
        else:
            self.after_model_delete(model)

        return True

#     def scaffold_sortable_columns(self):
#         columns = dict()
#
#         for n, f in self._get_model_fields():
#             if self.column_display_pk or type(f) != AutoField:
#                 columns[n] = f
#
#         return columns

    def _get_model_fields(self, model=None):
        if model is None:
            model = self.model

        return sorted(((v.name, v) for v in model._meta.fields))
