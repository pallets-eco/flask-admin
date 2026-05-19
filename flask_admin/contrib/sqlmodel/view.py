import typing as t
import uuid

from flask_admin.contrib.sqla import filters as sqla_filters
from flask_admin.contrib.sqla import form as sqla_form
from flask_admin.contrib.sqla import tools
from flask_admin.contrib.sqla._compat import _get_deprecated_session
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

    def _coerce_pk_value(self, id_value: t.Any) -> t.Any:
        primary_key = self._primary_key

        if isinstance(primary_key, tuple):
            decoded = tools.iterdecode(id_value)
            if not isinstance(decoded, tuple):
                return decoded

            values: list[t.Any] = list(decoded)
            for index, key_name in enumerate(primary_key):
                if index >= len(values):
                    break

                try:
                    column = getattr(self.model, key_name).property.columns[0]
                    python_type = column.type.python_type
                except Exception:
                    continue

                if python_type is uuid.UUID and isinstance(values[index], str):
                    values[index] = uuid.UUID(values[index])

            return tuple(values)

        value = tools.iterdecode(id_value)
        try:
            column = getattr(self.model, primary_key).property.columns[0]
            python_type = column.type.python_type
        except Exception:
            return value

        if python_type is uuid.UUID and isinstance(value, str):
            return uuid.UUID(value)

        return value

    def get_one(self, id: t.Any) -> t.Any:
        session = t.cast(t.Any, _get_deprecated_session(self.session))
        return session.get(self.model, self._coerce_pk_value(id))


ModelView = SQLModelView
