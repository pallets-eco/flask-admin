from wtforms import fields, validators

from flask.ext.admin import form
from flask.ext.admin.model.form import converts, ModelConverterBase, InlineFormAdmin

from .validators import Unique
from .fields import QuerySelectField, QuerySelectMultipleField, InlineModelFormList


class AdminModelConverter(ModelConverterBase):
    """
        SQLAlchemy model to form converter
    """
    def __init__(self, session, view):
        super(AdminModelConverter, self).__init__()

        self.session = session
        self.view = view

    def _get_label(self, name, field_args):
        if 'label' in field_args:
            return field_args['label']

        rename_columns = getattr(self.view, 'rename_columns', None)

        if rename_columns:
            return rename_columns.get(name)

        return None

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

            kwargs.update({
                'allow_blank': local_column.nullable,
                'label': self._get_label(prop.key, kwargs),
                'query_factory': lambda: self.session.query(remote_model)
            })

            if local_column.nullable:
                kwargs['validators'].append(validators.Optional())
            elif prop.direction.name != 'MANYTOMANY':
                kwargs['validators'].append(validators.Required())

            # Override field type if necessary
            override = self._get_field_override(prop.key)
            if override:
                return override(**kwargs)

            if prop.direction.name == 'MANYTOONE':
                return QuerySelectField(widget=form.ChosenSelectWidget(),
                                        **kwargs)
            elif prop.direction.name == 'ONETOMANY':
                # Skip backrefs
                if not local_column.foreign_keys and getattr(self.view, 'hide_backrefs', False):
                    return None

                return QuerySelectMultipleField(
                                widget=form.ChosenSelectWidget(multiple=True),
                                **kwargs)
            elif prop.direction.name == 'MANYTOMANY':
                return QuerySelectMultipleField(
                                widget=form.ChosenSelectWidget(multiple=True),
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

                if not column.nullable:
                    kwargs['validators'].append(validators.Required())

                # Apply label
                kwargs['label'] = self._get_label(prop.key, kwargs)

                # Figure out default value
                default = getattr(column, 'default', None)

                if default is not None:
                    callable_default = getattr(default, 'arg', None)

                    if callable_default and callable(callable_default):
                        default = callable_default(None)

                if default is not None:
                    kwargs['default'] = default

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
    def conv_String(self, field_args, **extra):
        self._string_common(field_args=field_args, **extra)
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
        return fields.DateTimeField(**field_args)

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


# Get list of fields and generate form
def get_form(model, converter,
            base_class=form.BaseForm,
            only=None, exclude=None,
            field_args=None,
            hidden_pk=False):

    # TODO: Support new 0.8 API
    if not hasattr(model, '_sa_class_manager'):
        raise TypeError('model must be a sqlalchemy mapped model')

    mapper = model._sa_class_manager.mapper
    field_args = field_args or {}

    properties = ((p.key, p) for p in mapper.iterate_properties)
    if only:
        properties = (x for x in properties if x[0] in only)
    elif exclude:
        properties = (x for x in properties if x[0] not in exclude)

    field_dict = {}
    for name, prop in properties:
        field = converter.convert(model, mapper, prop, field_args.get(name), hidden_pk)
        if field is not None:
            field_dict[name] = field

    return type(model.__name__ + 'Form', (base_class, ), field_dict)


def contribute_inline(session, model, form_class, inline_models):
    # Get mapper
    mapper = model._sa_class_manager.mapper

    # Contribute columns
    for p in inline_models:
        # Figure out
        if isinstance(p, basestring):
            info = InlineFormAdmin(p)
        elif isinstance(p, tuple):
            info = InlineFormAdmin(p[0], **p[1])
        elif isinstance(p, InlineFormAdmin):
            info = p
        else:
            raise Exception('Unknown inline model admin: %s' % repr(p))

        prop = mapper.get_property(info.field)
        if prop is None:
            raise Exception('Inline form property %s.%s was not found' % (model.__name__,
                                                                          info.field))

        if not hasattr(prop, 'direction'):
            raise Exception('Failed to convert inline admin %s - only one-to-many relations are supported' % info.field)

        if prop.direction.name != 'ONETOMANY':
            raise Exception('Failed to convert inline admin %s - only one-to-many relations are supported' % info.field)

        # Find reverse relationship (to exlude from the list)
        ignore = []

        for remote_prop in prop.mapper.iterate_properties:
            if hasattr(remote_prop, 'direction') and remote_prop.direction.name == 'MANYTOONE':
                if remote_prop.mapper.class_ == prop.parent.class_:
                    ignore.append(remote_prop.key)
                    print remote_prop.key

        if info.exclude:
            exclude = ignore + info.exclude
        else:
            exclude = ignore

        # Create field
        remote_model = prop.mapper.class_

        converter = AdminModelConverter(session, info)
        child_form = get_form(remote_model, converter,
                            only=info.include,
                            exclude=exclude,
                            hidden_pk=True)

        setattr(form_class, p, InlineModelFormList(child_form, session, remote_model))

    return form_class
