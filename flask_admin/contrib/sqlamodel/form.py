from sqlalchemy.orm.exc import NoResultFound

from wtforms import ValidationError, fields, validators
from wtforms.ext.sqlalchemy.orm import converts, ModelConverter
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

from flask.ext.admin import form


class Unique(object):
    """Checks field value unicity against specified table field.

    :param get_session:
        A function that return a SQAlchemy Session.
    :param model:
        The model to check unicity against.
    :param column:
        The unique column.
    :param message:
        The error message.
    """
    field_flags = ('unique', )

    def __init__(self, db_session, model, column, message=None):
        self.db_session = db_session
        self.model = model
        self.column = column
        self.message = message

    def __call__(self, form, field):
        try:
            obj = (self.db_session.query(self.model)
                       .filter(self.column == field.data).one())

            if not hasattr(form, '_obj') or not form._obj == obj:
                if self.message is None:
                    self.message = field.gettext(u'Already exists.')
                raise ValidationError(self.message)
        except NoResultFound:
            pass


class AdminModelConverter(ModelConverter):
    """
        SQLAlchemy model to form converter
    """
    def __init__(self, view):
        super(AdminModelConverter, self).__init__()

        self.view = view

    def _get_label(self, name, field_args):
        if 'label' in field_args:
            return field_args['label']

        if self.view.rename_columns:
            return self.view.rename_columns.get(name)

        return None

    def _get_field_override(self, name):
        if self.view.form_overrides:
            return self.view.form_overrides.get(name)

        return None

    def convert(self, model, mapper, prop, field_args, *args):
        kwargs = {
            'validators': [],
            'filters': []
        }

        if field_args:
            kwargs.update(field_args)

        if hasattr(prop, 'direction'):
            remote_model = prop.mapper.class_
            local_column = prop.local_remote_pairs[0][0]

            kwargs.update({
                'allow_blank': local_column.nullable,
                'label': self._get_label(prop.key, kwargs),
                'query_factory': lambda: self.view.session.query(remote_model)
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
                if not local_column.foreign_keys and self.view.hide_backrefs:
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
                column = prop.columns[0]

                # Do not display foreign keys - use relations
                if column.foreign_keys:
                    return None

                unique = False

                if column.primary_key:
                    # By default, don't show primary keys either
                    if self.view.form_columns is None:
                        return None

                    # If PK is not explicitly allowed, ignore it
                    if prop.key not in self.view.form_columns:
                        return None

                    kwargs['validators'].append(Unique(self.view.session,
                                                       model,
                                                       column))
                    unique = True

                # If field is unique, validate it
                if column.unique and not unique:
                    kwargs['validators'].append(Unique(self.view.session,
                                                       model,
                                                       column))

                if not column.nullable:
                    kwargs['validators'].append(validators.Required())

            # Apply label
            kwargs['label'] = self._get_label(prop.key, kwargs)

            # Override field type if necessary
            override = self._get_field_override(prop.key)
            if override:
                return override(**kwargs)

            return super(AdminModelConverter, self).convert(model,
                                                            mapper,
                                                            prop,
                                                            kwargs)

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
