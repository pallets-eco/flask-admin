import datetime
import json
import re
import time
import typing as t
from enum import Enum

from wtforms import fields
from wtforms.form import BaseForm

from flask_admin._compat import _iter_choices_wtforms_compat
from flask_admin._compat import as_unicode
from flask_admin._compat import text_type
from flask_admin.babel import gettext

from .._types import T_ITER_CHOICES
from .._types import T_TRANSLATABLE
from .._types import T_VALIDATOR
from . import widgets as admin_widgets

"""
An understanding of WTForms's Custom Widgets is helpful for understanding this code:
https://wtforms.readthedocs.io/widgets/#custom-widgets
"""

__all__ = [
    "DateTimeField",
    "TimeField",
    "Select2Field",
    "Select2TagsField",
    "JSONField",
]


class DateTimeField(fields.DateTimeField):
    """
    Allows modifying the datetime format of a DateTimeField using form_args.
    """

    widget = admin_widgets.DateTimePickerWidget()

    def __init__(
        self,
        label: t.Optional[T_TRANSLATABLE] = None,
        validators: t.Optional[list[T_VALIDATOR]] = None,
        format: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> None:
        """
        Constructor

        :param label:
            Label
        :param validators:
            Field validators
        :param format:
            Format for text to date conversion. Defaults to '%Y-%m-%d %H:%M:%S'
        :param kwargs:
            Any additional parameters
        """
        super().__init__(label, validators, format or "%Y-%m-%d %H:%M:%S", **kwargs)


class TimeField(fields.Field):
    """
    A text field which stores a `datetime.time` object.
    Accepts time string in multiple formats: 20:10, 20:10:00, 10:00 am, 9:30pm, etc.
    """

    widget = admin_widgets.TimePickerWidget()

    def __init__(
        self,
        label: t.Optional[T_TRANSLATABLE] = None,
        validators: t.Optional[list[T_VALIDATOR]] = None,
        formats: t.Optional[t.Iterable] = None,
        default_format: t.Optional[str] = None,
        widget_format: t.Any = None,
        **kwargs: t.Any,
    ) -> None:
        """
        Constructor

        :param label:
            Label
        :param validators:
            Field validators
        :param formats:
            Supported time formats, as a enumerable.
        :param default_format:
            Default time format. Defaults to '%H:%M:%S'
        :param kwargs:
            Any additional parameters
        """
        super().__init__(label, validators, **kwargs)

        self.formats = formats or (
            "%H:%M:%S",
            "%H:%M",
            "%I:%M:%S%p",
            "%I:%M%p",
            "%I:%M:%S %p",
            "%I:%M %p",
        )

        self.default_format = default_format or "%H:%M:%S"

    def _value(self) -> str:
        if self.raw_data:
            return " ".join(self.raw_data)
        elif self.data is not None:
            return self.data.strftime(self.default_format)
        else:
            return ""

    def process_formdata(self, valuelist: t.Iterable[str]) -> None:
        if valuelist:
            date_str = " ".join(valuelist)

            if date_str.strip():
                for format in self.formats:
                    try:
                        timetuple = time.strptime(date_str, format)
                        self.data = datetime.time(
                            timetuple.tm_hour, timetuple.tm_min, timetuple.tm_sec
                        )
                        return
                    except ValueError:
                        pass

                raise ValueError(gettext("Invalid time format"))
            else:
                self.data = None


class Select2Field(fields.SelectField):
    """
    `Select2 <https://github.com/ivaynberg/select2>`_ styled select widget.

    You must include select2.js, form-x.x.x.js and select2 stylesheet for it to
    work.
    """

    widget = admin_widgets.Select2Widget()

    def __init__(
        self,
        label: t.Optional[T_TRANSLATABLE] = None,
        validators: t.Optional[list[T_VALIDATOR]] = None,
        coerce: t.Callable[[t.Any], t.Any] = text_type,
        choices: t.Union[tuple[str, ...], Enum, None] = None,
        allow_blank: bool = False,
        blank_text: t.Optional[T_TRANSLATABLE] = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(
            label,
            validators,
            coerce,
            choices,  # type: ignore[arg-type]
            **kwargs,
        )
        self.allow_blank = allow_blank
        self.blank_text = blank_text or " "

    def iter_choices(self) -> t.Iterator[T_ITER_CHOICES]:  # type: ignore[override]
        if self.allow_blank:
            yield _iter_choices_wtforms_compat(
                "__None", self.blank_text, self.data is None
            )

        for choice in self.choices:
            if isinstance(choice, tuple):
                yield _iter_choices_wtforms_compat(
                    choice[0], choice[1], self.coerce(choice[0]) == self.data
                )
            else:
                yield _iter_choices_wtforms_compat(
                    choice.value,  # type: ignore[attr-defined]
                    choice.name,  # type: ignore[attr-defined]
                    self.coerce(choice.value) == self.data,  # type: ignore[attr-defined]
                )

    def process_data(self, value: t.Any) -> None:
        if value is None:
            self.data = None
        else:
            try:
                self.data = self.coerce(value)
            except (ValueError, TypeError):
                self.data = None

    def process_formdata(self, valuelist: t.Optional[t.Sequence[str]]) -> None:
        if valuelist:
            if valuelist[0] == "__None":
                self.data = None
            else:
                try:
                    self.data = self.coerce(valuelist[0])
                except ValueError as err:
                    raise ValueError(
                        self.gettext("Invalid Choice: could not coerce")
                    ) from err

    def pre_validate(self, form: BaseForm) -> None:
        if self.allow_blank and self.data is None:
            return

        super().pre_validate(form)


class Select2TagsField(fields.StringField):
    """`Select2Tags <http://ivaynberg.github.com/select2/#tags>`_ styled text field.

    You must include select2.js, form-x.x.x.js and select2 stylesheet for it to work.
    """

    widget = admin_widgets.Select2TagsWidget()
    _strip_regex = re.compile(
        r"#\d+(?:(,)|\s$)"
    )  # e.g., 'tag#123, anothertag#425 ' => 'tag, anothertag'

    def __init__(
        self,
        label: t.Optional[T_TRANSLATABLE] = None,
        validators: t.Optional[list[T_VALIDATOR]] = None,
        save_as_list: bool = False,
        coerce: t.Callable[[t.Any], t.Any] = text_type,
        allow_duplicates: bool = False,
        **kwargs: t.Any,
    ) -> None:
        """Initialization

        :param save_as_list:
            If `True` then populate ``obj`` using list else string
        :param allow_duplicates:
            If `True` then duplicate tags are allowed in the field.
        """
        self.save_as_list = save_as_list
        self.allow_duplicates = allow_duplicates
        self.coerce = coerce

        super().__init__(label, validators, **kwargs)

    def process_formdata(self, valuelist: t.Optional[t.Sequence[str]] = None) -> None:
        if valuelist:
            entrylist = valuelist[0]
            if self.allow_duplicates and entrylist.endswith(" "):
                # This means this is an allowed duplicate (see form.js,
                # `createSearchChoice`), so its ID was modified. Hence, we need to
                # restore the original IDs.
                entrylist = re.sub(self._strip_regex, "\\1", entrylist)
            if self.save_as_list:
                self.data = [  # type: ignore[assignment]
                    self.coerce(v.strip()) for v in entrylist.split(",") if v.strip()
                ]
            else:
                self.data = self.coerce(entrylist)

    def _value(self) -> str:
        if isinstance(self.data, (list, tuple)):
            return ",".join(as_unicode(v) for v in self.data)
        elif self.data:
            return as_unicode(self.data)
        else:
            return ""


class JSONField(fields.TextAreaField):
    def _value(self) -> str:
        if self.raw_data:
            return self.raw_data[0]
        elif self.data:
            # prevent utf8 characters from being converted to ascii
            return as_unicode(json.dumps(self.data, ensure_ascii=False))
        else:
            return "{}"

    def process_formdata(self, valuelist: t.Optional[t.Sequence[str]]) -> None:
        if valuelist:
            value = valuelist[0]

            # allow saving blank field as None
            if not value:
                self.data = None
                return

            try:
                self.data = json.loads(valuelist[0])
            except ValueError as err:
                raise ValueError(self.gettext("Invalid JSON")) from err
