import typing as t

from flask_admin.contrib.sqla import filters as sqla_filters
from flask_admin.contrib.sqla import form as sqla_form
from flask_admin.contrib.sqla.view import ModelView as SQLAModelView


class SQLModelModelConverter(sqla_form.AdminModelConverter):
    @staticmethod
    def _normalize_type_name(type_name: str, type_module: str) -> str:
        if type_name == "AutoString" and type_module.startswith("sqlmodel."):
            return "String"
        return type_name

    def get_converter(self, column: t.Any) -> t.Any:
        type_name = type(column.type).__name__
        type_module = type(column.type).__module__
        normalized_type_name = self._normalize_type_name(type_name, type_module)

        converter = self.converters.get(normalized_type_name)
        if converter is not None:
            return converter

        return super().get_converter(column)


class SQLModelFilterConverter(sqla_filters.FilterConverter):
    @staticmethod
    def _normalize_type_name(type_name: str, type_module: str) -> str:
        if type_name == "AutoString" and type_module.startswith("sqlmodel."):
            return "string"
        return type_name

    def convert(
        self,
        type_name: str,
        column: t.Any,
        name: str,
        **kwargs: t.Any,
    ) -> t.Any:
        normalized_type_name = self._normalize_type_name(
            type_name,
            type(column.type).__module__,
        )
        return super().convert(normalized_type_name, column, name, **kwargs)


class SQLModelView(SQLAModelView):
    model_form_converter = SQLModelModelConverter
    filter_converter: sqla_filters.FilterConverter = SQLModelFilterConverter()


ModelView = SQLModelView
