import mongoengine

from flask.ext.admin._compat import string_types, as_unicode, iteritems
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


def create_ajax_loader(model, name, field_name, fields):
    prop = getattr(model, field_name, None)

    if prop is None:
        raise ValueError('Model %s does not have field %s.' % (model, field_name))

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


def process_ajax_references(references, view):
    def make_name(base, name):
        if base:
            return ('%s-%s' % (base, name)).lower()
        else:
            return as_unicode(name).lower()

    def handle_field(field, subdoc, base):
        ftype = type(field).__name__

        if ftype == 'ListField':
            child_doc = getattr(subdoc, '_form_subdocuments', {}).get(None)

            if child_doc:
                handle_field(field.field, child_doc, base)
        elif ftype == 'EmbeddedDocumentField':
            result = {}

            ajax_refs = getattr(subdoc, 'form_ajax_refs', {})

            for field_name, opts in iteritems(ajax_refs):
                child_name = make_name(base, field_name)

                if isinstance(opts, (list, tuple)):
                    loader = create_ajax_loader(field.document_type_obj, child_name, field_name, opts)
                else:
                    loader = opts

                result[field_name] = loader
                references[child_name] = loader

            subdoc._form_ajax_refs = result

            child_doc = getattr(subdoc, '_form_subdocuments', None)
            if child_doc:
                handle_subdoc(field.document_type_obj, subdoc, base)
        else:
            raise ValueError('Failed to process subdocument field %s' % (field,))

    def handle_subdoc(model, subdoc, base):
        documents = getattr(subdoc, '_form_subdocuments', {})

        for name, doc in iteritems(documents):
            field = getattr(model, name, None)

            if not field:
                raise ValueError('Invalid subdocument field %s.%s')

            handle_field(field, doc, make_name(base, name))

    handle_subdoc(view.model, view, '')

    return references
