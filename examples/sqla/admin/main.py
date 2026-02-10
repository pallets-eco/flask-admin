from flask import redirect
from flask import url_for
from flask_admin import Admin
from flask_admin.babel import gettext
from flask_admin.base import MenuLink
from flask_admin.contrib.sqla import filters
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from flask_admin.contrib.sqla.filters import FilterEqual
from flask_admin.form import rules
from flask_admin.theme import Bootstrap4Theme
from markupsafe import Markup
from wtforms import validators

from . import app
from . import db
from .models import AVAILABLE_USER_TYPES
from .models import AuditLog
from .models import Post
from .models import Tag
from .models import Tree
from .models import User


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask-Admin Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 20px;
        }

        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
            padding: 40px;
            max-width: 500px;
            width: 100%;
            text-align: center;
        }

        .logo {
            font-size: 48px;
            margin-bottom: 10px;
        }

        h1 {
            color: #1a1a2e;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .subtitle {
            color: #666;
            font-size: 16px;
            margin-bottom: 30px;
        }

        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #ddd, transparent);
            margin: 20px 0;
        }

        .language-label {
            color: #888;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 20px;
        }

        .languages {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .lang-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 14px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }

        .lang-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        .lang-btn:active {
            transform: translateY(-1px);
        }

        .lang-btn .flag {
            font-size: 20px;
        }

        .lang-btn.featured {
            grid-column: span 2;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
        }

        .lang-btn.featured:hover {
            box-shadow: 0 8px 25px rgba(245, 87, 108, 0.4);
        }

        .footer {
            margin-top: 30px;
            color: #999;
            font-size: 13px;
        }

        .footer a {
            color: #667eea;
            text-decoration: none;
        }

        .footer a:hover {
            text-decoration: underline;
        }

        @media (max-width: 480px) {
            .card {
                padding: 30px 20px;
            }

            h1 {
                font-size: 24px;
            }

            .languages {
                grid-template-columns: 1fr;
            }

            .lang-btn.featured {
                grid-column: span 1;
            }
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">&#9881;</div>
        <h1>Flask-Admin Demo</h1>
        <p class="subtitle">SQLAlchemy Example with Audit Logging</p>

        <div class="divider"></div>

        <p class="language-label">Select Your Language</p>

        <div class="languages">
            <a href="/admin/?lang=en" class="lang-btn featured">
                <span class="flag">&#127468;&#127463;</span>
                <span>English</span>
            </a>
            <a href="/admin/?lang=de" class="lang-btn">
                <span class="flag">&#127465;&#127466;</span>
                <span>Deutsch</span>
            </a>
            <a href="/admin/?lang=fr" class="lang-btn">
                <span class="flag">&#127467;&#127479;</span>
                <span>Fran&#231;ais</span>
            </a>
            <a href="/admin/?lang=es" class="lang-btn">
                <span class="flag">&#127466;&#127480;</span>
                <span>Espa&#241;ol</span>
            </a>
            <a href="/admin/?lang=pt" class="lang-btn">
                <span class="flag">&#127463;&#127479;</span>
                <span>Portugu&#234;s</span>
            </a>
            <a href="/admin/?lang=ru" class="lang-btn">
                <span class="flag">&#127479;&#127482;</span>
                <span>&#1056;&#1091;&#1089;&#1089;&#1082;&#1080;&#1081;</span>
            </a>
            <a href="/admin/?lang=cs" class="lang-btn">
                <span class="flag">&#127464;&#127487;</span>
                <span>&#268;e&#353;tina</span>
            </a>
            <a href="/admin/?lang=fa" class="lang-btn">
                <span class="flag">&#127470;&#127479;</span>
                <span>&#1601;&#1575;&#1585;&#1587;&#1740;</span>
            </a>
            <a href="/admin/?lang=pa" class="lang-btn">
                <span class="flag">&#127470;&#127475;</span>
                <span>&#2602;&#2672;&#2588;&#2622;&#2604;&#2624;</span>
            </a>
            <a href="/admin/?lang=zh_CN" class="lang-btn">
                <span class="flag">&#127464;&#127475;</span>
                <span>&#31616;&#20307;&#20013;&#25991;</span>
            </a>
            <a href="/admin/?lang=zh_TW" class="lang-btn">
                <span class="flag">&#127481;&#127484;</span>
                <span>&#32321;&#39636;&#20013;&#25991;</span>
            </a>
        </div>

        <div class="footer">
            Powered by <a href="https://github.com/flask-admin/flask-admin" target="_blank">Flask-Admin</a>
        </div>
    </div>
</body>
</html>"""


@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="/favicon.ico"))


# Custom filter class
class FilterLastNameBrown(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        if value == "1":
            return query.filter(self.column == "Brown")
        else:
            return query.filter(self.column != "Brown")

    def operation(self):
        return "is Brown"


# Customized User model admin
def phone_number_formatter(view, context, model, name):
    return Markup(f"<nobr>{model.phone_number}</nobr>") if model.phone_number else None


def is_numberic_validator(form, field):
    if field.data and not field.data.isdigit():
        raise validators.ValidationError(gettext("Only numbers are allowed."))


class UserAdmin(ModelView):
    can_set_page_size = True
    page_size = 5
    page_size_options = (5, 10, 15)
    can_view_details = True
    action_disallowed_list = [
        "delete",
    ]

    form_choices = {
        "type": AVAILABLE_USER_TYPES,
    }
    form_args = {
        "dialling_code": {"label": "Dialling code"},
        "local_phone_number": {
            "label": "Phone number",
            "validators": [is_numberic_validator],
        },
    }
    form_widget_args = {"id": {"readonly": True}}
    column_list = [
        "type",
        "first_name",
        "last_name",
        "email",
        "ip_address",
        "currency",
        "timezone",
        "phone_number",
    ]
    column_searchable_list = [
        "first_name",
        "last_name",
        "phone_number",
        "email",
    ]
    column_editable_list = ["type", "currency", "timezone"]
    column_details_list = [
        "id",
        "featured_post",
        "website",
        "enum_choice_field",
        "sqla_utils_choice_field",
        "sqla_utils_enum_choice_field",
    ] + column_list  # type: ignore[operator]
    form_columns = [
        "id",
        "type",
        "featured_post",
        "enum_choice_field",
        "sqla_utils_choice_field",
        "sqla_utils_enum_choice_field",
        "last_name",
        "first_name",
        "email",
        "website",
        "dialling_code",
        "local_phone_number",
        "ip_address",
        "timezone",
    ]
    create_template = "admin/users/create.html"
    form_create_rules = [
        rules.Header("Users"),  # HTML header
        rules.HTML("<hr>"),  # HTML horizontal line
        "last_name",  # show it as first field
        "first_name",  # show it as second field
        rules.Text("Foobar"),  # static text
        rules.FieldSet(
            (
                "type",
                rules.Row(
                    rules.Group(
                        "dialling_code",
                        prepend="➕",
                        append='<i class="fa fa-phone"></i>',
                    ),
                    "local_phone_number",
                    "email",
                ),
                rules.Text("--- The end of contact details ---"),
            ),
            "Contact details:",
        ),  # field set with legend
        # custom container (see templates/admin/create.html)
        rules.Container(
            "wrap_in_card",
            rules.NestedRule(
                separator="<hr>",
                rules=[
                    rules.Field("enum_choice_field"),
                    rules.Field("sqla_utils_choice_field"),
                    rules.Field("sqla_utils_enum_choice_field"),
                ],
            ),
            card_title="Some Choices",
        ),
        "website",
        "ip_address",
        "timezone",
        # render a macro (see templates/admin/create.html)
        rules.Macro("my_macro", arg1="Just a Title", arg2="bla bla bla"),
    ]

    column_auto_select_related = True
    column_default_sort = [
        ("last_name", False),
        ("first_name", False),
    ]  # sort on multiple columns

    # custom filter: each filter in the list is a filter operation (equals, not equals,
    # etc) filters with the same name will appear as operations under the same filter
    column_filters = [
        "first_name",
        FilterEqual(column=User.last_name, name="Last Name"),
        FilterLastNameBrown(
            column=User.last_name, name="Last Name", options=(("1", "Yes"), ("0", "No"))
        ),
        "phone_number",
        "email",
        "ip_address",
        "currency",
        "timezone",
    ]
    column_formatters = {"phone_number": phone_number_formatter}

    # setup edit forms so that only posts created by this user can be selected as
    # 'featured'
    def edit_form(self, obj):  # type: ignore[override]
        return self._filtered_posts(super().edit_form(obj))  # type: ignore[override]

    def _filtered_posts(self, form):
        form.featured_post.query_factory = lambda: Post.query.filter(
            Post.user_id == form._obj.id
        ).all()
        return form


class PostAdmin(ModelView):
    column_display_pk = True
    column_list = [
        "id",
        "user",
        "user.email",
        "title",
        "date",
        "tags",
        "background_color",
        "created_at",
    ]
    column_editable_list = [
        "background_color",
    ]
    column_default_sort = ("date", True)
    create_modal = True
    edit_modal = True
    column_sortable_list = [
        "id",
        "title",
        "date",
        "user.email",
        ("user", ("user.last_name", "user.first_name")),  # sort on multiple columns
    ]
    column_searchable_list = [
        "title",
        "tags.name",
        "user.first_name",
        "user.last_name",
    ]
    column_labels = {
        "title": "Post Title",
        "tags.name": "Tags",
        "user.first_name": "User's first name",
        "user.last_name": "Last name",
    }
    column_filters = [
        "id",
        "user.first_name",
        "user.id",
        "background_color",
        "created_at",
        "title",
        "date",
        "tags",
        filters.FilterLike(
            Post.title,
            "Fixed Title",
            options=(("test1", "Test 1"), ("test2", "Test 2")),
        ),
    ]
    can_export = True
    export_max_rows = 1000
    export_types = ["csv", "xls"]

    # Pass arguments to WTForms. In this case, change label for text field to
    # be 'Big Text' and add DataRequired() validator.
    form_args = {"text": dict(label="Big Text", validators=[validators.DataRequired()])}
    form_widget_args = {"text": {"rows": 10}}

    form_ajax_refs = {
        "user": {"fields": (User.first_name, User.last_name)},
        "tags": {
            "fields": (Tag.name,),
            "minimum_input_length": 0,  # show suggestions, even before any user input
            "placeholder": "Please select",
            "page_size": 5,
        },
    }

    def __init__(self, session):
        # Just call parent class with predefined model.
        super().__init__(Post, session)


class TreeView(ModelView):
    list_template = "tree_list.html"
    column_auto_select_related = True
    column_list = [
        "id",
        "name",
        "parent",
    ]
    form_excluded_columns = [
        "children",
    ]
    column_filters = [
        "id",
        "name",
        "parent",
    ]

    # override the 'render' method to pass your own parameters to the template
    def render(self, template, **kwargs):
        return super().render(template, foo="bar", **kwargs)


def format_action_for_export(view, context, model, name):
    """Format action enum for export."""
    return model.action.value if model.action else ""


def format_timestamp_for_export(view, context, model, name):
    """Format timestamp for export."""
    return model.timestamp.strftime("%Y-%m-%d %H:%M:%S") if model.timestamp else ""


class AuditLogAdmin(ModelView):
    """Read-only view for audit log entries."""
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_default_sort = ("timestamp", True)
    column_list = [
        "id",
        "timestamp",
        "action",
        "model_name",
        "record_id",
    ]
    column_details_list = [
        "id",
        "timestamp",
        "action",
        "model_name",
        "record_id",
        "old_values",
        "new_values",
    ]
    column_filters = [
        "action",
        "model_name",
        "record_id",
        "timestamp",
    ]
    column_searchable_list = [
        "model_name",
        "record_id",
    ]

    # CSV Export configuration
    can_export = True
    export_max_rows = 10000
    export_types = ["csv"]

    # Columns to include in export (in order)
    column_export_list = [
        "id",
        "action",
        "model_name",
        "record_id",
        "old_values",
        "new_values",
        "timestamp",
    ]

    # Column labels for export headers
    column_labels = {
        "id": "ID",
        "action": "Action",
        "model_name": "Table Name",
        "record_id": "Record ID",
        "old_values": "Old Values",
        "new_values": "New Values",
        "timestamp": "Timestamp",
    }

    # Formatters for export to ensure proper CSV formatting
    column_formatters_export = {
        "action": format_action_for_export,
        "timestamp": format_timestamp_for_export,
    }


admin = Admin(app, name="Example: SQLAlchemy", theme=Bootstrap4Theme(swatch="default"))

admin.add_view(UserAdmin(User, db))
admin.add_view(ModelView(Tag, db))
admin.add_view(PostAdmin(db))
admin.add_view(TreeView(Tree, db, category="Other"))
admin.add_view(AuditLogAdmin(AuditLog, db, name="Audit Log", category="Other"))
admin.add_sub_category(name="Links", parent_name="Other")
admin.add_link(MenuLink(name="Back Home", url="/", category="Links"))
admin.add_link(
    MenuLink(name="External link", url="http://www.example.com/", category="Links")
)
