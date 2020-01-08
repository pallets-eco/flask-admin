from admin import app, db
from admin.models import AVAILABLE_USER_TYPES, User, Post, Tag, Tree
from flask import Markup, send_file

from wtforms import validators

import flask_admin as admin
from flask_admin.base import MenuLink
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla import filters
from flask_admin.contrib.sqla.filters import BaseSQLAFilter, FilterEqual
from flask_admin.babel import gettext


# Flask views
@app.route('/')
def index():
    tmp = u"""
<p><a href="/admin/?lang=en">Click me to get to Admin! (English)</a></p>
<p><a href="/admin/?lang=cs">Click me to get to Admin! (Czech)</a></p>
<p><a href="/admin/?lang=de">Click me to get to Admin! (German)</a></p>
<p><a href="/admin/?lang=es">Click me to get to Admin! (Spanish)</a></p>
<p><a href="/admin/?lang=fa">Click me to get to Admin! (Farsi)</a></p>
<p><a href="/admin/?lang=fr">Click me to get to Admin! (French)</a></p>
<p><a href="/admin/?lang=pt">Click me to get to Admin! (Portuguese)</a></p>
<p><a href="/admin/?lang=ru">Click me to get to Admin! (Russian)</a></p>
<p><a href="/admin/?lang=pa">Click me to get to Admin! (Punjabi)</a></p>
<p><a href="/admin/?lang=zh_CN">Click me to get to Admin! (Chinese - Simplified)</a></p>
<p><a href="/admin/?lang=zh_TW">Click me to get to Admin! (Chinese - Traditional)</a></p>
"""
    return tmp


@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico')


# Custom filter class
class FilterLastNameBrown(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        if value == '1':
            return query.filter(self.column == "Brown")
        else:
            return query.filter(self.column != "Brown")

    def operation(self):
        return 'is Brown'


# Customized User model admin
def phone_number_formatter(view, context, model, name):
    return Markup("<nobr>{}</nobr>".format(model.phone_number)) if model.phone_number else None


def is_numberic_validator(form, field):
    if field.data and not field.data.isdigit():
        raise validators.ValidationError(gettext('Only numbers are allowed.'))


class UserAdmin(sqla.ModelView):

    can_view_details = True  # show a modal dialog with records details
    action_disallowed_list = ['delete', ]

    form_choices = {
        'type': AVAILABLE_USER_TYPES,
    }
    form_args = {
        'dialling_code': {'label': 'Dialling code'},
        'local_phone_number': {
            'label': 'Phone number',
            'validators': [is_numberic_validator]
        },
    }
    form_widget_args = {
        'id': {
            'readonly': True
        }
    }
    column_list = [
        'type',
        'first_name',
        'last_name',
        'email',
        'ip_address',
        'currency',
        'timezone',
        'phone_number',
    ]
    column_searchable_list = [
        'first_name',
        'last_name',
        'phone_number',
        'email',
    ]
    column_editable_list = ['type', 'currency', 'timezone']
    column_details_list = [
        'id',
        'featured_post',
        'website',
        'enum_choice_field',
        'sqla_utils_choice_field',
        'sqla_utils_enum_choice_field',
    ] + column_list
    form_columns = [
        'id',
        'type',
        'featured_post',
        'enum_choice_field',
        'sqla_utils_choice_field',
        'sqla_utils_enum_choice_field',
        'last_name',
        'first_name',
        'email',
        'website',
        'dialling_code',
        'local_phone_number',
    ]
    form_create_rules = [
        'last_name',
        'first_name',
        'type',
        'email',
    ]

    column_auto_select_related = True
    column_default_sort = [('last_name', False), ('first_name', False)]  # sort on multiple columns

    # custom filter: each filter in the list is a filter operation (equals, not equals, etc)
    # filters with the same name will appear as operations under the same filter
    column_filters = [
        'first_name',
        FilterEqual(column=User.last_name, name='Last Name'),
        FilterLastNameBrown(column=User.last_name, name='Last Name',
                            options=(('1', 'Yes'), ('0', 'No'))),
        'phone_number',
        'email',
        'ip_address',
        'currency',
        'timezone',
    ]
    column_formatters = {'phone_number': phone_number_formatter}

    # setup edit forms so that only posts created by this user can be selected as 'featured'
    def edit_form(self, obj):
        return self._filtered_posts(
            super(UserAdmin, self).edit_form(obj)
        )

    def _filtered_posts(self, form):
        form.featured_post.query_factory = lambda: Post.query.filter(Post.user_id == form._obj.id).all()
        return form


# Customized Post model admin
class PostAdmin(sqla.ModelView):
    column_display_pk = True
    column_list = ['id', 'user', 'title', 'date', 'tags', 'background_color', 'created_at', ]
    column_editable_list = ['background_color', ]
    column_default_sort = ('date', True)
    create_modal = True
    edit_modal = True
    column_sortable_list = [
        'id',
        'title',
        'date',
        ('user', ('user.last_name', 'user.first_name')),  # sort on multiple columns
    ]
    column_labels = {
        'title': 'Post Title'  # Rename 'title' column in list view
    }
    column_searchable_list = [
        'title',
        'tags.name',
        'user.first_name',
        'user.last_name',
    ]
    column_labels = {
        'title': 'Title',
        'tags.name': 'Tags',
        'user.first_name': 'User\'s first name',
        'user.last_name': 'Last name',
    }
    column_filters = [
        'id',
        'user.first_name',
        'user.id',
        'background_color',
        'created_at',
        'title',
        'date',
        'tags',
        filters.FilterLike(Post.title, 'Fixed Title', options=(('test1', 'Test 1'), ('test2', 'Test 2'))),
    ]
    can_export = True
    export_max_rows = 1000
    export_types = ['csv', 'xls']

    # Pass arguments to WTForms. In this case, change label for text field to
    # be 'Big Text' and add DataRequired() validator.
    form_args = {
        'text': dict(label='Big Text', validators=[validators.DataRequired()])
    }
    form_widget_args = {
        'text': {
            'rows': 10
        }
    }

    form_ajax_refs = {
        'user': {
            'fields': (User.first_name, User.last_name)
        },
        'tags': {
            'fields': (Tag.name,),
            'minimum_input_length': 0,  # show suggestions, even before any user input
            'placeholder': 'Please select',
            'page_size': 5,
        },
    }

    def __init__(self, session):
        # Just call parent class with predefined model.
        super(PostAdmin, self).__init__(Post, session)


class TreeView(sqla.ModelView):
    list_template = 'tree_list.html'
    column_auto_select_related = True
    column_list = [
        'id',
        'name',
        'parent',
    ]
    form_excluded_columns = ['children', ]
    column_filters = ['id', 'name', 'parent', ]

    # override the 'render' method to pass your own parameters to the template
    def render(self, template, **kwargs):
        return super(TreeView, self).render(template, foo="bar", **kwargs)


# Create admin
admin = admin.Admin(app, name='Example: SQLAlchemy', template_mode='bootstrap3')

# Add views
admin.add_view(UserAdmin(User, db.session))
admin.add_view(sqla.ModelView(Tag, db.session))
admin.add_view(PostAdmin(db.session))
admin.add_view(TreeView(Tree, db.session, category="Other"))
admin.add_sub_category(name="Links", parent_name="Other")
admin.add_link(MenuLink(name='Back Home', url='/', category='Links'))
admin.add_link(MenuLink(name='External link', url='http://www.example.com/', category='Links'))
