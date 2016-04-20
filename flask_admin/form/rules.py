from jinja2 import Markup

from flask_admin._compat import string_types
from flask_admin import helpers


class BaseRule(object):
    """
        Base form rule. All form formatting rules should derive from `BaseRule`.
    """
    def __init__(self):
        self.parent = None
        self.rule_set = None

    def configure(self, rule_set, parent):
        """
            Configure rule and assign to rule set.

            :param rule_set:
                Rule set
            :param parent:
                Parent rule (if any)
        """
        self.parent = parent
        self.rule_set = rule_set
        return self

    @property
    def visible_fields(self):
        """
            A list of visible fields for the given rule.
        """
        return []

    def __call__(self, form, form_opts=None, field_args={}):
        """
            Render rule.

            :param form:
                Form object
            :param form_opts:
                Form options
            :param field_args:
                Optional arguments that should be passed to template or the field
        """
        raise NotImplementedError()


class NestedRule(BaseRule):
    """
        Nested rule. Can contain child rules and render them.
    """
    def __init__(self, rules=[], separator=''):
        """
            Constructor.

            :param rules:
                Child rule list
            :param separator:
                Default separator between rules when rendering them.
        """
        super(NestedRule, self).__init__()
        self.rules = list(rules)
        self.separator = separator

    def configure(self, rule_set, parent):
        """
            Configure rule.

            :param rule_set:
                Rule set
            :param parent:
                Parent rule (if any)
        """
        self.rules = rule_set.configure_rules(self.rules, self)
        return super(NestedRule, self).configure(rule_set, parent)

    @property
    def visible_fields(self):
        """
            Return visible fields for all child rules.
        """
        visible_fields = []
        for rule in self.rules:
            for field in rule.visible_fields:
                visible_fields.append(field)
        return visible_fields

    def __iter__(self):
        """
            Return rules.
        """
        return self.rules

    def __call__(self, form, form_opts=None, field_args={}):
        """
            Render all children.

            :param form:
                Form object
            :param form_opts:
                Form options
            :param field_args:
                Optional arguments that should be passed to template or the field
        """
        result = []

        for r in self.rules:
            result.append(r(form, form_opts, field_args))

        return Markup(self.separator.join(result))


class Text(BaseRule):
    """
        Render text (or HTML snippet) from string.
    """
    def __init__(self, text, escape=True):
        """
            Constructor.

            :param text:
                Text to render
            :param escape:
                Should text be escaped or not. Default is `True`.
        """
        super(Text, self).__init__()

        self.text = text
        self.escape = escape

    def __call__(self, form, form_opts=None, field_args={}):
        if self.escape:
            return self.text

        return Markup(self.text)


class HTML(Text):
    """
        Shortcut for `Text` rule with `escape` set to `False`.
    """
    def __init__(self, html):
        super(HTML, self).__init__(html, escape=False)


class Macro(BaseRule):
    """
        Render macro by its name from current Jinja2 context.
    """
    def __init__(self, macro_name, **kwargs):
        """
            Constructor.

            :param macro_name:
                Macro name
            :param kwargs:
                Default macro parameters
        """
        super(Macro, self).__init__()

        self.macro_name = macro_name
        self.default_args = kwargs

    def _resolve(self, context, name):
        """
            Resolve macro in a Jinja2 context

            :param context:
                Jinja2 context
            :param name:
                Macro name. May be full path (with dots)
        """
        parts = name.split('.')

        try:
            field = context.resolve(parts[0])
        except AttributeError:
            raise Exception('Your template is missing '
                            '"{% set render_ctx = h.resolve_ctx() %}"')

        if not field:
            return None

        for p in parts[1:]:
            field = getattr(field, p, None)

            if not field:
                return field

        return field

    def __call__(self, form, form_opts=None, field_args={}):
        """
            Render macro rule.

            :param form:
                Form object
            :param form_opts:
                Form options
            :param field_args:
                Optional arguments that should be passed to the macro
        """
        context = helpers.get_render_ctx()
        macro = self._resolve(context, self.macro_name)

        if not macro:
            raise ValueError('Cannot find macro %s in current context.' % self.macro_name)

        opts = dict(self.default_args)
        opts.update(field_args)
        return macro(**opts)


