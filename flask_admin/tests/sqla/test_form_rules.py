import pytest

from flask_admin.form import rules

from .test_basic import create_models
from .test_basic import CustomModelView


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_form_rules(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1, param, form_rules=("test2", "test1", rules.Field("test4"))
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        pos1 = data.find("Test1")
        pos2 = data.find("Test2")
        pos3 = data.find("Test3")
        pos4 = data.find("Test4")
        assert pos1 > pos2
        assert pos4 > pos1
        assert pos3 == -1


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_rule_macro(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1,
            param,
            create_template="macro.html",
            form_create_rules=(
                rules.Macro("test", arg="foobar"),
                rules.Macro("test_lib.another_test"),
            ),
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        assert "Value = foobar" in data
        assert "Hello another_test" in data


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_rule_container(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1,
            param,
            create_template="macro.html",
            form_create_rules=(
                rules.Container("wrap", rules.Macro("test_lib.another_test")),
            ),
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        pos1 = data.find("<wrapper>")
        pos2 = data.find("another_test")
        pos3 = data.find("</wrapper>")
        assert pos1 != -1
        assert pos2 != -1
        assert pos3 != -1
        assert pos1 < pos2 < pos3


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_rule_text(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(Model1, param, form_create_rules=(rules.Text("hello"),))
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        assert "hello" in data


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_rule_html(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1, param, form_create_rules=(rules.HTML("<h1>hello</h1>"),)
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        assert "<h1>hello</h1>" in data


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_rule_header(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1, param, form_create_rules=(rules.Header("hello"),)
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        assert "<h3>hello</h3>" in data


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_rule_nested(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1,
            param,
            form_create_rules=(
                rules.NestedRule(
                    rules=[
                        rules.Text("hello1"),
                        rules.Field("test2"),
                        rules.Field("test1"),
                        rules.Field("test4"),
                    ]
                ),
            ),
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        assert "hello1" in data
        pos1 = data.find("Test1")
        pos2 = data.find("Test2")
        pos3 = data.find("Test3")
        pos4 = data.find("Test4")
        assert pos1 > pos2
        assert pos4 > pos1
        assert pos3 == -1


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_rule_row(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1,
            param,
            form_create_rules=(
                rules.Row(
                    rules.Field("test1"),
                    rules.Field("test2"),
                ),
            ),
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        pos1 = data.find("form-row")
        pos2 = data.find("form-group col", pos1)
        pos3 = data.find("Test1", pos2)
        pos4 = data.find("form-group col", pos3)
        pos5 = data.find("Test2", pos4)
        assert pos1 < pos2 < pos3 < pos4 < pos5


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_rule_group(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1,
            param,
            form_create_rules=(
                rules.Group(
                    "test1",
                    prepend="before",
                    append="after",
                ),
            ),
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        pos1 = data.find("form-group")
        pos2 = data.find("Test1", pos1)
        pos3 = data.find("before", pos2)
        pos4 = data.find("form-control", pos3)
        pos5 = data.find("after", pos4)
        assert pos1 < pos2 < pos3 < pos4 < pos5


@pytest.mark.filterwarnings("ignore:Fields missing:UserWarning")
def test_rule_field_set(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1,
            param,
            form_create_rules=(
                rules.FieldSet(
                    ["test2", "test1", "test4", rules.Text("helloworld")], "header"
                ),
            ),
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        assert "<h3>header</h3>" in data
        pos1 = data.find("Test1")
        pos2 = data.find("Test2")
        pos3 = data.find("Test3")
        pos4 = data.find("Test4")
        pos5 = data.find("helloworld")
        assert pos1 > pos2
        assert pos4 > pos1
        assert pos3 == -1
        assert pos5 > pos4


@pytest.mark.filterwarnings(
    "ignore:'iter_groups' is expected to return 4 items tuple since wtforms 3.1, this "
    "will be mandatory in wtforms 3.2:DeprecationWarning",
    "ignore:Fields missing from ruleset.*:UserWarning",
)
def test_rule_inlinefieldlist(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, Model2 = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1,
            param,
            inline_models=(Model2,),
            form_create_rules=("test1", "model2"),
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200


@pytest.mark.filterwarnings(
    "ignore:'iter_groups' is expected to return 4 items tuple since wtforms 3.1, this "
    "will be mandatory in wtforms 3.2:DeprecationWarning",
)
def test_inline_model_rules(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, Model2 = create_models(sqla_db_ext)
        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1,
            param,
            inline_models=[(Model2, dict(form_rules=("string_field", "bool_field")))],
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        data = rv.data.decode("utf-8")
        assert "int_field" not in data
