import typing as t
from collections.abc import Generator

from jinja2.runtime import Context
from markupsafe import Markup
from wtforms import Field as WTField
from wtforms import Form

from flask_admin import helpers
from flask_admin._compat import string_types
from flask_admin._types import T_FORM_OPTS
from flask_admin._types import T_INLINE_BASE_FORM_ADMIN
from flask_admin._types import T_MODEL_VIEW
from flask_admin._types import T_RULES_SEQUENCE
from flask_admin._types import T_TRANSLATABLE


class BaseRule:
    """
    Base form rule. All form formatting rules should derive from `BaseRule`.
    """

    def __init__(self) -> None:
        self.parent: BaseRule | None = None
        self.rule_set: RuleSet | None = None

    def configure(
        self, rule_set: "RuleSet", parent: t.Optional["BaseRule"]
    ) -> "BaseRule":
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
    def visible_fields(self) -> list[str]:
        """
        A list of visible fields for the given rule.
        """
        return []

    def __call__(
        self,
        form: Form,
        form_opts: t.Union[T_FORM_OPTS, None] = None,
        field_args: t.Any = None,
    ) -> str:
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

    def __init__(
        self,
        rules: t.Optional[T_RULES_SEQUENCE] = None,  # ruff: noqa
        separator: str = "",
    ) -> None:
        """
        Constructor.

        :param rules:
            Child rule list
        :param separator:
            Default separator between rules when rendering them.
        """
        if rules is None:
            rules = []
        super().__init__()
        self.rules: list[str | Header | BaseRule] = list(rules)
        self.separator = separator

    def configure(self, rule_set: "RuleSet", parent: BaseRule | None) -> BaseRule:
        """
        Configure rule.

        :param rule_set:
            Rule set
        :param parent:
            Parent rule (if any)
        """
        self.rules = rule_set.configure_rules(self.rules, self)  # type: ignore
        return super().configure(rule_set, parent)

    @property
    def visible_fields(self) -> list[str]:
        """
        Return visible fields for all child rules.
        """
        visible_fields = []
        for rule in self.rules:
            for field in rule.visible_fields:  # type:ignore[union-attr]
                visible_fields.append(field)
        return visible_fields

    def __iter__(self) -> t.Iterable[t.Union[BaseRule, str, "Header"]]:
        """
        Return rules.
        """
        return self.rules

    def __call__(
        self,
        form: Form,
        form_opts: t.Union[T_FORM_OPTS, None] = None,
        field_args: t.Any = None,
    ) -> str:
        """
        Render all children.

        :param form:
            Form object
        :param form_opts:
            Form options
        :param field_args:
            Optional arguments that should be passed to template or the field
        """
        if field_args is None:
            field_args = {}
        result = []

        for r in self.rules:
            result.append(
                str(
                    r(  # type:ignore[operator]
                        form, form_opts, field_args
                    )
                )
            )

        return Markup(self.separator.join(result))


class Text(BaseRule):
    """
    Render text (or HTML snippet) from string.
    """

    def __init__(self, text: str, escape: bool = True) -> None:
        """
        Constructor.

        :param text:
            Text to render
        :param escape:
            Should text be escaped or not. Default is `True`.
        """
        super().__init__()

        self.text = text
        self.escape = escape

    def __call__(
        self,
        form: Form,
        form_opts: t.Union[T_FORM_OPTS, None] = None,
        field_args: t.Any = None,
    ) -> str:
        if field_args is None:
            field_args = {}
        if self.escape:
            return self.text

        return Markup(self.text)


class HTML(Text):
    """
    Shortcut for `Text` rule with `escape` set to `False`.
    """

    def __init__(self, html: str) -> None:
        super().__init__(html, escape=False)


class Macro(BaseRule):
    """
    Render macro by its name from current Jinja2 context.
    """

    def __init__(self, macro_name: str, **kwargs: t.Any) -> None:
        """
        Constructor.

        :param macro_name:
            Macro name
        :param kwargs:
            Default macro parameters
        """
        super().__init__()

        self.macro_name = macro_name
        self.default_args = kwargs

    def _resolve(self, context: Context, name: str) -> WTField | None:
        """
        Resolve macro in a Jinja2 context

        :param context:
            Jinja2 context
        :param name:
            Macro name. May be full path (with dots)
        """
        parts = name.split(".")

        try:
            field = context.resolve(parts[0])
        except AttributeError as err:
            raise Exception(
                'Your template is missing "{% set render_ctx = h.resolve_ctx() %}"'
            ) from err

        if not field:
            return None

        for p in parts[1:]:
            field = getattr(field, p, None)

            if not field:
                return field

        return field  # type: ignore[return-value]

    def __call__(
        self,
        form: Form,
        form_opts: t.Union[T_FORM_OPTS, None] = None,
        field_args: t.Any = None,
    ) -> str:
        """
        Render macro rule.

        :param form:
            Form object
        :param form_opts:
            Form options
        :param field_args:
            Optional arguments that should be passed to the macro
        """
        if field_args is None:
            field_args = {}
        context = helpers.get_render_ctx()
        macro = self._resolve(context, self.macro_name)  # type:ignore[arg-type]

        if not macro:
            raise ValueError(f"Cannot find macro {self.macro_name} in current context.")

        opts = dict(self.default_args)
        opts.update(field_args)
        return macro(**opts)