class Container(Macro):
    """
        Render container around child rule.
    """
    def __init__(self, macro_name, child_rule, **kwargs):
        """
            Constructor.

            :param macro_name:
                Macro name that will be used as a container
            :param child_rule:
                Child rule to be rendered inside of container
            :param kwargs:
                Container macro arguments
        """
        super(Container, self).__init__(macro_name, **kwargs)
        self.child_rule = child_rule

    def configure(self, rule_set, parent):
        """
            Configure rule.

            :param rule_set:
                Rule set
            :param parent:
                Parent rule (if any)
        """
        self.child_rule.configure(rule_set, self)
        return super(Container, self).configure(rule_set, parent)

    @property
    def visible_fields(self):
        return self.child_rule.visible_fields

    def __call__(self, form, form_opts=None, field_args={}):
        """
            Render container.

            :param form:
                Form object
            :param form_opts:
                Form options
            :param field_args:
                Optional arguments that should be passed to template or the field
        """
        context = helpers.get_render_ctx()

        def caller(**kwargs):
            return context.call(self.child_rule, form, form_opts, kwargs)

        args = dict(field_args)
        args['caller'] = caller

        return super(Container, self).__call__(form, form_opts, args)


class Field(Macro):
    """
        Form field rule.
    """
    def __init__(self, field_name, render_field='lib.render_field'):
        """
            Constructor.

            :param field_name:
                Field name to render
            :param render_field:
                Macro that will be used to render the field.
        """
        super(Field, self).__init__(render_field)
        self.field_name = field_name

    @property
    def visible_fields(self):
        return [self.field_name]

    def __call__(self, form, form_opts=None, field_args={}):
        """
            Render field.

            :param form:
                Form object
            :param form_opts:
                Form options
            :param field_args:
                Optional arguments that should be passed to template or the field
        """
        field = getattr(form, self.field_name, None)

        if field is None:
            raise ValueError('Form %s does not have field %s' % (form, self.field_name))

        opts = {}

        if form_opts:
            opts.update(form_opts.widget_args.get(self.field_name, {}))

        opts.update(field_args)

        params = {
            'form': form,
            'field': field,
            'kwargs': opts
        }

        return super(Field, self).__call__(form, form_opts, params)


class Header(Macro):
    """
        Render header text.
    """
    def __init__(self, text, header_macro='lib.render_header'):
        """
            Constructor.

            :param text:
                Text to render
            :param header_macro:
                Header rendering macro
        """
        super(Header, self).__init__(header_macro, text=text)


class FieldSet(NestedRule):
    """
        Field set with header.
    """
    def __init__(self, rules, header=None, separator=''):
        """
            Constructor.

            :param rules:
                Child rules
            :param header:
                Header text
            :param separator:
                Child rule separator
        """
        if header:
            rule_set = [Header(header)] + list(rules)
        else:
            rule_set = list(rules)

        super(FieldSet, self).__init__(rule_set, separator=separator)


class RuleSet(object):
    """
        Rule set.
    """
    def __init__(self, view, rules):
        """
            Constructor.

            :param view:
                Administrative view
            :param rules:
                Rule list
        """
        self.view = view
        self.rules = self.configure_rules(rules)

    @property
    def visible_fields(self):
        visible_fields = []
        for rule in self.rules:
            for field in rule.visible_fields:
                visible_fields.append(field)
        return visible_fields

    def convert_string(self, value):
        """
            Convert string to rule.

            Override this method to change default behavior.
        """
        return Field(value)

    def configure_rules(self, rules, parent=None):
        """
            Configure all rules recursively - bind them to current RuleSet and
            convert string references to `Field` rules.

            :param rules:
                Rule list
            :param parent:
                Parent rule (if any)
        """
        result = []

        for r in rules:
            if isinstance(r, string_types):
                result.append(self.convert_string(r).configure(self, parent))
            else:
                try:
                    result.append(r.configure(self, parent))
                except AttributeError:
                    raise TypeError('Could not convert "%s" to rule' % repr(r))

        return result

    def __iter__(self):
        """
            Iterate through registered rules.
        """
        for r in self.rules:
            yield r
