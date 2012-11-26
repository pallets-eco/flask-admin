import itertools

from wtforms.fields import FieldList, FormField

from .widgets import InlineFieldListWidget, InlineFormWidget


class InlineFieldList(FieldList):
    widget = InlineFieldListWidget()

    def __init__(self, *args, **kwargs):
        super(InlineFieldList, self).__init__(*args, **kwargs)

        # Create template
        self.template = self.unbound_field.bind(form=None, name='')

        # Small hack to remove separator from FormField
        if isinstance(self.template, FormField):
            self.template.separator = ''

        self.template.process(None)

    def __call__(self, **kwargs):
        return self.widget(self,
                    template=self.template,
                    check=self.display_row_controls,
                    **kwargs)

    def display_row_controls(self, field):
        return True

    def process(self, formdata, data=None):
        res = super(InlineFieldList, self).process(formdata, data)

        # Postprocess - contribute flag
        if formdata:
            for f in self.entries:
                key = 'del-%s' % f.id
                f._should_delete = key in formdata

        return res

    def should_delete(self, field):
        return getattr(field, '_should_delete', False)

    def populate_obj(self, obj, name):
        values = getattr(obj, name, None)
        try:
            ivalues = iter(values)
        except TypeError:
            ivalues = iter([])

        candidates = itertools.chain(ivalues, itertools.repeat(None))
        _fake = type(str('_fake'), (object, ), {})

        output = []
        for field, data in itertools.izip(self.entries, candidates):
            if not self.should_delete(field):
                fake_obj = _fake()
                fake_obj.data = data
                field.populate_obj(fake_obj, 'data')
                output.append(fake_obj.data)

        setattr(obj, name, output)


class InlineModelFormField(FormField):
    """
        Customized ``FormField``.

        Excludes model primary key from the `populate_obj` and
        handles `should_delete` flag.
    """
    widget = InlineFormWidget()

    def __init__(self, form, pk, **kwargs):
        super(InlineModelFormField, self).__init__(form, **kwargs)

        self._pk = pk

    def get_pk(self):
        return getattr(self.form, self._pk).data

    def populate_obj(self, obj, name):
        for name, field in self.form._fields.iteritems():
            if name != self._pk:
                field.populate_obj(obj, name)


class InlineFormField(FormField):
    """
        Inline version of the ``FormField`` widget.
    """
    widget = InlineFormWidget()
