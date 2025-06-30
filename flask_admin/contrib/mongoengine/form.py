import decimal

from bson import ObjectId
from mongoengine import ListField
from mongoengine import ReferenceField
from mongoengine.base import BaseDocument
from mongoengine.base import DocumentMetaclass
from mongoengine.base import get_document
from mongoengine.queryset import DoesNotExist
from wtforms import fields
from wtforms import validators

from flask_admin import form
from flask_admin._compat import iteritems
from flask_admin._compat import _iter_choices_wtforms_compat
from flask_admin.form.validators import FieldListInputRequired
from flask_admin.model.fields import AjaxSelectField
from flask_admin.model.fields import AjaxSelectMultipleField
from flask_admin.model.fields import InlineFieldList
from flask_admin.model.form import FieldPlaceholder

from .fields import ModelFormField
from .fields import MongoFileField
from .fields import MongoImageField
from .subdoc import EmbeddedForm


class QuerySetSelectField(fields.SelectFieldBase):
    """
    Given a QuerySet either at initialization or inside a view, will display a
    select drop-down field of choices. The `data` property actually will
    store/keep an ORM model instance, not the ID. Submitting a choice which is
    not in the queryset will result in a validation error.

    Specifying `label_attr` in the constructor will use that property of the
    model instance for display in the list, else the model object's `__str__`
    or `__unicode__` will be used.

    If `allow_blank` is set to `True`, then a blank choice will be added to the
    top of the list. Selecting this choice will result in the `data` property
    being `None`.  The label for the blank choice can be set by specifying the
    `blank_text` parameter.
    """

    widget = form.Select2Widget()

    def __init__(
        self,
        label="",
        validators=None,
        queryset=None,
        label_attr="",
        allow_blank=False,
        blank_text="---",
        label_modifier=None,
        **kwargs,
    ):
        """Init docstring placeholder."""

        super().__init__(label, validators, **kwargs)
        self.label_attr = label_attr
        self.allow_blank = allow_blank
        self.blank_text = blank_text
        self.label_modifier = label_modifier
        self.queryset = queryset

    def iter_choices(self):
        """
        Provides data for choice widget rendering. Must return a sequence or
        iterable of (value, label, selected) tuples.
        """
        if self.allow_blank:
            yield _iter_choices_wtforms_compat("__None", self.blank_text,
                                               self.data is None)

        if self.queryset is None:
            return

        self.queryset.rewind()
        for obj in self.queryset:
            label = (
                self.label_modifier(obj)
                if self.label_modifier
                else (self.label_attr and getattr(obj, self.label_attr) or obj)
            )

            if isinstance(self.data, list):
                selected = obj in self.data
            else:
                selected = self._is_selected(obj)
            yield _iter_choices_wtforms_compat(obj.id, label, selected)

    def process_formdata(self, valuelist):
        """
        Process data received over the wire from a form.

        This will be called during form construction with data supplied
        through the `formdata` argument.

        :param valuelist: A list of strings to process.
        """
        if not valuelist or valuelist[0] == "__None" or self.queryset is None:
            self.data = None
            return

        try:
            obj = self.queryset.get(pk=valuelist[0])
            self.data = obj
        except DoesNotExist:
            self.data = None

    def pre_validate(self, form):
        """
        Field-level validation. Runs before any other validators.

        :param form: The form the field belongs to.
        """
        if (not self.allow_blank or self.data is not None) and not self.data:
            raise validators.ValidationError(self.gettext("Not a valid choice"))

    def _is_selected(self, item):
        return item == self.data


