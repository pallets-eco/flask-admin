import logging

from flask_admin.model import BaseModelView
from wtforms_appengine import ndb as wt_ndb

from google.cloud import ndb

from flask_wtf import FlaskForm
from flask_admin.model.form import create_editable_list_form
from .form import AdminModelConverter
from ast import literal_eval


class NdbModelView(BaseModelView):
    """
    AppEngine NDB model scaffolding.
    """

    def get_pk_value(self, model):
        return model.key.urlsafe()

    def scaffold_list_columns(self):
        return sorted([k for (k, v) in self.model.__dict__.items() if isinstance(v, ndb.Property)])

    def scaffold_sortable_columns(self):
        return [k for (k, v) in self.model.__dict__.items() if isinstance(v, ndb.Property) and v._indexed]

    def init_search(self):
        return None

    def is_valid_filter(self):
        pass

    def scaffold_filters(self):
        # TODO: implement
        pass

    form_args = None

    model_form_converter = AdminModelConverter
    """
        Model form conversion class. Use this to implement custom field conversion logic.

        For example::

            class MyModelConverter(AdminModelConverter):
                pass


            class MyAdminView(ModelView):
                model_form_converter = MyModelConverter
    """

    def scaffold_form(self):
        form_class = wt_ndb.model_form(
            self.model(),
            base_class=FlaskForm,
            only=self.form_columns,
            exclude=self.form_excluded_columns,
            field_args=self.form_args,
            converter=self.model_form_converter(),
        )
        return form_class

    def scaffold_list_form(self, widget=None, validators=None):
        form_class = wt_ndb.model_form(
            self.model(),
            base_class=FlaskForm,
            only=self.column_editable_list,
            field_args=self.form_args,
            converter=self.model_form_converter(),
        )
        result = create_editable_list_form(FlaskForm, form_class, widget)
        return result

    def get_list(self, page, sort_field, sort_desc, search, filters,
                 page_size=None):
        # TODO: implement filters (don't think search can work here)

        q = self.model.query(*filters) if filters else self.model.query()

        if sort_field:
            order_field = getattr(self.model, sort_field)
            if sort_desc:
                order_field = -order_field
            q = q.order(order_field)

        if not page_size:
            page_size = self.page_size

        results = q.fetch(page_size, offset=page * page_size)

        return q.count(), results

    def get_one(self, urlsafe_key):
        try:
            urlsafe_key = literal_eval(urlsafe_key)
        except:
            pass
        return ndb.Key(urlsafe=urlsafe_key).get()

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            model.put()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                # flash(gettext('Failed to create record. %(error)s',
                #    error=ex), 'error')
                logging.exception('Failed to create record.')
            return False
        else:
            self.after_model_change(form, model, True)

        return model

    def update_model(self, form, model):
        try:
            form.populate_obj(model)
            model.put()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                # flash(gettext('Failed to update record. %(error)s',
                #    error=ex), 'error')
                logging.exception('Failed to update record.')
            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def delete_model(self, model):
        try:
            model.key.delete()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                # flash(gettext('Failed to delete record. %(error)s',
                #    error=ex),
                #    'error')
                logging.exception('Failed to delete record.')
            return False
        else:
            self.after_model_delete(model)

        return True


def ModelView(model):
    if issubclass(model, ndb.Model):
        return NdbModelView(model)
    else:
        raise ValueError("Unsupported model: %s" % model)
