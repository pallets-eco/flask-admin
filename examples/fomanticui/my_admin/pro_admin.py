import os

from flask import flash
from flask_admin import actions
from flask_admin import Admin
from flask_admin.contrib import rediscli
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_admin.model.form import InlineFormAdmin
from flask_admin.theme import FomanticUI
from models import Address
from models import Attachment
from models import Category
from models import Comment
from models import db
from models import Department
from models import Employee
from models import Order
from models import OrderItem
from models import Payment
from models import Post
from models import Product
from models import Project
from models import Role
from models import Tag
from models import User
from redis import Redis

from .views import IndexView

# ---------------- Generic helpers ----------------


class ReadOnlyModelView(ModelView):
    """A view that disallows create / edit / delete to test read-only mode."""

    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    can_export = True
    export_types = ["csv", "json", "xls", "xlsx", "html", "pdf"]
    page_size_options = (5, 10, 25, 50, 100)


# ---------------- Inline helpers ----------------


class CommentInline(InlineFormAdmin):
    form_columns = ("id", "user", "body", "created_at")


class AddressInline(InlineFormAdmin):
    form_columns = (
        "id",
        "street",
        "city",
        "state",
        "postal_code",
        "country",
        "is_primary",
    )


class OrderItemInline(InlineFormAdmin):
    form_columns = ("id", "product", "quantity", "price")


class PaymentInline(InlineFormAdmin):
    form_columns = ("id", "amount", "method", "paid_at")


# ---------------- Concrete model views ----------------


class ExtendedUserView(ModelView):
    column_list = (
        "id",
        "email",
        "name",
        "age",
        "active",
        "created_at",
        "balance",
    )
    inline_models = (AddressInline(Address),)
    column_searchable_list = ("email", "name")
    column_filters = ("active", "age", "created_at", "balance")
    column_editable_list = ("active",)
    column_default_sort = ("created_at", True)
    can_export = True
    export_types = ["csv", "json", "xlsx"]
    page_size_options = (5, 10, 25, 50)

    @actions.action("activate", "Activate", "Activate selected users?")
    def action_activate(self, ids):
        qry = User.query.filter(User.id.in_(ids))
        count = 0
        for u in qry.all():
            if not u.active:
                u.active = True
                count += 1
        db.session.commit()
        flash(f"Activated {count} users!", "success")


class PostFullView(ModelView):
    column_list = (
        "id",
        "title",
        "author",
        "category",
        "created_at",
        "tags",
    )
    column_searchable_list = ("title", "body")
    column_editable_list = ("title", "category", "author", "tags", "created_at")
    column_filters = ("category", "created_at", "tags")
    column_formatters = {
        "title": lambda v, c, m, p: m.title[:40] + "…"
        if len(m.title) > 40
        else m.title,
    }
    inline_models = [CommentInline(Comment), Attachment]
    form_excluded_columns = ("created_at",)
    page_size_options = (10, 25, 50)


class RoleView(ReadOnlyModelView):
    column_searchable_list = ("name",)


class CategoryView(ModelView):
    column_list = ("id", "name", "description")
    column_searchable_list = ("name",)
    # form_overrides = {"description": "ckeditor"}


class TagView(ReadOnlyModelView):
    column_searchable_list = ("name",)


class CommentView(ReadOnlyModelView):
    column_filters = ("created_at", "post")


class AttachmentView(ReadOnlyModelView):
    column_list = ("id", "filename", "mimetype", "post")
    can_create = True


class ProductView(ModelView):
    column_list = ("id", "name", "price", "stock", "data")
    column_filters = ("price", "stock")
    column_editable_list = ("price", "stock")
    can_export = True
    export_types = ["xlsx", "csv", "json"]
    can_edit = True
    edit_modal = True
    can_create = True


class OrderView(ModelView):
    column_list = ("id", "user", "status", "total_price", "created_at")
    column_filters = ("status", "created_at", "total_price")
    inline_models = [OrderItemInline(OrderItem), PaymentInline(Payment)]
    can_set_page_size = True
    page_size_options = (10, 25, 100)
    column_default_sort = ("created_at", True)


class OrderItemView(ReadOnlyModelView):
    column_list = ("id", "order", "product", "quantity", "price")


