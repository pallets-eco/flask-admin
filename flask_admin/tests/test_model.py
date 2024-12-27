from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.test import Client
from wtforms import fields

from flask_admin import Admin
from flask_admin import form
from flask_admin._compat import iteritems
from flask_admin._compat import itervalues
from flask_admin.model import base
from flask_admin.model import filters
from flask_admin.model.template import macro
from flask_admin.theme import Bootstrap4Theme


class Model:
    def __init__(self, id=None, c1=1, c2=2, c3=3):
        self.id = id
        self.col1 = c1
        self.col2 = c2
        self.col3 = c3


class Form(form.BaseForm):
    col1 = fields.StringField()
    col2 = fields.StringField()
    col3 = fields.StringField()


class SimpleFilter(filters.BaseFilter):
    def apply(self, query):
        query._applied = True
        return query

    def operation(self):
        return "test"


class MockModelView(base.BaseModelView):
    def __init__(
        self,
        model,
        data=None,
        name=None,
        category=None,
        endpoint=None,
        url=None,
        **kwargs,
    ):
        # Allow to set any attributes from parameters
        for k, v in iteritems(kwargs):
            setattr(self, k, v)

        super().__init__(model, name, category, endpoint, url)

        self.created_models = []
        self.updated_models = []
        self.deleted_models = []

        self.search_arguments = []

        if data is None:
            self.all_models = {1: Model(1), 2: Model(2)}
        else:
            self.all_models = data

        self.last_id = len(self.all_models) + 1

    # Scaffolding
    def get_pk_value(self, model):
        return model.id

    def scaffold_list_columns(self):
        columns = ["col1", "col2", "col3"]

        if self.column_exclude_list:
            return filter(lambda x: x not in self.column_exclude_list, columns)

        return columns

    def init_search(self):
        return bool(self.column_searchable_list)

    def scaffold_filters(self, name):
        return [SimpleFilter(name)]

    def scaffold_sortable_columns(self):
        return ["col1", "col2", "col3"]

    def scaffold_form(self):
        return Form

    # Data
    def get_list(self, page, sort_field, sort_desc, search, filters, page_size=None):
        self.search_arguments.append((page, sort_field, sort_desc, search, filters))
        return len(self.all_models), itervalues(self.all_models)

    def get_one(self, id):
        return self.all_models.get(int(id))

    def create_model(self, form):
        model = Model(self.last_id)
        self.last_id += 1

        form.populate_obj(model)
        self.created_models.append(model)
        self.all_models[model.id] = model

        return True

    def update_model(self, form, model):
        form.populate_obj(model)
        self.updated_models.append(model)
        return True

    def delete_model(self, model):
        self.deleted_models.append(model)
        return True