class Container(Macro):
    """
    Render container around child rule.
    """

    def __init__(self, macro_name: str, child_rule: BaseRule, **kwargs: t.Any) -> None:
        """
        Constructor.

        :param macro_name:
            Macro name that will be used as a container
        :param child_rule:
            Child rule to be rendered inside of container
        :param kwargs:
            Container macro arguments


        The container is nothing but a Jinja Macro
        that is placed within the current jinja context. The rule inside the container
        is represented by `{{ caller() }}` as it is shown in the follwoing Jinja
        [snippet](/advanced/index.html#built-in-rules):
        """
        super().__init__(macro_name, **kwargs)
        self.child_rule = child_rule

    def configure(self, rule_set: "RuleSet", parent: BaseRule | None) -> BaseRule:
        """
        Configure rule.

        :param rule_set:
            Rule set
        :param parent:
            Parent rule (if any)
        """
        self.child_rule.configure(rule_set, self)
        return super().configure(rule_set, parent)

    @property
    def visible_fields(self) -> list[str]:
        return self.child_rule.visible_fields

    def __call__(
        self,
        form: Form,
        form_opts: t.Union[T_FORM_OPTS, None] = None,
        field_args: t.Any = None,
    ) -> str:
        """
        Render container.

        :param form:
            Form object
        :param form_opts:
            Form options
        :param field_args:
            Optional arguments that should be passed to template or the field
        """
        if field_args is None:
            field_args = {}
        context = helpers.get_render_ctx()

        def caller(**kwargs: t.Any) -> None:
            return context.call(  # type:ignore[union-attr, return-value]
                self.child_rule, form, form_opts, kwargs
            )

        args = dict(field_args)
        args["caller"] = caller

        return super().__call__(form, form_opts, args)


class Field(Macro):
    """
    Form field rule.
    """

    def __init__(self, field_name: str, render_field: str = "lib.render_field") -> None:
        """
        Constructor.

        :param field_name:
            Field name to render
        :param render_field:
            Macro that will be used to render the field.
        """
        super().__init__(render_field)
        self.field_name = field_name

    @property
    def visible_fields(self) -> list[str]:
        return [self.field_name]

    def __call__(
        self,
        form: Form,
        form_opts: t.Union[T_FORM_OPTS, None] = None,
        field_args: t.Any = None,
    ) -> str:
        """
        Render field.

        :param form:
            Form object
        :param form_opts:
            Form options
        :param field_args:
            Optional arguments that should be passed to template or the field
        """
        if field_args is None:
            field_args = {}
        field = getattr(form, self.field_name, None)

        if field is None:
            raise ValueError(f"Form {form} does not have field {self.field_name}")

        opts = {}

        if form_opts:
            opts.update(form_opts.widget_args.get(self.field_name, {}))

        opts.update(field_args)

        params = {"form": form, "field": field, "kwargs": opts}

        return super().__call__(form, form_opts, params)


class Header(Macro):
    """
    Render header text.
    """

    def __init__(self, text: str, header_macro: str = "lib.render_header") -> None:
        """
        Constructor.

        :param text:
            Text to render
        :param header_macro:
            Header rendering macro
        """
        super().__init__(header_macro, text=text)


class FieldSet(NestedRule):
    """
    Field set with header.
    """

    def __init__(
        self,
        rules: T_RULES_SEQUENCE,
        header: T_TRANSLATABLE | None = None,
        separator: str = "",
    ) -> None:
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

        super().__init__(rule_set, separator=separator)


class Row(NestedRule):
    """
    Takes a list of rules and render them in a single row.
    """

    def __init__(self, *columns: str | BaseRule, **kw: t.Any) -> None:
        super().__init__()
        self.rules: list[str | BaseRule] = columns  # type:ignore[assignment]

    def __call__(
        self,
        form: Form,
        form_opts: t.Union[T_FORM_OPTS, None] = None,
        field_args: t.Any = None,
    ) -> str:
        if field_args is None:
            field_args = {}
        cols = []
        for col in self.rules:
            if col.visible_fields:  # type:ignore[union-attr]
                w_args = form_opts.widget_args.setdefault(  # type:ignore[union-attr]
                    col.visible_fields[0],  # type:ignore[union-attr]
                    {},
                )
                w_args.setdefault("column_class", "col")
            cols.append(
                col(  # type: ignore[operator]
                    form, form_opts, field_args
                )
            )

        return Markup('<div class="form-row">{}</div>'.format("".join(cols)))