class QuerySetSelectMultipleField(QuerySetSelectField):
    """Same as :class:`QuerySetSelectField` but with multiselect options."""

    widget = form.Select2Widget(multiple=True)

    def __init__(
        self,
        label="",
        validators=None,
        queryset=None,
        label_attr="",
        allow_blank=False,
        blank_text="---",
        **kwargs,
    ):
        super().__init__(
            label, validators, queryset, label_attr, allow_blank, blank_text, **kwargs
        )

    def process_formdata(self, valuelist):
        """
        Process data received over the wire from a form.

        This will be called during form construction with data supplied
        through the `formdata` argument.

        :param valuelist: A list of strings to process.
        """

        if not valuelist or valuelist[0] == "__None" or not self.queryset:
            self.data = None
            return

        self.queryset.rewind()
        self.data = list(self.queryset(pk__in=valuelist))
        if not len(self.data):
            self.data = None

    def _is_selected(self, item):
        return item in self.data if self.data else False


class ModelSelectField(QuerySetSelectField):
    """
    Like a QuerySetSelectField, except takes a model class instead of a
    queryset and lists everything in it.
    """

    def __init__(self, label="", validators=None, model=None, **kwargs):
        queryset = kwargs.pop("queryset", model.objects)
        super().__init__(label, validators, queryset=queryset, **kwargs)


class ModelSelectMultipleField(QuerySetSelectMultipleField):
    """
    Allows multiple select
    """

    def __init__(self, label="", validators=None, model=None, **kwargs):
        queryset = kwargs.pop("queryset", model.objects)
        super().__init__(label, validators, queryset=queryset, **kwargs)


