import json
from enum import Enum

import pytest
import wtforms
import wtforms.fields
from bs4 import BeautifulSoup
from flask import Flask
from werkzeug.datastructures import MultiDict

from flask_admin.babel import lazy_gettext
from flask_admin.form import BaseForm
from flask_admin.form import Select2Field
from flask_admin.model.widgets import XEditableWidget

_WTFORMS_VERSION = tuple(int(part) for part in wtforms.__version__.split(".")[:2])


class _Color(Enum):
    RED = "red"
    BLUE = "blue"


def test_select2_field_renders_and_validates_tuple_choices(
    app: Flask, babel: object | None
) -> None:
    class ChoiceForm(BaseForm):
        tuples = Select2Field(
            choices=[("draft", "Draft"), ("published", "Published")],
            allow_blank=True,
        )

    with app.test_request_context():
        form = ChoiceForm(MultiDict([("tuples", "published")]))
        assert form.validate()
        assert form.tuples.data == "published"

        select_choice_cls = getattr(wtforms.fields, "SelectChoice", None)
        if select_choice_cls is not None:
            assert form.tuples.choices is not None
            assert all(isinstance(c, select_choice_cls) for c in form.tuples.choices)

        choice_cls = getattr(wtforms.fields, "Choice", None)
        iterated = list(form.tuples.iter_choices())
        if choice_cls is not None:
            assert all(isinstance(c, choice_cls) for c in iterated)

        tuples_html = str(form.tuples())
        assert 'value="__None"' in tuples_html
        assert 'value="published"' in tuples_html
        assert "Published" in tuples_html


@pytest.mark.skipif(
    _WTFORMS_VERSION < (3, 0),
    reason="Enum choices require WTForms >= 3.0",
)
def test_select2_field_enum_choices(app: Flask, babel: object | None) -> None:
    class EnumForm(BaseForm):
        enum_list = Select2Field(choices=list(_Color))

    with app.test_request_context():
        form = EnumForm(MultiDict([("enum_list", "blue")]))
        assert form.validate()
        assert form.enum_list.data == "blue"

        enum_html = str(form.enum_list())
        assert 'value="blue"' in enum_html
        assert "BLUE" in enum_html


@pytest.mark.skipif(
    _WTFORMS_VERSION < (3, 1),
    reason="dict optgroup choices require WTForms >= 3.1",
)
def test_select2_field_dict_optgroups(app: Flask, babel: object | None) -> None:
    class GroupedForm(BaseForm):
        grouped = Select2Field(
            choices={"Primary": [("r", "Red")], "Other": [("g", "Green")]}
        )

    with app.test_request_context():
        form = GroupedForm(MultiDict([("grouped", "r")]))
        assert form.validate()
        assert form.grouped.data == "r"

        html = str(form.grouped())
        assert 'value="r"' in html
        assert "Red" in html


@pytest.mark.skipif(
    _WTFORMS_VERSION < (3, 2),
    reason="3-tuple render_kw and callable choices require WTForms >= 3.2",
)
def test_select2_field_render_kw_and_callable_choices(
    app: Flask, babel: object | None
) -> None:
    class AdvancedChoiceForm(BaseForm):
        with_kw = Select2Field(
            choices=[("a", "Alpha", {"disabled": True}), ("b", "Beta")]
        )
        dynamic = Select2Field(choices=lambda: [("x", "X"), ("y", "Y")])

    with app.test_request_context():
        form = AdvancedChoiceForm(MultiDict([("with_kw", "b"), ("dynamic", "x")]))
        assert form.validate()
        assert form.with_kw.data == "b"
        assert form.dynamic.data == "x"
        assert "disabled" in str(form.with_kw())
        assert 'value="x"' in str(form.dynamic())


@pytest.mark.skipif(
    _WTFORMS_VERSION < (3, 3),
    reason="shorthand dict choices require WTForms >= 3.3",
)
def test_select2_field_shorthand_dict_lazy_labels(
    app: Flask, babel: object | None
) -> None:
    class ShorthandForm(BaseForm):
        status = Select2Field(
            choices={"a": lazy_gettext("Alpha"), "b": lazy_gettext("Beta")}
        )

    with app.test_request_context():
        form = ShorthandForm(MultiDict([("status", "a")]))
        assert form.validate()
        assert form.status.data == "a"
        assert "Alpha" in str(form.status())


def test_xeditable_widget_renders_select2_choices(
    app: Flask, babel: object | None
) -> None:
    widget = XEditableWidget()

    class EditableForm(BaseForm):
        status = Select2Field(
            choices=[("draft", "Draft"), ("published", "Published")],
            allow_blank=True,
            widget=widget,
        )
        color = Select2Field(
            choices=list(_Color),
            widget=widget,
        )

    with app.test_request_context():
        form = EditableForm()

        status_soup = BeautifulSoup(
            str(form.status(pk=1, display_value="Draft")), "html.parser"
        )
        status_link = status_soup.find("a")
        assert status_link is not None
        status_source = json.loads(str(status_link["data-source"]))
        assert status_source == [
            {"value": "__None", "text": ""},
            {"value": "draft", "text": "Draft"},
            {"value": "published", "text": "Published"},
        ]

        color_soup = BeautifulSoup(
            str(form.color(pk=1, display_value="RED")), "html.parser"
        )
        color_link = color_soup.find("a")
        assert color_link is not None
        color_source = json.loads(str(color_link["data-source"]))
        assert color_source == [
            {"value": "red", "text": "RED"},
            {"value": "blue", "text": "BLUE"},
        ]
