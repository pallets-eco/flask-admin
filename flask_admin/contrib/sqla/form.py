import warnings

from wtforms import fields, validators
from sqlalchemy import Boolean, Column

from flask_admin import form
from flask_admin.model.form import (converts, ModelConverterBase,
                                    InlineModelConverterBase, FieldPlaceholder)
from flask_admin.model.fields import AjaxSelectField, AjaxSelectMultipleField
from flask_admin.model.helpers import prettify_name
from flask_admin._backwards import get_property
from flask_admin._compat import iteritems

from .validators import Unique
from .fields import QuerySelectField, QuerySelectMultipleField, InlineModelFormList
from .tools import has_multiple_pks, filter_foreign_columns
from .ajax import create_ajax_loader


class AdminModelConverter(ModelConverterBase):
    """
        SQLAlchemy model to form converter
    """
    def __init__(self, session, view):
        super(AdminModelConverter, self).__init__()

        self.session = session
        self.view = view

    def _get_label(self, name, field_args):
        """
            Label for field name. If it is not specified explicitly,
            then the views prettify_name method is used to find it.

            :param field_args:
                Dictionary with additional field arguments
        """
        if 'label' in field_args:
            return field_args['label']

        column_labels = get_property(self.view, 'column_labels', 'rename_columns')

        if column_labels:
            return column_labels.get(name)

        prettify_override = getattr(self.view, 'prettify_name', None)
        if prettify_override:
            return prettify_override(name)

        return prettify_name(name)

    def _get_description(self, name, field_args):
        if 'description' in field_args:
            return field_args['description']

        column_descriptions = getattr(self.view, 'column_descriptions', None)

        if column_descriptions:
            return column_descriptions.get(name)

    def _get_field_override(self, name):
        form_overrides = getattr(self.view, 'form_overrides', None)

        if form_overrides:
            return form_overrides.get(name)

        return None

    def _model_select_field(self, prop, multiple, remote_model, **kwargs):
        loader = getattr(self.view, '_form_ajax_refs', {}).get(prop.key)

        if loader:
            if multiple:
                return AjaxSelectMultipleField(loader, **kwargs)
            else:
                return AjaxSelectField(loader, **kwargs)

        if 'query_factory' not in kwargs:
            kwargs['query_factory'] = lambda: self.session.query(remote_model)

        if 'widget' not in kwargs:
            if multiple:
                kwargs['widget'] = form.Select2Widget(multiple=True)
            else:
                kwargs['widget'] = form.Select2Widget()

        if multiple:
            return QuerySelectMultipleField(**kwargs)
        else:
            return QuerySelectField(**kwargs)

    def _convert_relation(self, prop, kwargs):
        # Check if relation is specified
        form_columns = getattr(self.view, 'form_columns', None)
        if form_columns and prop.key not in form_columns:
            return None

        remote_model = prop.mapper.class_
        column = prop.local_remote_pairs[0][0]

        # If this relation points to local column that's not foreign key, assume
        # that it is backref and use remote column data
        if not column.foreign_keys:
            column = prop.local_remote_pairs[0][1]

        kwargs['label'] = self._get_label(prop.key, kwargs)
        kwargs['description'] = self._get_description(prop.key, kwargs)

        # determine optional/required, or respect existing
        requirement_options = (validators.Optional, validators.InputRequired)
        if not any(isinstance(v, requirement_options) for v in kwargs['validators']):
            if column.nullable or prop.direction.name != 'MANYTOONE':
                kwargs['validators'].append(validators.Optional())
            else:
                kwargs['validators'].append(validators.InputRequired())

        # Contribute model-related parameters
        if 'allow_blank' not in kwargs:
            kwargs['allow_blank'] = column.nullable

        # Override field type if necessary
        override = self._get_field_override(prop.key)
        if override:
            return override(**kwargs)

        if prop.direction.name == 'MANYTOONE' or not prop.uselist:
            return self._model_select_field(prop, False, remote_model, **kwargs)
        elif prop.direction.name == 'ONETOMANY':
            return self._model_select_field(prop, True, remote_model, **kwargs)
        elif prop.direction.name == 'MANYTOMANY':
            return self._model_select_field(prop, True, remote_model, **kwargs)

    def convert(self, model, mapper, prop, field_args, hidden_pk):
        # Properly handle forced fields
        if isinstance(prop, FieldPlaceholder):
            return form.recreate_field(prop.field)

        kwargs = {
            'validators': [],
            'filters': []
        }

        if field_args:
            kwargs.update(field_args)

        if kwargs['validators']:
            # Create a copy of the list since we will be modifying it.
            kwargs['validators'] = list(kwargs['validators'])

        # Check if it is relation or property
        if hasattr(prop, 'direction'):
            return self._convert_relation(prop, kwargs)
        else:
            # Ignore pk/fk
            if hasattr(prop, 'columns'):
                # Check if more than one column mapped to the property
                if len(prop.columns) > 1:
                    columns = filter_foreign_columns(model.__table__, prop.columns)

                    if len(columns) > 1:
                        warnings.warn('Can not convert multiple-column properties (%s.%s)' % (model, prop.key))
                        return None

                    column = columns[0]
                else:
                    # Grab column
                    column = prop.columns[0]

                form_columns = getattr(self.view, 'form_columns', None) or ()

                # Do not display foreign keys - use relations, except when explicitly instructed
                if column.foreign_keys and prop.key not in form_columns:
                    return None

                # Only display "real" columns
                if not isinstance(column, Column):
                    return None

                unique = False

                if column.primary_key:
                    if hidden_pk:
                        # If requested to add hidden field, show it
                        return fields.HiddenField()
                    else:
                        # By default, don't show primary keys either
                        # If PK is not explicitly allowed, ignore it
                        if prop.key not in form_columns:
                            return None

                        # Current Unique Validator does not work with multicolumns-pks
                        if not has_multiple_pks(model):
                            kwargs['validators'].append(Unique(self.session,
                                                               model,
                                                               column))
                            unique = True

                # If field is unique, validate it
                if column.unique and not unique:
                    kwargs['validators'].append(Unique(self.session,
                                                       model,
                                                       column))

                optional_types = getattr(self.view, 'form_optional_types', (Boolean,))

                if (
                    not column.nullable
                    and not isinstance(column.type, optional_types)
                    and not column.default
                    and not column.server_default
                ):
                    kwargs['validators'].append(validators.InputRequired())

                # Apply label and description if it isn't inline form field
                if self.view.model == mapper.class_:
                    kwargs['label'] = self._get_label(prop.key, kwargs)
                    kwargs['description'] = self._get_description(prop.key, kwargs)

                # Figure out default value
                default = getattr(column, 'default', None)
                value = None

                if default is not None:
                    value = getattr(default, 'arg', None)

                    if value is not None:
                        if getattr(default, 'is_callable', False):
                            value = lambda: default.arg(None)
                        else:
                            if not getattr(default, 'is_scalar', True):
                                value = None

                if value is not None:
                    kwargs['default'] = value

                # Check nullable
                if column.nullable:
                    kwargs['validators'].append(validators.Optional())

                # Override field type if necessary
                override = self._get_field_override(prop.key)
                if override:
                    return override(**kwargs)

                # Check choices
                form_choices = getattr(self.view, 'form_choices', None)

                if mapper.class_ == self.view.model and form_choices:
                    choices = form_choices.get(column.key)
                    if choices:
                        return form.Select2Field(
                            choices=choices,
                            allow_blank=column.nullable,
                            **kwargs
                        )

                # Run converter
                converter = self.get_converter(column)

                if converter is None:
                    return None

                return converter(model=model, mapper=mapper, prop=prop,
                                 column=column, field_args=kwargs)

        return None

    @classmethod
    def _string_common(cls, column, field_args, **extra):
        if column.type.length:
            field_args['validators'].append(validators.Length(max=column.type.length))

    @converts('String', 'Unicode')
    def conv_String(self, column, field_args, **extra):
        if hasattr(column.type, 'enums'):
            accepted_values = list(column.type.enums)

            field_args['choices'] = [(f, f) for f in column.type.enums]

            if column.nullable:
                field_args['allow_blank'] = column.nullable
                accepted_values.append(None)

            field_args['validators'].append(validators.AnyOf(accepted_values))

            return form.Select2Field(**field_args)

        if column.nullable:
            filters = field_args.get('filters', [])
            filters.append(lambda x: x or None)
            field_args['filters'] = filters

        self._string_common(column=column, field_args=field_args, **extra)
        return fields.StringField(**field_args)

    @converts('Text', 'UnicodeText',
              'sqlalchemy.types.LargeBinary', 'sqlalchemy.types.Binary')
    def conv_Text(self, field_args, **extra):
        self._string_common(field_args=field_args, **extra)
        return fields.TextAreaField(**field_args)

    @converts('Boolean', 'sqlalchemy.dialects.mssql.base.BIT')
    def conv_Boolean(self, field_args, **extra):
        return fields.BooleanField(**field_args)

    @converts('Date')
    def convert_date(self, field_args, **extra):
        field_args['widget'] = form.DatePickerWidget()
        return fields.DateField(**field_args)

    @converts('DateTime')
    def convert_datetime(self, field_args, **extra):
        return form.DateTimeField(**field_args)

    @converts('Time')
    def convert_time(self, field_args, **extra):
        return form.TimeField(**field_args)

    @converts('Integer', 'SmallInteger')
    def handle_integer_types(self, column, field_args, **extra):
        unsigned = getattr(column.type, 'unsigned', False)
        if unsigned:
            field_args['validators'].append(validators.NumberRange(min=0))
        return fields.IntegerField(**field_args)

    @converts('Numeric', 'Float')
    def handle_decimal_types(self, column, field_args, **extra):
        places = getattr(column.type, 'scale', 2)
        if places is not None:
            field_args['places'] = places
        return fields.DecimalField(**field_args)

    @converts('databases.mysql.MSYear')
    def conv_MSYear(self, field_args, **extra):
        field_args['validators'].append(validators.NumberRange(min=1901, max=2155))
        return fields.StringField(**field_args)

    @converts('sqlalchemy.dialects.postgresql.base.INET',
              'databases.postgres.PGInet', 'dialects.postgresql.base.INET')
    def conv_PGInet(self, field_args, **extra):
        field_args.setdefault('label', u'IP Address')
        field_args['validators'].append(validators.IPAddress())
        return fields.StringField(**field_args)

    @converts('sqlalchemy.dialects.postgresql.base.MACADDR',
              'dialects.postgresql.base.MACADDR')
    def conv_PGMacaddr(self, field_args, **extra):
        field_args.setdefault('label', u'MAC Address')
        field_args['validators'].append(validators.MacAddress())
        return fields.StringField(**field_args)

    @converts('dialects.postgresql.base.UUID')
    def conv_PGUuid(self, field_args, **extra):
        field_args.setdefault('label', u'UUID')
        field_args['validators'].append(validators.UUID())
        return fields.StringField(**field_args)

    @converts('sqlalchemy.dialects.postgresql.base.ARRAY')
    def conv_ARRAY(self, field_args, **extra):
        return form.Select2TagsField(save_as_list=True, **field_args)


