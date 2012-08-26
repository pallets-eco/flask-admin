from flask.globals import _request_ctx_stack


class RenderTemplateWidget(object):
    def __init__(self, template):
        self.template = template

    def __call__(self, field, **kwargs):
        ctx = _request_ctx_stack.top
        jinja_env = ctx.app.jinja_env

        print kwargs

        kwargs['field'] = field

        template = jinja_env.get_template(self.template)
        return template.render(kwargs)


class InlineFormListWidget(RenderTemplateWidget):
    def __init__(self):
        super(InlineFormListWidget, self).__init__('admin/model/inline_form_list.html')