class PaymentView(ReadOnlyModelView):
    column_list = ("id", "order", "amount", "method", "paid_at")
    column_filters = ("method",)


class DepartmentView(ModelView):
    column_list = ("id", "name", "budget", "created_at")
    column_searchable_list = ("name",)
    column_filters = ("budget",)
    column_editable_list = ("budget",)


class EmployeeView(ModelView):
    column_list = (
        "id",
        "first_name",
        "last_name",
        "department",
        "salary",
        "hire_date",
        "rating",
    )
    column_searchable_list = ("first_name", "last_name")
    column_filters = ("department", "salary", "hire_date", "rating")
    form_ajax_refs = {"department": {"fields": ("name",)}}
    column_editable_list = ("salary", "rating")
    page_size_options = (10, 25, 50, 100)


class ProjectView(ModelView):
    column_list = ("id", "name", "deadline", "budget")
    column_filters = ("deadline", "budget")
    column_searchable_list = ("name",)
    form_columns = ("employees", "name", "deadline", "budget")
    # form_ajax_refs = {"employees": {"fields": ("first_name", "last_name")}}


# ----------------- Admin instance -----------------

admin = Admin(
    name="ProAdmin",
    theme=FomanticUI(base_template="master.html"),
    index_view=IndexView("Home", endpoint="proadmin", url="/proadmin"),
)


admin.add_link(
    MenuLink(
        name="Support",
        url="https://discord.gg/flask",
        icon_type="default",
        icon_value="life ring",
    )
)

# Files
_path_filemanager = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
admin.add_view(
    FileAdmin(_path_filemanager, name="File Manager", endpoint="p/filemanager")
)

# Redis console
v = rediscli.RedisCli(Redis(), "Redis Console")
v.menu_icon_value = "terminal"
admin.add_view(v)

# General data
admin.add_view(ExtendedUserView(User, db.session, name="Users", endpoint="p/users"))
admin.add_view(
    RoleView(Role, db.session, name="Roles", endpoint="p/roles", category="Reference")
)
admin.add_view(
    CategoryView(
        Category,
        db.session,
        name="Categories",
        endpoint="p/categories",
        category="Reference",
    )
)
admin.add_view(
    TagView(Tag, db.session, name="Tags", endpoint="p/tags", category="Reference")
)

# Blog
admin.add_view(
    PostFullView(Post, db.session, name="Posts", endpoint="p/posts", category="Blog")
)
admin.add_view(
    CommentView(
        Comment, db.session, name="Comments", endpoint="p/comments", category="Blog"
    )
)
admin.add_view(
    AttachmentView(
        Attachment,
        db.session,
        name="Attachments",
        endpoint="p/attachments",
        category="Blog",
    )
)

# Shop
admin.add_view(
    ProductView(
        Product,
        db.session,
        name="Products",
        endpoint="p/products",
        category="E-Commerce",
    )
)
admin.add_view(
    OrderView(
        Order, db.session, name="Orders", endpoint="p/orders", category="E-Commerce"
    )
)
admin.add_view(
    OrderItemView(
        OrderItem,
        db.session,
        name="Order Items",
        endpoint="p/orderitems",
        category="E-Commerce",
    )
)
admin.add_view(
    PaymentView(
        Payment,
        db.session,
        name="Payments",
        endpoint="p/payments",
        category="E-Commerce",
    )
)

admin.add_link(
    MenuLink(
        name="Documentation",
        url="https://flask-admin.readthedocs.io/",
        icon_type="default",
        icon_value="book",
    )
)
admin.add_link(
    MenuLink(
        name="GitHub",
        url="https://github.com/flask-admin/flask-admin",
        icon_type="default",
        icon_value="github",
    )
)
admin.add_link(
    MenuLink(
        name="Support",
        url="https://discord.gg/flask",
        icon_type="default",
        icon_value="life ring",
    )
)

# HR
admin.add_view(
    DepartmentView(
        Department,
        db.session,
        name="Departments",
        endpoint="p/departments",
        category="HR",
    )
)
admin.add_view(
    EmployeeView(
        Employee, db.session, name="Employees", endpoint="p/employees", category="HR"
    )
)
admin.add_view(
    ProjectView(
        Project, db.session, name="Projects", endpoint="p/projects", category="HR"
    )
)
