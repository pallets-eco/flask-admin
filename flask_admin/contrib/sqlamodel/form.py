from wtforms import fields, validators
from sqlalchemy import Boolean, Column

from flask.ext.admin import form
from flask.ext.admin.tools import get_property
from flask.ext.admin.model.form import (converts, ModelConverterBase,
                                        InlineFormAdmin, InlineModelConverterBase)

from .validators import Unique
from .fields import QuerySelectField, QuerySelectMultipleField, InlineModelFormList

try:
    # Field has better input parsing capabilities.
    from wtforms.ext.dateutil.fields import DateTimeField
except ImportError:
    from wtforms.fields import DateTimeField


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

        return self.view.prettify_name(name)

    def _get_description(self, name, field_args):
        if 'description' in field_args:
            return field_args['description']
        if self.view.column_descriptions:
            return self.view.column_descriptions.get(name)

    def _get_field_override(self, name):
        form_overrides = getattr(self.view, 'form_overrides', None)

        if form_overrides:
            return form_overrides.get(name)

        return None

    def convert(self, model, mapper, prop, field_args, hidden_pk):
        kwargs = {
            'validators': [],
            'filters': []
        }

        if field_args:
            kwargs.update(field_args)

        # Check if it is relation or property
        if hasattr(prop, 'direction'):
            remote_model = prop.mapper.class_
            local_column = prop.local_remote_pairs[0][0]

            kwargs['label'] = self._get_label(prop.key, kwargs)
            kwargs['description'] = self._get_description(prop.key, kwargs)

            if local_column.nullable:
                kwargs['validators'].append(validators.Optional())
            elif prop.direction.name != 'MANYTOMANY':
                kwargs['validators'].append(validators.Required())

            # Override field type if necessary
            override = self._get_field_override(prop.key)
            if override:
                return override(**kwargs)

            # Contribute model-related parameters
            if 'allow_blank' not in kwargs:
                kwargs['allow_blank'] = local_column.nullable,
            if 'query_factory' not in kwargs:
                kwargs['query_factory'] = lambda: self.session.query(remote_model)

            if prop.direction.name == 'MANYTOONE':
                return QuerySelectField(widget=form.Select2Widget(),
                                        **kwargs)
            elif prop.direction.name == 'ONETOMANY':
                # Skip backrefs
                if not local_column.foreign_keys and getattr(self.view, 'column_hide_backrefs', False):
                    return None

                return QuerySelectMultipleField(
                                widget=form.Select2Widget(multiple=True),
                                **kwargs)
            elif prop.direction.name == 'MANYTOMANY':
                return QuerySelectMultipleField(
                                widget=form.Select2Widget(multiple=True),
                                **kwargs)
        else:
            # Ignore pk/fk
            if hasattr(prop, 'columns'):
                # Check if more than one column mapped to the property
                if len(prop.columns) != 1:
                    raise TypeError('Can not convert multiple-column properties (%s.%s)' % (model, prop.key))

                # Grab column
                column = prop.columns[0]

                # Do not display foreign keys - use relations
                if column.foreign_keys:
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
                        form_columns = getattr(self.view, 'form_columns', None)

                        if form_columns is None:
                            return None

                        # If PK is not explicitly allowed, ignore it
                        if prop.key not in form_columns:
                            return None

                        kwargs['validators'].append(Unique(self.session,
                                                           model,
                                                           column))
                        unique = True

                # If field is unique, validate it
                if column.unique and not unique:
                    kwargs['validators'].append(Unique(self.session,
                                                       model,
                                                       column))

                if not column.nullable and not isinstance(column.type, Boolean):
                    kwargs['validators'].append(validators.Required())

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
                            value = value(None)
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
            field_args['validators'].append(validators.AnyOf(column.type.enums))
            field_args['choices'] = [(f,f) for f in column.type.enums]
            return form.Select2Field(**field_args)
        self._string_common(column=column, field_args=field_args, **extra)
        return fields.TextField(**field_args)

    @converts('Text', 'UnicodeText',
            'sqlalchemy.types.LargeBinary', 'sqlalchemy.types.Binary')
    def conv_Text(self, field_args, **extra):
        self._string_common(field_args=field_args, **extra)
        return fields.TextAreaField(**field_args)

    @converts('Boolean')
    def conv_Boolean(self, field_args, **extra):
        return fields.BooleanField(**field_args)

    @converts('Date')
    def convert_date(self, field_args, **extra):
        field_args['widget'] = form.DatePickerWidget()
        return fields.DateField(**field_args)

    @converts('DateTime')
    def convert_datetime(self, field_args, **extra):
        field_args['widget'] = form.DateTimePickerWidget()
        return DateTimeField(**field_args)

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
        return fields.TextField(**field_args)

    @converts('databases.postgres.PGInet', 'dialects.postgresql.base.INET')
    def conv_PGInet(self, field_args, **extra):
        field_args.setdefault('label', u'IP Address')
        field_args['validators'].append(validators.IPAddress())
        return fields.TextField(**field_args)

    @converts('dialects.postgresql.base.MACADDR')
    def conv_PGMacaddr(self, field_args, **extra):
        field_args.setdefault('label', u'MAC Address')
        field_args['validators'].append(validators.MacAddress())
        return fields.TextField(**field_args)

    @converts('dialects.postgresql.base.UUID')
    def conv_PGUuid(self, field_args, **extra):
        field_args.setdefault('label', u'UUID')
        field_args['validators'].append(validators.UUID())
        return fields.TextField(**field_args)

    @converts('sqlalchemy.dialects.postgresql.base.ARRAY')
    def conv_ARRAY(self, field_args, **extra):
        return form.Select2TagsField(save_as_list=True, **field_args)


