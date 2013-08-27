import mongoengine

from flask.ext.admin._compat import string_types, as_unicode
from flask.ext.admin.model.ajax import AjaxModelLoader, DEFAULT_PAGE_SIZE


class QueryAjaxModelLoader(AjaxModelLoader):
    def __init__(self, name, model, fields):
        """
            Constructor.

            :param fields:
                Fields to run query against
        """
        super(QueryAjaxModelLoader, self).__init__(name)

        self.model = model
        self.fields = fields

    def format(self, model):
        if not model:
            return None

        return (as_unicode(model.id), as_unicode(model))

    def get_one(self, pk):
        return self.model.objects.filter(id=pk).first()

    def get_list(self, term, offset=0, limit=DEFAULT_PAGE_SIZE):
        query = self.model.objects

        criteria = None

        for field in self.fields:
            flt = {u'%s__icontains' % field.name: term}

            if not criteria:
                criteria = mongoengine.Q(**flt)
            else:
                criteria |= mongoengine.Q(**flt)

        query = query.filter(criteria)

        if offset:
            query = query.skip(offset)

        return query.limit(limit).all()


def create_ajax_loader(model, name, fields):
    prop = getattr(model, name, None)

    if prop is None:
        raise ValueError('Model %s does not have field %s.' % (model, name))

    # TODO: Check for field

    remote_model = prop.document_type
    remote_fields = []

    for field in fields:
        if isinstance(field, string_types):
            attr = getattr(remote_model, field, None)

            if not attr:
                raise ValueError('%s.%s does not exist.' % (remote_model, field))

            remote_fields.append(attr)
        else:
            remote_fields.append(field)

    return QueryAjaxModelLoader(name, remote_model, remote_fields)
