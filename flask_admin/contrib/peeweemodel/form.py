from wtforms import fields

from peewee import DateTimeField, DateField, TimeField

from wtfpeewee.orm import ModelConverter

from flask.ext.admin import form


class CustomModelConverter(ModelConverter):
    def __init__(self, additional=None):
        super(CustomModelConverter, self).__init__(additional)
        self.converters[DateTimeField] = self.handle_datetime
        self.converters[DateField] = self.handle_date
        self.converters[TimeField] = self.handle_time

    def handle_date(self, model, field, **kwargs):
        kwargs['widget'] = form.DatePickerWidget()
        return field.name, fields.DateField(**kwargs)

    def handle_datetime(self, model, field, **kwargs):
        kwargs['widget'] = form.DateTimePickerWidget()
        return field.name, fields.DateTimeField(**kwargs)

    def handle_time(self, model, field, **kwargs):
        return field.name, form.TimeField(**kwargs)