# Get list of fields and generate form
def get_form(model, converter,
            base_class=form.BaseForm,
            only=None, exclude=None,
            field_args=None,
            hidden_pk=False,
            ignore_hidden=True):
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
            # Try to look it up in properties list first
            p = props.get(name)
            if p is not None:
                # Try to see if it is proxied property
                if hasattr(p, '_proxied_property'):
                    return p._proxied_property

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
    for name, prop in properties:
        # Ignore protected properties
        if ignore_hidden and name.startswith('_'):
            continue

        field = converter.convert(model, mapper, prop, field_args.get(name), hidden_pk)
        if field is not None:
            field_dict[name] = field

    return type(model.__name__ + 'Form', (base_class, ), field_dict)


class InlineModelConverter(InlineModelConverterBase):
    """
        Inline model form helper.
    """
    def __init__(self, session, view):
        super(InlineModelConverter, self).__init__(view)
        self.session = session

    def get_info(self, p):
        info = super(InlineModelConverter, self).get_info(p)

        # Special case for model instances
        if info is None:
            if hasattr(p, '_sa_class_manager'):
                return InlineFormAdmin(p)
            else:
                model = getattr(p, 'model', None)

                if model is None:
                    raise Exception('Unknown inline model admin: %s' % repr(p))

                attrs = dict()
                for attr in dir(p):
                    if not attr.startswith('_') and attr != 'model':
                        attrs[attr] = getattr(p, attr)

                return InlineFormAdmin(model, **attrs)

            info = InlineFormAdmin(model, **attrs)

        return info

    def contribute(self, converter, model, form_class, inline_model):
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
            if hasattr(prop, 'direction') and prop.direction.name == 'MANYTOONE':
                if prop.mapper.class_ == model:
                    reverse_prop = prop
                    break
        else:
            raise Exception('Cannot find reverse relation for model %s' % info.model)

        # Find forward property
        forward_prop = None

        for prop in mapper.iterate_properties:
            if hasattr(prop, 'direction') and prop.direction.name == 'ONETOMANY':
                if prop.mapper.class_ == target_mapper.class_:
                    forward_prop = prop
                    break
        else:
            raise Exception('Cannot find forward relation for model %s' % info.model)

        # Remove reverse property from the list
        ignore = [reverse_prop.key]

        if info.form_excluded_columns:
            exclude = ignore + info.form_excluded_columns
        else:
            exclude = ignore

        # Create form
        child_form = get_form(info.model,
                            converter,
                            only=info.form_columns,
                            exclude=exclude,
                            field_args=info.form_args,
                            hidden_pk=True)

        # Post-process form
        child_form = info.postprocess_form(child_form)

        kwargs = dict()

        label = self.get_label(info, forward_prop.key)
        if label:
            kwargs['label'] = label

        # Contribute field
        setattr(form_class,
                forward_prop.key,
                InlineModelFormList(child_form,
                                    self.session,
                                    info.model,
                                    forward_prop.key,
                                    **kwargs))

        return form_class
