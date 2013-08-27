from flask.ext.admin._compat import iteritems
from flask.ext.admin.model.form import InlineBaseFormAdmin


class EmbeddedForm(InlineBaseFormAdmin):
    def __init__(self, **kwargs):
        super(EmbeddedForm, self).__init__(**kwargs)

        self._form_subdocuments = convert_subdocuments(getattr(self, 'form_subdocuments', {}))


def convert_subdocuments(values):
    result = {}

    for name, p in iteritems(values):
        if isinstance(p, dict):
            result[name] = EmbeddedForm(**p)
        elif isinstance(p, EmbeddedForm):
            result[name] = p
        else:
            raise ValueError('Invalid subdocument type: expecting dict or instance of flask.ext.admin.contrib.mongoengine.EmbeddedForm, got %s' % type(p))

    return result
