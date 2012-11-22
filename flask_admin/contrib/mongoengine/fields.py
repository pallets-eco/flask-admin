from wtforms.fields import FormField


class ModelFormField(FormField):
    def __init__(self, model, *args, **kwargs):
        # Small hack to get rid of separator if name is empty
        name = kwargs.get('name')
        if not name:
            kwargs['separator'] = ''

        super(ModelFormField, self).__init__(*args, **kwargs)

        self.model = model

    def populate_obj(self, obj, name):
        candidate = getattr(obj, name, None)
        if candidate is None:
            candidate = self.model()
            setattr(obj, name, candidate)

        self.form.populate_obj(candidate)