def test_mockview(app, admin):
    view = MockModelView(Model)
    admin.add_view(view)

    assert view.model == Model

    assert view.name == "Model"
    assert view.endpoint == "model"

    # Verify scaffolding
    assert view._sortable_columns == ["col1", "col2", "col3"]
    assert view._create_form_class == Form
    assert view._edit_form_class == Form
    assert view._search_supported is False
    assert view._filters is None

    client = app.test_client()

    # Make model view requests
    rv = client.get("/admin/model/")
    assert rv.status_code == 200

    # Test model creation view
    rv = client.get("/admin/model/new/")
    assert rv.status_code == 200

    rv = client.post(
        "/admin/model/new/", data=dict(col1="test1", col2="test2", col3="test3")
    )
    assert rv.status_code == 302
    assert len(view.created_models) == 1

    model = view.created_models.pop()
    assert model.id == 3
    assert model.col1 == "test1"
    assert model.col2 == "test2"
    assert model.col3 == "test3"

    # Try model edit view
    rv = client.get("/admin/model/edit/?id=3")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "test1" in data

    rv = client.post(
        "/admin/model/edit/?id=3", data=dict(col1="test!", col2="test@", col3="test#")
    )
    assert rv.status_code == 302
    assert len(view.updated_models) == 1

    model = view.updated_models.pop()
    assert model.col1 == "test!"
    assert model.col2 == "test@"
    assert model.col3 == "test#"

    rv = client.get("/admin/model/edit/?id=4")
    assert rv.status_code == 302

    # Attempt to delete model
    rv = client.post("/admin/model/delete/?id=3")
    assert rv.status_code == 302
    # werkzeug 2.1.0+ returns *relative* location header by default, so just check the
    # end
    assert rv.headers["location"].endswith("/admin/model/")

    # Create a dispatched application to test that edit view's "save and
    # continue" functionality works when app is not located at root
    dummy_app = Flask("dummy_app")
    dispatched_app = DispatcherMiddleware(dummy_app, {"/dispatched": app})
    dispatched_client = Client(dispatched_app)

    rv = dispatched_client.post(
        "/dispatched/admin/model/edit/?id=3&url=/dispatched/admin/model/?flt0_filter%3Dvalue",
        data=dict(
            col1="another test!", col2="test@", col3="test#", _continue_editing="True"
        ),
    )

    # werkzeug 2.1.0+ always returns a `TestResponse` instance (backward-compat as
    # tuple is removed)
    if isinstance(rv, tuple):
        app_iter, status, headers = rv
    else:
        status = rv.status
        headers = rv.headers

    assert status == "302 FOUND"
    assert headers["Location"].endswith(
        "/dispatched/admin/model/edit/?id=3&url=/dispatched/admin/model/?flt0_filter%3Dvalue",
    )
    model = view.updated_models.pop()
    assert model.col1 == "another test!"


def test_permissions(app, admin):
    view = MockModelView(Model)
    admin.add_view(view)

    client = app.test_client()

    view.can_create = False
    rv = client.get("/admin/model/new/")
    assert rv.status_code == 302

    view.can_edit = False
    rv = client.get("/admin/model/edit/?id=1")
    assert rv.status_code == 302

    view.can_delete = False
    rv = client.post("/admin/model/delete/?id=1")
    assert rv.status_code == 302


def test_templates(app, admin):
    view = MockModelView(Model)
    admin.add_view(view)

    client = app.test_client()

    view.list_template = "mock.html"
    view.create_template = "mock.html"
    view.edit_template = "mock.html"

    rv = client.get("/admin/model/")
    assert rv.data == b"Success!"

    rv = client.get("/admin/model/new/")
    assert rv.data == b"Success!"

    rv = client.get("/admin/model/edit/?id=1")
    assert rv.data == b"Success!"


def test_list_columns(app, admin):
    view = MockModelView(
        Model, column_list=["col1", "col3"], column_labels=dict(col1="Column1")
    )
    admin.add_view(view)

    assert len(view._list_columns) == 2
    assert view._list_columns == [("col1", "Column1"), ("col3", "Col3")]

    client = app.test_client()

    rv = client.get("/admin/model/")
    data = rv.data.decode("utf-8")
    assert "Column1" in data
    assert "Col2" not in data


def test_exclude_columns(app, admin):
    view = MockModelView(Model, column_exclude_list=["col2"])
    admin.add_view(view)

    assert view._list_columns == [("col1", "Col1"), ("col3", "Col3")]

    client = app.test_client()

    rv = client.get("/admin/model/")
    data = rv.data.decode("utf-8")
    assert "Col1" in data
    assert "Col2" not in data


def test_sortable_columns(app, admin):
    view = MockModelView(Model, column_sortable_list=["col1", ("col2", "test1")])
    admin.add_view(view)

    assert view._sortable_columns == dict(col1="col1", col2="test1")


def test_column_searchable_list(app, admin):
    view = MockModelView(Model, column_searchable_list=["col1", "col2"])
    admin.add_view(view)

    assert view._search_supported is True

    # TODO: Make calls with search


