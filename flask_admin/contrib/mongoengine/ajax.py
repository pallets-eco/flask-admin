import mongoengine

from flask_admin._compat import string_types, as_unicode, iteritems
from flask_admin.model.ajax import AjaxModelLoader, DEFAULT_PAGE_SIZE


class QueryAjaxModelLoader(AjaxModelLoader):
    def __init__(self, name, model, **options):
        """
            Constructor.

            :param fields:
                Fields to run query against
        """
        super(QueryAjaxModelLoader, self).__init__(name, options)

        self.model = model
        self.fields = options.get('fields')

        self._cached_fields = self._process_fields()

        if not self.fields:
            raise ValueError('AJAX loading requires `fields` to be specified for %s.%s' % (model, self.name))

    def _process_fields(self):
        remote_fields = []

        for field in self.fields:
            if isinstance(field, string_types):
                attr = getattr(self.model, field, None)

                if not attr:
                    raise ValueError('%s.%s does not exist.' % (self.model, field))

                remote_fields.append(attr)
            else:
                remote_fields.append(field)

        return remote_fields

    def format(self, model):
        if not model:
            return None

        return (as_unicode(model.id), as_unicode(model))

    def get_one(self, pk):
        return self.model.objects.filter(id=pk).first()

    def get_list(self, term, offset=0, limit=DEFAULT_PAGE_SIZE):
        query = self.model.objects

        if len(term) > 0:
            criteria = None

            for field in self._cached_fields:
                flt = {u'%s__icontains' % field.name: term}

                if not criteria:
                    criteria = mongoengine.Q(**flt)
                else:
                    criteria |= mongoengine.Q(**flt)

            query = query.filter(criteria)

        if offset:
            query = query.skip(offset)

        return query.limit(limit).all()


def create_ajax_loader(model, name, field_name, opts):
    prop = getattr(model, field_name, None)

    if prop is None:
        raise ValueError('Model %s does not have field %s.' % (model, field_name))

    ftype = type(prop).__name__

    if ftype == 'ListField' or ftype == 'SortedListField':
        prop = prop.field
        ftype = type(prop).__name__

    if ftype != 'ReferenceField':
        raise ValueError('Dont know how to convert %s type for AJAX loader' % ftype)

    remote_model = prop.document_type
    return QueryAjaxModelLoader(name, remote_model, **opts)


def process_ajax_references(references, view):
    def make_name(base, name):
        if base:
            return ('%s-%s' % (base, name)).lower()
        else:
            return as_unicode(name).lower()

    def handle_field(field, subdoc, base):
        ftype = type(field).__name__

        if ftype == 'ListField' or ftype == 'SortedListField':
            child_doc = getattr(subdoc, '_form_subdocuments', {}).get(None)

            if child_doc:
                handle_field(field.field, child_doc, base)
        elif ftype == 'EmbeddedDocumentField':
            result = {}

            ajax_refs = getattr(subdoc, 'form_ajax_refs', {})

            for field_name, opts in iteritems(ajax_refs):
                child_name = make_name(base, field_name)

                if isinstance(opts, dict):
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
                raise ValueError('Invalid subdocument field %s.%s' % (model, name))

            handle_field(field, doc, make_name(base, name))

    handle_subdoc(view.model, view, '')

    return references