def _resolve_prop(prop):
    """
        Resolve proxied property

        :param prop:
            Property to resolve
    """
    # Try to see if it is proxied property
    if hasattr(prop, '_proxied_property'):
        return prop._proxied_property

    return prop


# Get list of fields and generate form
def get_form(model, converter,
             base_class=form.BaseForm,
             only=None,
             exclude=None,
             field_args=None,
             hidden_pk=False,
             ignore_hidden=True,
             extra_fields=None):
    """
        Generate form from the model.

        :param model:
            Model to generate form from
        :param converter:
            Converter class to use
        :param base_class:
            Base form class
        :param only:
            Include fields
        :param exclude:
            Exclude fields
        :param field_args:
            Dictionary with additional field arguments
        :param hidden_pk:
            Generate hidden field with model primary key or not
        :param ignore_hidden:
            If set to True (default), will ignore properties that start with underscore
    """

    # TODO: Support new 0.8 API
    if not hasattr(model, '_sa_class_manager'):
        raise TypeError('model must be a sqlalchemy mapped model')

    mapper = model._sa_class_manager.mapper
    field_args = field_args or {}

    properties = ((p.key, p) for p in mapper.iterate_properties)

    if only:
        props = dict(properties)

        def find(name):
            # If field is in extra_fields, it has higher priority
            if extra_fields and name in extra_fields:
                return FieldPlaceholder(extra_fields[name])

            # Try to look it up in properties list first
            p = props.get(name)

            if p is not None:
                return p

            # If it is hybrid property or alias, look it up in a model itself
            p = getattr(model, name, None)
            if p is not None and hasattr(p, 'property'):
                return p.property

            raise ValueError('Invalid model property name %s.%s' % (model, name))

        # Filter properties while maintaining property order in 'only' list
        properties = ((x, find(x)) for x in only)
    elif exclude:
        properties = (x for x in properties if x[0] not in exclude)

    field_dict = {}
    for name, p in properties:
        # Ignore protected properties
        if ignore_hidden and name.startswith('_'):
            continue

        prop = _resolve_prop(p)

        field = converter.convert(model, mapper, prop, field_args.get(name), hidden_pk)
        if field is not None:
            field_dict[name] = field

    # Contribute extra fields
    if not only and extra_fields:
        for name, field in iteritems(extra_fields):
            field_dict[name] = form.recreate_field(field)

    return type(model.__name__ + 'Form', (base_class, ), field_dict)


