import typing as t

from flask_admin.contrib.sqla import form as sqla_form
from flask_admin.contrib.sqla.view import ModelView as SQLAModelView


class SQLModelModelConverter(sqla_form.AdminModelConverter):
    @staticmethod
    def _normalize_type_name(type_name: str, type_module: str) -> str:
        if type_name == "AutoString" and type_module.startswith("sqlmodel."):
            return "String"
        return type_name

    def get_converter(self, column):
        type_name = type(column.type).__name__
        type_module = type(column.type).__module__
        normalized_type_name = self._normalize_type_name(type_name, type_module)

        converter = self.converters.get(normalized_type_name)
        if converter is not None:
            return converter

        return super().get_converter(column)


class SQLModelFilterConverter:
    def __init__(self, wrapped):
        self.wrapped = wrapped

    @staticmethod
    def _normalize_type_name(type_name: str, type_module: str) -> str:
        if type_name == "AutoString" and type_module.startswith("sqlmodel."):
            return "string"
        return type_name

    def convert(self, type_name: str, column, name: str, **kwargs: t.Any):
        normalized_type_name = self._normalize_type_name(
            type_name,
            type(column.type).__module__,
        )
        return self.wrapped.convert(normalized_type_name, column, name, **kwargs)


class SQLModelView(SQLAModelView):
    model_form_converter = SQLModelModelConverter

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_converter = SQLModelFilterConverter(self.filter_converter)
        self._refresh_cache()


ModelView = SQLModelView
