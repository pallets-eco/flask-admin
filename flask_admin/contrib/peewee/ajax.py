import mongoengine

from flask.ext.admin._compat import as_unicode
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
