from flask.ext.admin.form import RenderTemplateWidget


class InlineFieldListWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFieldListWidget, self).__init__('admin/model/inline_field_list.html')


class InlineFormWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFormWidget, self).__init__('admin/model/inline_form.html')
