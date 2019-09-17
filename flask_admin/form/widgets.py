from werkzeug.routing import BuildError
from wtforms import widgets
from flask.globals import _request_ctx_stack
from flask import url_for
from flask_admin.babel import gettext, ngettext
from flask_admin import helpers as h

__all__ = ['Select2Widget', 'DatePickerWidget', 'DateTimePickerWidget', 'RenderTemplateWidget', 'Select2TagsWidget', ]


def _is_bootstrap3():
    view = h.get_current_view()
    return view and view.admin.template_mode == 'bootstrap3'


class Select2Widget(widgets.Select):
    """
        `Select2 <https://github.com/ivaynberg/select2>`_ styled select widget.

        You must include select2.js, form-x.x.x.js and select2 stylesheet for it to
        work.
    """
    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', u'select2')

        allow_blank = getattr(field, 'allow_blank', False)
        if allow_blank and not self.multiple:
            kwargs['data-allow-blank'] = u'1'

        return super(Select2Widget, self).__call__(field, **kwargs) + self.create_related_link(field)

    def create_related_link(self, field):
        try:
            url = url_for(field.name + ".create_view")
            html = """
                <a class="add-related" onclick='window.open("%s?in-new-window=true", "%s", "width=600, height=450")'>
                    <span class="glyphicon glyphicon-plus"
                    style="cursor:pointer; position: absolute; top: 0px; left: -3px;"></span>
                </a>
                """ % (url, field.name)
        except BuildError:
            html = ""
        return html


class Select2TagsWidget(widgets.TextInput):
    """`Select2 <http://ivaynberg.github.com/select2/#tags>`_ styled text widget.
    You must include select2.js, form-x.x.x.js and select2 stylesheet for it to work.
    """
    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', u'select2-tags')
        return super(Select2TagsWidget, self).__call__(field, **kwargs)


class DatePickerWidget(widgets.TextInput):
    """
        Date picker widget.

        You must include bootstrap-datepicker.js and form-x.x.x.js for styling to work.
    """
    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', u'datepicker')
        kwargs.setdefault('data-date-format', u'YYYY-MM-DD')

        self.date_format = kwargs['data-date-format']
        return super(DatePickerWidget, self).__call__(field, **kwargs)


class DateTimePickerWidget(widgets.TextInput):
    """
        Datetime picker widget.

        You must include bootstrap-datepicker.js and form-x.x.x.js for styling to work.
    """
    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', u'datetimepicker')
        kwargs.setdefault('data-date-format', u'YYYY-MM-DD HH:mm:ss')
        return super(DateTimePickerWidget, self).__call__(field, **kwargs)


class TimePickerWidget(widgets.TextInput):
    """
        Date picker widget.

        You must include bootstrap-datepicker.js and form-x.x.x.js for styling to work.
    """
    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', u'timepicker')
        kwargs.setdefault('data-date-format', u'HH:mm:ss')
        return super(TimePickerWidget, self).__call__(field, **kwargs)


class RenderTemplateWidget(object):
    """
        WTForms widget that renders Jinja2 template
    """
    def __init__(self, template):
        """
            Constructor

            :param template:
                Template path
        """
        self.template = template

    def __call__(self, field, **kwargs):
        ctx = _request_ctx_stack.top
        jinja_env = ctx.app.jinja_env

        kwargs.update({
            'field': field,
            '_gettext': gettext,
            '_ngettext': ngettext,
            'h': h,
        })

        template = jinja_env.get_template(self.template)
        return template.render(kwargs)
