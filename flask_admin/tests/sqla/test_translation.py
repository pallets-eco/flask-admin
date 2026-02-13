from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from flask_admin.babel import gettext

from ...contrib.sqla import ModelView
from .. import flask_babel_test_decorator
from .test_basic import create_models
from .test_basic import CustomModelView


@flask_babel_test_decorator
def test_column_label_translation(request, app, session_or_db, sqla_db_ext):
    # We need to configure the default Babel locale _before_ the `babel` fixture is
    # initialised, so we have to use `request.getfixturevalue` to pull the fixture
    # within the test function rather than the test signature. The `admin` fixture
    # pulls in the `babel` fixture, which will then use the configuration here.
    app.config["BABEL_DEFAULT_LOCALE"] = "es"
    admin = request.getfixturevalue("admin")

    with app.app_context():
        Model1, _ = create_models(sqla_db_ext)

        label = gettext("Name")

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(
            Model1,
            param,
            column_list=["test1", "test3"],
            column_labels=dict(test1=label),
            column_filters=("test1",),
        )
        admin.add_view(view)

        client = app.test_client()

        rv = client.get("/admin/model1/?flt1_0=test")
        assert rv.status_code == 200
        assert '{"Nombre":' in rv.data.decode("utf-8")


@flask_babel_test_decorator
def test_unique_validator_translation_is_dynamic(
    app, sqla_db_ext, admin, session_or_db
):
    with app.app_context():

        class UniqueTable(sqla_db_ext.Base):  # type: ignore[name-defined, misc]
            __tablename__ = "uniquetable"
            id = Column(Integer, primary_key=True)
            value = Column(String, unique=True)

        sqla_db_ext.create_all()

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = ModelView(UniqueTable, param)
        view.can_create = True
        admin.add_view(view)

        client = app.test_client()
        rv = client.post(
            "/admin/uniquetable/new",
            data=dict(id="1", value="hello"),
            follow_redirects=True,
        )
        assert rv.status_code == 200

        rv = client.post(
            "/admin/uniquetable/new",
            data=dict(id="1", value="hello"),
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert "Already exists." in rv.text

        from flask_babel import force_locale

        with force_locale("fr"):
            rv = client.post(
                "/admin/uniquetable/new",
                data=dict(id="1", value="hello"),
                follow_redirects=True,
            )
            assert rv.status_code == 200
            assert "Existe déjà." in rv.text
