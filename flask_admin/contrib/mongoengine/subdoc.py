import typing as t

from flask_admin._compat import iteritems
from flask_admin.model.form import InlineBaseFormAdmin


class EmbeddedForm(InlineBaseFormAdmin):
    def __init__(self, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)

        self._form_subdocuments = convert_subdocuments(
            getattr(self, "form_subdocuments", {})
        )


def convert_subdocuments(values: dict[t.Any, t.Any]) -> dict[t.Any, t.Any]:
    result = {}

    for name, p in iteritems(values):
        if isinstance(p, dict):
            result[name] = EmbeddedForm(**p)
        elif isinstance(p, EmbeddedForm):
            result[name] = p
        else:
            raise ValueError(
                "Invalid subdocument type: expecting dict or "
                f"instance of flask_admin.contrib.mongoengine.EmbeddedForm, got {p}"
            )

    return result