def test_column_filters(app, admin):
    view = MockModelView(Model, column_filters=["col1", "col2"])
    admin.add_view(view)

    assert len(view._filters) == 2
    assert view._filters[0].name == "col1"
    assert view._filters[1].name == "col2"

    assert [(f["index"] == f["operation"]) for f in view._filter_groups["col1"]], [
        (0, "test")
    ]
    assert [(f["index"] == f["operation"]) for f in view._filter_groups["col2"]], [
        (1, "test")
    ]

    # TODO: Make calls with filters


def test_filter_list_callable(app, admin):
    flt = SimpleFilter("test", options=lambda: [("1", "Test 1"), ("2", "Test 2")])

    view = MockModelView(Model, column_filters=[flt])
    admin.add_view(view)

    opts = flt.get_options(view)
    assert len(opts) == 2
    assert opts == [("1", "Test 1"), ("2", "Test 2")]


def test_form():
    # TODO: form_columns
    # TODO: form_excluded_columns
    # TODO: form_args
    # TODO: form_widget_args
    pass


def test_csrf(app, admin):
    class SecureModelView(MockModelView):
        form_base_class = form.SecureForm

        def scaffold_form(self):
            return form.SecureForm

    def get_csrf_token(data):
        data = data.split('name="csrf_token" type="hidden" value="')[1]
        token = data.split('"')[0]
        return token

    view = SecureModelView(Model, endpoint="secure")
    admin.add_view(view)

    client = app.test_client()

    ################
    # create_view
    ################
    rv = client.get("/admin/secure/new/")
    assert rv.status_code == 200
    assert 'name="csrf_token"' in rv.data.decode("utf-8")

    csrf_token = get_csrf_token(rv.data.decode("utf-8"))

    # Create without CSRF token
    rv = client.post("/admin/secure/new/", data=dict(name="test1"))
    assert rv.status_code == 200

    # Create with CSRF token
    rv = client.post(
        "/admin/secure/new/", data=dict(name="test1", csrf_token=csrf_token)
    )
    assert rv.status_code == 302

    ###############
    # edit_view
    ###############
    rv = client.get("/admin/secure/edit/?url=%2Fadmin%2Fsecure%2F&id=1")
    assert rv.status_code == 200
    assert 'name="csrf_token"' in rv.data.decode("utf-8")

    csrf_token = get_csrf_token(rv.data.decode("utf-8"))

    # Edit without CSRF token
    rv = client.post(
        "/admin/secure/edit/?url=%2Fadmin%2Fsecure%2F&id=1", data=dict(name="test1")
    )
    assert rv.status_code == 200

    # Edit with CSRF token
    rv = client.post(
        "/admin/secure/edit/?url=%2Fadmin%2Fsecure%2F&id=1",
        data=dict(name="test1", csrf_token=csrf_token),
    )
    assert rv.status_code == 302

    ################
    # delete_view
    ################
    rv = client.get("/admin/secure/")
    assert rv.status_code == 200
    assert 'name="csrf_token"' in rv.data.decode("utf-8")

    csrf_token = get_csrf_token(rv.data.decode("utf-8"))

    # Delete without CSRF token, test validation errors
    rv = client.post(
        "/admin/secure/delete/",
        data=dict(id="1", url="/admin/secure/"),
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "Record was successfully deleted." not in rv.data.decode("utf-8")
    assert "Failed to delete record." in rv.data.decode("utf-8")

    # Delete with CSRF token
    rv = client.post(
        "/admin/secure/delete/",
        data=dict(id="1", url="/admin/secure/", csrf_token=csrf_token),
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "Record was successfully deleted." in rv.data.decode("utf-8")

    ################
    # actions
    ################
    rv = client.get("/admin/secure/")
    assert rv.status_code == 200
    assert 'name="csrf_token"' in rv.data.decode("utf-8")

    csrf_token = get_csrf_token(rv.data.decode("utf-8"))

    # Delete without CSRF token, test validation errors
    rv = client.post(
        "/admin/secure/action/",
        data=dict(rowid="1", url="/admin/secure/", action="delete"),
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert "Record was successfully deleted." not in rv.data.decode("utf-8")
    assert "Failed to perform action." in rv.data.decode("utf-8")


def test_custom_form(app, admin):
    class TestForm(form.BaseForm):
        pass

    view = MockModelView(Model, form=TestForm)
    admin.add_view(view)

    assert view._create_form_class == TestForm
    assert view._edit_form_class == TestForm

    assert not hasattr(view._create_form_class, "col1")


def test_modal_edit_bs4(app, babel):
    admin_bs4 = Admin(app, theme=Bootstrap4Theme())

    edit_modal_on = MockModelView(Model, edit_modal=True, endpoint="edit_modal_on")
    edit_modal_off = MockModelView(Model, edit_modal=False, endpoint="edit_modal_off")
    create_modal_on = MockModelView(
        Model, create_modal=True, endpoint="create_modal_on"
    )
    create_modal_off = MockModelView(
        Model, create_modal=False, endpoint="create_modal_off"
    )
    admin_bs4.add_view(edit_modal_on)
    admin_bs4.add_view(edit_modal_off)
    admin_bs4.add_view(create_modal_on)
    admin_bs4.add_view(create_modal_off)

    client_bs4 = app.test_client()

    # bootstrap 2 - ensure modal window is added when edit_modal is enabled
    rv = client_bs4.get("/admin/edit_modal_on/")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "fa_modal_window" in data

    # bootstrap 2 - test edit modal disabled
    rv = client_bs4.get("/admin/edit_modal_off/")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "fa_modal_window" not in data

    # bootstrap 2 - ensure modal window is added when create_modal is enabled
    rv = client_bs4.get("/admin/create_modal_on/")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "fa_modal_window" in data

    # bootstrap 2 - test create modal disabled
    rv = client_bs4.get("/admin/create_modal_off/")
    assert rv.status_code == 200
    data = rv.data.decode("utf-8")
    assert "fa_modal_window" not in data


def check_class_name():
    class DummyView(MockModelView):
        pass

    view = DummyView(Model)
    assert view.name == "Dummy View"


def test_export_csv(app, admin):
    client = app.test_client()

    # test redirect when csv export is disabled
    view = MockModelView(Model, column_list=["col1", "col2"], endpoint="test")
    admin.add_view(view)

    # basic test of csv export with a few records
    view_data = {
        1: Model(1, "col1_1", "col2_1"),
        2: Model(2, "col1_2", "col2_2"),
        3: Model(3, "col1_3", "col2_3"),
    }

    view2 = MockModelView(
        Model, view_data, can_export=True, column_list=["col1", "col2"]
    )
    admin.add_view(view2)

    # test explicit use of column_export_list
    view3 = MockModelView(
        Model,
        view_data,
        can_export=True,
        column_list=["col1", "col2"],
        column_export_list=["id", "col1", "col2"],
        endpoint="exportinclusion",
    )
    admin.add_view(view3)

    # test explicit use of column_export_exclude_list
    view4 = MockModelView(
        Model,
        view_data,
        can_export=True,
        column_list=["col1", "col2"],
        column_export_exclude_list=["col2"],
        endpoint="exportexclusion",
    )
    admin.add_view(view4)

    # test utf8 characters in csv export
    view_data_v2 = {**view_data, 4: Model(1, "\u2013ut8_1\u2013", "\u2013utf8_2\u2013")}
    view5 = MockModelView(
        Model,
        view_data_v2,
        can_export=True,
        column_list=["col1", "col2"],
        endpoint="utf8",
    )
    admin.add_view(view5)

    # test None type, integer type, column_labels, and column_formatters
    view_data_v3 = {
        1: Model(1, "col1_1", 1),
        2: Model(2, "col1_2", 2),
        3: Model(3, None, 3),
    }

    view6 = MockModelView(
        Model,
        view_data_v3,
        can_export=True,
        column_list=["col1", "col2"],
        column_labels={"col1": "Str Field", "col2": "Int Field"},
        column_formatters=dict(col2=lambda v, c, m, p: m.col2 * 2),
        endpoint="types_and_formatters",
    )
    admin.add_view(view6)

    # test column_formatters_export and column_formatters_export
    type_formatters = {type(None): lambda view, value, name: "null"}

    view7 = MockModelView(
        Model,
        view_data_v3,
        can_export=True,
        column_list=["col1", "col2"],
        column_formatters_export=dict(col2=lambda v, c, m, p: m.col2 * 3),
        column_formatters=dict(col2=lambda v, c, m, p: m.col2 * 2),  # overridden
        column_type_formatters_export=type_formatters,
        endpoint="export_types_and_formatters",
    )
    admin.add_view(view7)

    # Macros are not implemented for csv export yet and will throw an error
    view8 = MockModelView(
        Model,
        can_export=True,
        column_list=["col1", "col2"],
        column_formatters=dict(col1=macro("render_macro")),
        endpoint="macro_exception",
    )
    admin.add_view(view8)

    # We should be able to specify column_formatters_export
    # and not get an exception if a column_formatter is using a macro
    def export_formatter(v, c, m, p):
        return m.col1 if m else ""

    view9 = MockModelView(
        Model,
        view_data_v3,
        can_export=True,
        column_list=["col1", "col2"],
        column_formatters=dict(col1=macro("render_macro")),
        column_formatters_export=dict(col1=export_formatter),
        endpoint="macro_exception_formatter_override",
    )
    admin.add_view(view9)

    # We should not get an exception if a column_formatter is
    # using a macro but it is on the column_export_exclude_list
    view10 = MockModelView(
        Model,
        view_data_v3,
        can_export=True,
        column_list=["col1", "col2"],
        column_formatters=dict(col1=macro("render_macro")),
        column_export_exclude_list=["col1"],
        endpoint="macro_exception_exclude_override",
    )
    admin.add_view(view10)

    # When we use column_export_list to hide the macro field
    # we should not get an exception
    view11 = MockModelView(
        Model,
        view_data_v3,
        can_export=True,
        column_list=["col1", "col2"],
        column_formatters=dict(col1=macro("render_macro")),
        column_export_list=["col2"],
        endpoint="macro_exception_list_override",
    )
    admin.add_view(view11)

    # If they define a macro on the column_formatters_export list
    # then raise an exception
    view12 = MockModelView(
        Model,
        view_data_v3,
        can_export=True,
        column_list=["col1", "col2"],
        column_formatters=dict(col1=macro("render_macro")),
        endpoint="macro_exception_macro_override",
    )
    admin.add_view(view12)

    rv = client.get("/admin/test/export/csv/")
    assert rv.status_code == 302

    rv = client.get("/admin/model/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.mimetype == "text/csv"
    assert rv.status_code == 200
    assert (
        "Col1,Col2\r\n"
        + "col1_1,col2_1\r\n"
        + "col1_2,col2_2\r\n"
        + "col1_3,col2_3\r\n"
        == data
    )

    rv = client.get("/admin/exportinclusion/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.mimetype == "text/csv"
    assert rv.status_code == 200
    assert (
        "Id,Col1,Col2\r\n"
        + "1,col1_1,col2_1\r\n"
        + "2,col1_2,col2_2\r\n"
        + "3,col1_3,col2_3\r\n"
        == data
    )

    rv = client.get("/admin/exportexclusion/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.mimetype == "text/csv"
    assert rv.status_code == 200
    assert "Col1\r\n" + "col1_1\r\n" + "col1_2\r\n" + "col1_3\r\n" == data

    rv = client.get("/admin/utf8/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert "\u2013ut8_1\u2013,\u2013utf8_2\u2013\r\n" in data

    rv = client.get("/admin/types_and_formatters/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert (
        "Str Field,Int Field\r\n" + "col1_1,2\r\n" + "col1_2,4\r\n" + ",6\r\n" == data
    )

    rv = client.get("/admin/export_types_and_formatters/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert "Col1,Col2\r\n" + "col1_1,3\r\n" + "col1_2,6\r\n" + "null,9\r\n" == data

    rv = client.get("/admin/macro_exception/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 500

    rv = client.get("/admin/macro_exception_formatter_override/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert "Col1,Col2\r\n" + "col1_1,1\r\n" + "col1_2,2\r\n" + ",3\r\n" == data

    rv = client.get("/admin/macro_exception_exclude_override/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert "Col2\r\n" + "1\r\n" + "2\r\n" + "3\r\n" == data

    rv = client.get("/admin/macro_exception_list_override/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 200
    assert "Col2\r\n" + "1\r\n" + "2\r\n" + "3\r\n" == data

    rv = client.get("/admin/macro_exception_macro_override/export/csv/")
    data = rv.data.decode("utf-8")
    assert rv.status_code == 500


def test_export_tablib(app, admin):
    client = app.test_client()

    # basic test of tsv export with a few records using tablib
    view_data = {
        1: Model(1, "col1_1", "col2_1"),
        2: Model(2, "col1_2", "col2_2"),
        3: Model(3, "col1_3", "col2_3"),
    }

    view = MockModelView(
        Model,
        view_data,
        can_export=True,
        column_list=["col1", "col2"],
        export_types=["tsv"],
    )
    admin.add_view(view)

    rv = client.get("/admin/model/export/tsv/")
    data = rv.data.decode("utf-8")
    assert rv.mimetype == "text/tab-separated-values"
    assert rv.status_code == 200
    assert (
        "Col1\tCol2\r\n"
        + "col1_1\tcol2_1\r\n"
        + "col1_2\tcol2_2\r\n"
        + "col1_3\tcol2_3\r\n"
        == data
    )


def test_list_row_actions(app, admin):
    client = app.test_client()

    from flask_admin.model import template

    # Test default actions
    view = MockModelView(Model, endpoint="test")
    admin.add_view(view)

    actions = view.get_list_row_actions()
    assert isinstance(actions[0], template.EditRowAction)
    assert isinstance(actions[1], template.DeleteRowAction)

    # Test default actions
    view = MockModelView(
        Model, endpoint="test1", can_edit=False, can_delete=False, can_view_details=True
    )
    admin.add_view(view)

    actions = view.get_list_row_actions()
    assert len(actions) == 1
    assert isinstance(actions[0], template.ViewRowAction)

    # Test popups
    view = MockModelView(
        Model,
        endpoint="test2",
        can_view_details=True,
        details_modal=True,
        edit_modal=True,
    )
    admin.add_view(view)

    actions = view.get_list_row_actions()
    assert isinstance(actions[0], template.ViewPopupRowAction)
    assert isinstance(actions[1], template.EditPopupRowAction)
    assert isinstance(actions[2], template.DeleteRowAction)

    # Test custom views
    view = MockModelView(
        Model,
        endpoint="test3",
        column_extra_row_actions=[
            template.LinkRowAction(
                "glyphicon glyphicon-off", "http://localhost/?id={row_id}"
            ),
            template.EndpointLinkRowAction(
                "glyphicon glyphicon-test", "test1.index_view"
            ),
        ],
    )
    admin.add_view(view)

    actions = view.get_list_row_actions()
    assert isinstance(actions[0], template.EditRowAction)
    assert isinstance(actions[1], template.DeleteRowAction)
    assert isinstance(actions[2], template.LinkRowAction)
    assert isinstance(actions[3], template.EndpointLinkRowAction)

    rv = client.get("/admin/test/")
    assert rv.status_code == 200

    rv = client.get("/admin/test1/")
    assert rv.status_code == 200

    rv = client.get("/admin/test2/")
    assert rv.status_code == 200

    rv = client.get("/admin/test3/")
    assert rv.status_code == 200

    data = rv.data.decode("utf-8")

    assert "glyphicon-off" in data
    assert "http://localhost/?id=" in data
    assert "glyphicon-test" in data
