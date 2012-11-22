from flask.ext.admin.form import RenderTemplateWidget


class InlineFieldListWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFieldListWidget, self).__init__('admin/model/inline_field_list.html')


class InlineFormListWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFormListWidget, self).__init__('admin/model/inline_form_list.html')
