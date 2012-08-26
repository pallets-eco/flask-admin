from flask.ext.admin.form import RenderTemplateWidget


class InlineFormListWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFormListWidget, self).__init__('admin/model/inline_form_list.html')
