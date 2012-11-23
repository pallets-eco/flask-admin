from wtforms.fields import FormField


class ModelFormField(FormField):
    """
        Customized ModelFormField for MongoEngine EmbeddedDocuments.
    """
    def __init__(self, model, *args, **kwargs):
        super(ModelFormField, self).__init__(*args, **kwargs)

        self.model = model

    def populate_obj(self, obj, name):
        candidate = getattr(obj, name, None)
        if candidate is None:
            candidate = self.model()
            setattr(obj, name, candidate)

        self.form.populate_obj(candidate)
