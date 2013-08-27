from sqlalchemy import or_

from flask.ext.admin._compat import as_unicode, string_types
from flask.ext.admin.model.ajax import AjaxModelLoader, DEFAULT_PAGE_SIZE


class QueryAjaxModelLoader(AjaxModelLoader):
    def __init__(self, name, session, model, fields):
        """
            Constructor.

            :param fields:
                Fields to run query against
        """
        super(QueryAjaxModelLoader, self).__init__(name)

        self.session = session
        self.model = model
        self.fields = fields

        primary_keys = model._sa_class_manager.mapper.primary_key
        if len(primary_keys) > 1:
            raise NotImplemented('Flask-Admin does not support multi-pk AJAX model loading.')

        self.pk = primary_keys[0].name

    def format(self, model):
        if not model:
            return None

        return (getattr(model, self.pk), as_unicode(model))

    def get_one(self, pk):
        return self.session.query(self.model).get(pk)

    def get_list(self, term, offset=0, limit=DEFAULT_PAGE_SIZE):
        query = self.session.query(self.model)

        filters = (field.like(u'%%%s%%' % term) for field in self.fields)
        query = query.filter(or_(*filters))

        return query.offset(offset).limit(limit).all()


def create_ajax_loader(model, session, name, field_name, fields):
        attr = getattr(model, field_name, None)

        if attr is None:
            raise ValueError('Model %s does not have field %s.' % (model, field_name))

        if not hasattr(attr, 'property') or not hasattr(attr.property, 'direction'):
            raise ValueError('%s.%s is not a relation.' % (model, field_name))

        remote_model = attr.prop.mapper.class_
        remote_fields = []

        for field in fields:
            if isinstance(field, string_types):
                attr = getattr(remote_model, field, None)

                if not attr:
                    raise ValueError('%s.%s does not exist.' % (remote_model, field))

                remote_fields.append(attr)
            else:
                # TODO: Figure out if it is valid SQLAlchemy property?
                remote_fields.append(field)

        return QueryAjaxModelLoader(name, session, remote_model, remote_fields)
