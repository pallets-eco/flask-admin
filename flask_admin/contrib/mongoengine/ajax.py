import mongoengine

from flask.ext.admin._compat import as_unicode
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
            flt = {'%s__icontains' % field.name: term}

            if not criteria:
                criteria = mongoengine.Q(**flt)
            else:
                criteria |= mongoengine.Q(**flt)

        return query.filter(criteria).skip(offset).limit(limit)
