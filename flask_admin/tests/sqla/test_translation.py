from flask_admin.babel import gettext

from ...contrib.sqla import ModelView
from .. import flask_babel_test_decorator
from .test_basic import create_models
from .test_basic import CustomModelView


@flask_babel_test_decorator
def test_column_label_translation(request, app):
    # We need to configure the default Babel locale _before_ the `babel` fixture is
    # initialised, so we have to use `request.getfixturevalue` to pull the fixture
    # within the test function rather than the test signature. The `admin` fixture
    # pulls in the `babel` fixture, which will then use the configuration here.
    app.config["BABEL_DEFAULT_LOCALE"] = "es"
    db = request.getfixturevalue("db")
    admin = request.getfixturevalue("admin")

    with app.app_context():
        Model1, _ = create_models(db)

        label = gettext("Name")

        view = CustomModelView(
            Model1,
            db.session,
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
def test_unique_validator_translation_is_dynamic(app, db, admin):
    with app.app_context():

        class UniqueTable(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            value = db.Column(db.String, unique=True)

        db.create_all()

        view = ModelView(UniqueTable, db.session)
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