class InlineModelConverter(InlineModelConverterBase):
    """
        Inline model form helper.
    """

    inline_field_list_type = InlineModelFormList
    """
        Used field list type.

        If you want to do some custom rendering of inline field lists,
        you can create your own wtforms field and use it instead
    """

    def __init__(self, session, view, model_converter):
        """
            Constructor.

            :param session:
                SQLAlchemy session
            :param view:
                Flask-Admin view object
            :param model_converter:
                Model converter class. Will be automatically instantiated with
                appropriate `InlineFormAdmin` instance.
        """
        super(InlineModelConverter, self).__init__(view)
        self.session = session
        self.model_converter = model_converter

    def get_info(self, p):
        info = super(InlineModelConverter, self).get_info(p)

        # Special case for model instances
        if info is None:
            if hasattr(p, '_sa_class_manager'):
                return self.form_admin_class(p)
            else:
                model = getattr(p, 'model', None)

                if model is None:
                    raise Exception('Unknown inline model admin: %s' % repr(p))

                attrs = dict()
                for attr in dir(p):
                    if not attr.startswith('_') and attr != 'model':
                        attrs[attr] = getattr(p, attr)

                return self.form_admin_class(model, **attrs)

            info = self.form_admin_class(model, **attrs)

        # Resolve AJAX FKs
        info._form_ajax_refs = self.process_ajax_refs(info)

        return info

    def process_ajax_refs(self, info):
        refs = getattr(info, 'form_ajax_refs', None)

        result = {}

        if refs:
            for name, opts in iteritems(refs):
                new_name = '%s-%s' % (info.model.__name__.lower(), name)

                loader = None
                if isinstance(opts, dict):
                    loader = create_ajax_loader(info.model, self.session, new_name, name, opts)
                else:
                    loader = opts

                result[name] = loader
                self.view._form_ajax_refs[new_name] = loader

        return result

    def contribute(self, model, form_class, inline_model):
        """
            Generate form fields for inline forms and contribute them to
            the `form_class`

            :param converter:
                ModelConverterBase instance
            :param session:
                SQLAlchemy session
            :param model:
                Model class
            :param form_class:
                Form to add properties to
            :param inline_model:
                Inline model. Can be one of:

                 - ``tuple``, first value is related model instance,
                 second is dictionary with options
                 - ``InlineFormAdmin`` instance
                 - Model class

            :return:
                Form class
        """

        mapper = model._sa_class_manager.mapper
        info = self.get_info(inline_model)

        # Find property from target model to current model
        target_mapper = info.model._sa_class_manager.mapper

        reverse_prop = None

        for prop in target_mapper.iterate_properties:
            if hasattr(prop, 'direction') and prop.direction.name in ('MANYTOONE', 'MANYTOMANY'):
                if issubclass(model, prop.mapper.class_):
                    reverse_prop = prop
                    break
        else:
            raise Exception('Cannot find reverse relation for model %s' % info.model)

        # Find forward property
        forward_prop = None

        if prop.direction.name == 'MANYTOONE':
            candidate = 'ONETOMANY'
        else:
            candidate = 'MANYTOMANY'

        for prop in mapper.iterate_properties:
            if hasattr(prop, 'direction') and prop.direction.name == candidate:
                if prop.mapper.class_ == target_mapper.class_:
                    forward_prop = prop
                    break
        else:
            raise Exception('Cannot find forward relation for model %s' % info.model)

        # Remove reverse property from the list
        ignore = [reverse_prop.key]

        if info.form_excluded_columns:
            exclude = ignore + list(info.form_excluded_columns)
        else:
            exclude = ignore

        # Create converter
        converter = self.model_converter(self.session, info)

        # Create form
        child_form = info.get_form()

        if child_form is None:
            child_form = get_form(info.model,
                                  converter,
                                  only=info.form_columns,
                                  exclude=exclude,
                                  field_args=info.form_args,
                                  hidden_pk=True,
                                  extra_fields=info.form_extra_fields)

        # Post-process form
        child_form = info.postprocess_form(child_form)

        kwargs = dict()

        label = self.get_label(info, forward_prop.key)
        if label:
            kwargs['label'] = label

        if self.view.form_args:
            field_args = self.view.form_args.get(forward_prop.key, {})
            kwargs.update(**field_args)

        # Contribute field
        setattr(form_class,
                forward_prop.key,
                self.inline_field_list_type(child_form,
                                            self.session,
                                            info.model,
                                            reverse_prop.key,
                                            info,
                                            **kwargs))

        return form_class
