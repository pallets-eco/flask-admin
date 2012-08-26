from wtforms.fields import FormField


class InlineModelFormField(FormField):
    """
        Customized ``FormField``.

        Excludes model primary key from the `populate_obj` and
        handles `should_delete` flag.
    """
    def __init__(self, form, pk, **kwargs):
        super(InlineModelFormField, self).__init__(form, **kwargs)

        self._pk = pk
        self._should_delete = False

    def process(self, formdata, data=None):
        super(InlineModelFormField, self).process(formdata, data)

        # Grab delete key
        if formdata:
            key = 'del-%s' % self.id
            if key in formdata:
                self._should_delete = True

    def should_delete(self):
        return self._should_delete

    def get_pk(self):
        return getattr(self.form, self._pk).data

    def populate_obj(self, obj, name):
        for name, field in self.form._fields.iteritems():
            if name != self._pk:
                field.populate_obj(obj, name)
