from flask.ext.mongoengine.wtf import orm

from flask.ext.admin.form import BaseForm


class CustomModelConverter(orm.ModelConverter):
    pass


def model_form(model, base_class=BaseForm, only=None, exclude=None,
               field_args=None, converter=None):
    return orm.model_form(model, base_class=base_class, only=only,
                          exclude=exclude, field_args=field_args,
                          converter=converter)