class Group(Macro):
    def __init__(
        self,
        field_name: str,
        prepend: str | tuple[str] | list[str] | None = None,
        append: str | tuple[str] | list[str] | None = None,
        **kwargs: t.Any,
    ) -> None:
        """
        [Bootstrap Input group](https://getbootstrap.com/docs/4.6/components/input-group/).
        It renders the target field whatever its type is
        (text, radio, checkbox..etc), allowing prepended and appended boxes to
        be filled with any HTML content.
        """
        render_field = kwargs.get("render_field", "lib.render_field")
        super().__init__(render_field)
        self.field_name = field_name
        self._addons = []

        if prepend:
            if not isinstance(prepend, tuple | list):
                prepend = [prepend]

            for cnf in prepend:
                if isinstance(cnf, str):
                    self._addons.append({"pos": "prepend", "type": "text", "text": cnf})
                    continue

                if cnf["type"] in ("field", "html", "text"):
                    cnf["pos"] = "prepend"
                    self._addons.append(cnf)

        if append:
            if not isinstance(append, tuple | list):
                append = [append]

            for cnf in append:
                if isinstance(cnf, str):
                    self._addons.append({"pos": "append", "type": "text", "text": cnf})
                    continue

                if cnf["type"] in ("field", "html", "text"):
                    cnf["pos"] = "append"
                    self._addons.append(cnf)

        print(self._addons)

    @property
    def visible_fields(self) -> list[str]:
        fields = [self.field_name]
        for cnf in self._addons:
            if cnf["type"] == "field":
                fields.append(cnf["name"])
        return fields

    def __call__(
        self,
        form: Form,
        form_opts: t.Union[T_FORM_OPTS, None] = None,
        field_args: t.Any = None,
    ) -> str:
        """
        Render field.

        :param form:
            Form object
        :param form_opts:
            Form options
        :param field_args:
            Optional arguments that should be passed to template or the field
        """
        if field_args is None:
            field_args = {}
        field = getattr(form, self.field_name, None)

        if field is None:
            raise ValueError(f"Form {form} does not have field {self.field_name}")

        if form_opts:
            widget_args = form_opts.widget_args
        else:
            widget_args = {}

        opts = {}
        prepend = []
        append = []
        for cnf in self._addons:
            ctn: str | None = None
            typ = cnf["type"]
            if typ == "field":
                name = cnf["name"]
                fld = form._fields.get(name, None)
                if fld:
                    w_args = widget_args.setdefault(name, {})
                    if fld.type in ("BooleanField", "RadioField"):
                        w_args.setdefault("class", "form-check-input")
                    else:
                        w_args.setdefault("class", "form-control")
                    ctn = fld(**w_args)
            elif typ == "text":
                ctn = '<span class="input-group-text">{}</span>'.format(cnf["text"])
            elif typ == "html":
                ctn = cnf["html"]

            if ctn:
                if cnf["pos"] == "prepend":
                    prepend.append(ctn)
                else:
                    append.append(ctn)

        if prepend:
            opts["prepend"] = Markup("".join(prepend))

        if append:
            opts["append"] = Markup("".join(append))

        opts.update(widget_args.get(self.field_name, {}))
        opts.update(field_args)

        params = {"form": form, "field": field, "kwargs": opts}

        return super().__call__(form, form_opts, params)


class RuleSet:
    """
    Rule set.
    """

    def __init__(
        self,
        view: t.Union[T_MODEL_VIEW, T_INLINE_BASE_FORM_ADMIN],
        rules: t.Sequence[str | tuple | list | BaseRule | FieldSet],
    ) -> None:
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
    def visible_fields(self) -> list[str]:
        visible_fields = []
        for rule in self.rules:
            for field in rule.visible_fields:
                visible_fields.append(field)
        return visible_fields

    def convert_string(self, value: str) -> BaseRule:
        """
        Convert string to rule.

        Override this method to change default behavior.
        """
        return Field(value)

    def configure_rules(
        self,
        rules: t.Sequence[str | tuple | list | BaseRule | FieldSet],
        parent: BaseRule | None = None,
    ) -> list[BaseRule]:
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
            elif isinstance(r, tuple | list):
                row = Row(*r)
                result.append(row.configure(self, parent))
            else:
                try:
                    result.append(r.configure(self, parent))
                except AttributeError as err:
                    raise TypeError(f'Could not convert "{repr(r)}" to rule') from err

        return result

    def __iter__(self) -> Generator[BaseRule, None, None]:
        """
        Iterate through registered rules.
        """
        yield from self.rules