class CustomModelConverter:
    """
    Customized MongoEngine form conversion class.

    Injects various Flask-Admin widgets and handles lists with
    customized InlineFieldList field.
    """

    def __init__(self, view):
        self.view = view
        self.converters = {
            "StringField": self.conv_String,
            "URLField": self.conv_URL,
            "EmailField": self.conv_Email,
            "IntField": self.conv_Int,
            "FloatField": self.conv_Float,
            "DecimalField": self.conv_Decimal,
            "BooleanField": self.conv_Boolean,
            "DateField": self.conv_Date,
            "BinaryField": self.conv_Binary,
            "DictField": self.conv_Dict,
            "SortedListField": self.conv_SortedList,
            "GeoPointField": self.conv_GeoLocation,
            "ObjectIdField": self.conv_ObjectId,
            "GenericReferenceField": self.conv_GenericReference,
            "DateTimeField": self.conv_DateTime,
            "ListField": self.conv_List,
            "EmbeddedDocumentField": self.conv_EmbeddedDocument,
            "ReferenceField": self.conv_Reference,
            "FileField": self.conv_File,
            "ImageField": self.conv_image,
        }

    def _get_field_override(self, name):
        form_overrides = getattr(self.view, "form_overrides", None)

        if form_overrides:
            return form_overrides.get(name)

        return None

    def _get_subdocument_config(self, name):
        config = getattr(self.view, "_form_subdocuments", {})

        p = config.get(name)
        if not p:
            return EmbeddedForm()

        return p

    def _convert_choices(self, choices):
        for c in choices:
            if isinstance(c, tuple):
                yield c
            else:
                yield (c, c)

    def clone_converter(self, view):
        return self.__class__(view)

    def convert(self, model, field, field_args):
        # Check if it is overridden field
        if isinstance(field, FieldPlaceholder):
            return form.recreate_field(field.field)

        kwargs = {
            "label": getattr(field, "verbose_name", None),
            "description": getattr(field, "help_text", ""),
            "validators": [],
            "filters": [],
            "default": field.default,
        }

        if field_args:
            kwargs.update(field_args)

        if kwargs["validators"]:
            # Create a copy of the list since we will be modifying it.
            kwargs["validators"] = list(kwargs["validators"])

        if field.required:
            if isinstance(field, ListField):
                kwargs["validators"].append(FieldListInputRequired())
            else:
                kwargs["validators"].append(validators.InputRequired())
        elif not isinstance(field, ListField):
            kwargs["validators"].append(validators.Optional())

        ftype = type(field).__name__

        if field.choices:
            kwargs["choices"] = list(self._convert_choices(field.choices))

            if ftype in self.converters:
                kwargs["coerce"] = self.coerce(ftype)
            if kwargs.pop("multiple", False):
                return fields.SelectMultipleField(**kwargs)
            return fields.SelectField(**kwargs)

        ftype = type(field).__name__

        if hasattr(field, "to_form_field"):
            return field.to_form_field(model, kwargs)

        override = self._get_field_override(field.name)
        if override:
            return override(**kwargs)

        if ftype in self.converters:
            return self.converters[ftype](model, field, kwargs)

    @classmethod
    def _string_common(cls, model, field, kwargs):
        if field.max_length or field.min_length:
            kwargs["validators"].append(
                validators.Length(
                    max=field.max_length or -1, min=field.min_length or -1
                )
            )

    @classmethod
    def _number_common(cls, model, field, kwargs):
        if field.max_value or field.min_value:
            kwargs["validators"].append(
                validators.NumberRange(max=field.max_value, min=field.min_value)
            )

    # Converters
    def conv_String(self, model, field, kwargs):
        if field.regex:
            kwargs["validators"].append(validators.Regexp(regex=field.regex))
        self._string_common(model, field, kwargs)
        password_field = kwargs.pop("password", False)
        textarea_field = kwargs.pop("textarea", False) or not field.max_length
        if password_field:
            return fields.PasswordField(**kwargs)
        if textarea_field:
            return fields.TextAreaField(**kwargs)
        return fields.StringField(**kwargs)

    def conv_URL(self, model, field, kwargs):
        kwargs["validators"].append(validators.URL())
        self._string_common(model, field, kwargs)
        return fields.StringField(**kwargs)

    def conv_Email(self, model, field, kwargs):
        kwargs["validators"].append(validators.Email())
        self._string_common(model, field, kwargs)
        return fields.StringField(**kwargs)

    def conv_Int(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return fields.IntegerField(**kwargs)

    def conv_Float(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return fields.FloatField(**kwargs)

    def conv_Decimal(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        kwargs["places"] = getattr(field, "precision", None)
        return fields.DecimalField(**kwargs)

    def conv_Boolean(self, model, field, kwargs):
        return fields.BooleanField(**kwargs)

    def conv_Date(self, model, field, kwargs):
        return fields.DateField(**kwargs)

    def conv_Binary(self, model, field, kwargs):
        # TODO: may be set file field that will save file`s data to MongoDB
        if field.max_bytes:
            kwargs["validators"].append(validators.Length(max=field.max_bytes))
        return fields.FileField(**kwargs)

    def conv_Dict(self, model, field, kwargs):
        return fields.TextAreaField(**kwargs)

    def conv_SortedList(self, model, field, kwargs):
        # TODO: sort functionality, may be need sortable widget
        return self.conv_List(model, field, kwargs)

    def conv_GeoLocation(self, model, field, kwargs):
        # TODO: create geo field and widget (also GoogleMaps)
        return

    def conv_ObjectId(self, model, field, kwargs):
        return

    def conv_GenericReference(self, model, field, kwargs):
        return

    # Existing converters

    def conv_DateTime(self, model, field, kwargs):
        kwargs["widget"] = form.DateTimePickerWidget()
        return fields.DateTimeField(**kwargs)

    def conv_List(self, model, field, kwargs):
        if field.field is None:
            raise ValueError(
                f'ListField "{field.name}" must have field specified for model {model}'
            )

        if isinstance(field.field, ReferenceField):
            loader = getattr(self.view, "_form_ajax_refs", {}).get(field.name)
            if loader:
                return AjaxSelectMultipleField(loader, **kwargs)

            return ModelSelectMultipleField(model=field.field.document_type, **kwargs)

        # Create converter
        view = self._get_subdocument_config(field.name)
        converter = self.clone_converter(view)

        if field.field.choices:
            kwargs["multiple"] = True
            return converter.convert(model, field.field, kwargs)

        unbound_field = converter.convert(model, field.field, {})
        return InlineFieldList(unbound_field, min_entries=0, **kwargs)

    def conv_EmbeddedDocument(self, model, field, kwargs):
        # FormField does not support validators
        kwargs["validators"] = []

        view = self._get_subdocument_config(field.name)

        form_opts = form.FormOpts(
            widget_args=getattr(view, "form_widget_args", None),
            form_rules=view._form_rules,
        )

        form_class = view.get_form()
        if form_class is None:
            converter = self.clone_converter(view)
            form_class = get_form(
                field.document_type_obj,
                converter,
                base_class=view.form_base_class or form.BaseForm,
                only=view.form_columns,
                exclude=view.form_excluded_columns,
                field_args=view.form_args,
                extra_fields=view.form_extra_fields,
            )

            form_class = view.postprocess_form(form_class)

        return ModelFormField(
            field.document_type_obj, view, form_class, form_opts=form_opts, **kwargs
        )

    def conv_Reference(self, model, field, kwargs):
        kwargs["allow_blank"] = not field.required

        loader = getattr(self.view, "_form_ajax_refs", {}).get(field.name)
        if loader:
            return AjaxSelectField(loader, **kwargs)

        return ModelSelectField(model=field.document_type, **kwargs)

    def conv_File(self, model, field, kwargs):
        return MongoFileField(**kwargs)

    def conv_image(self, model, field, kwargs):
        return MongoImageField(**kwargs)

    def coerce(self, field_type):
        coercions = {
            "IntField": int,
            "BooleanField": bool,
            "FloatField": float,
            "DecimalField": decimal.Decimal,
            "ObjectIdField": ObjectId,
        }
        return coercions.get(field_type, str)


def get_form(
    model,
    converter,
    base_class=form.BaseForm,
    only=None,
    exclude=None,
    field_args=None,
    extra_fields=None,
):
    """
    Create a wtforms Form for a given mongoengine Document schema::

        from flask_mongoengine.wtf import model_form
        from myproject.myapp.schemas import Article
        ArticleForm = model_form(Article)

    :param model:
        A mongoengine Document schema class
    :param base_class:
        Base form class to extend from. Must be a ``wtforms.Form`` subclass.
    :param only:
        An optional iterable with the property names that should be included in
        the form. Only these properties will have fields.
    :param exclude:
        An optional iterable with the property names that should be excluded
        from the form. All other properties will have fields.
    :param field_args:
        An optional dictionary of field names mapping to keyword arguments used
        to construct each field object.
    :param converter:
        A converter to generate the fields based on the model properties. If
        not set, ``ModelConverter`` is used.
    """

    if isinstance(model, str):
        model = get_document(model)

    if not isinstance(model, (BaseDocument, DocumentMetaclass)):
        raise TypeError("Model must be a mongoengine Document schema")

    field_args = field_args or {}

    # Find properties
    properties = sorted(
        ((k, v) for k, v in iteritems(model._fields)),
        key=lambda v: v[1].creation_counter,
    )

    if only:
        props = dict(properties)

        def find(name):
            if extra_fields and name in extra_fields:
                return FieldPlaceholder(extra_fields[name])

            p = props.get(name)
            if p is not None:
                return p

            raise ValueError(f"Invalid model property name {model}.{name}")

        properties = ((p, find(p)) for p in only)
    elif exclude:
        properties = (p for p in properties if p[0] not in exclude)

    # Create fields
    field_dict = {}
    for name, p in properties:
        field = converter.convert(model, p, field_args.get(name))
        if field is not None:
            field_dict[name] = field

    # Contribute extra fields
    if not only and extra_fields:
        for name, field in iteritems(extra_fields):
            field_dict[name] = form.recreate_field(field)

    field_dict["model_class"] = model
    return type(model.__name__ + "Form", (base_class,), field_dict)
