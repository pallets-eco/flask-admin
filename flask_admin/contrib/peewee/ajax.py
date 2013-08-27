from flask.ext.admin._compat import as_unicode, string_types
from flask.ext.admin.model.ajax import AjaxModelLoader, DEFAULT_PAGE_SIZE

from .tools import get_primary_key


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
        self.pk = get_primary_key(model)

    def format(self, model):
        if not model:
            return None

        return (getattr(model, self.pk), as_unicode(model))

    def get_one(self, pk):
        return self.model.get(**{self.pk: pk})

    def get_list(self, term, offset=0, limit=DEFAULT_PAGE_SIZE):
        query = self.model.select()

        stmt = None
        for field in self.fields:
            q = field ** (u'%%%s%%' % term)

            if stmt is None:
                stmt = q
            else:
                stmt |= q

        query = query.where(stmt)

        if offset:
            query = query.offset(offset)

        return list(query.limit(limit).execute())


def create_ajax_loader(model, name, field_name, fields):
    prop = getattr(model, field_name, None)

    if prop is None:
        raise ValueError('Model %s does not have field %s.' % (model, field_name))

    # TODO: Check for field
    remote_model = prop.rel_model
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
