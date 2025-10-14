import pytest
from flask import Flask
from flask import url_for

from flask_admin import base


@pytest.fixture
def app():
    app = Flask(__name__, host_matching=True, static_host="static.test.localhost")
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    yield app


def init_admin(app, using_init_app: bool, admin_kwargs):
    if using_init_app:
        admin = base.Admin(**admin_kwargs)
        admin.init_app(app)
    else:
        admin = base.Admin(app, **admin_kwargs)

    return admin


class MockView(base.BaseView):
    # Various properties
    allow_call = True
    allow_access = True
    visible = True

    @base.expose("/")
    def index(self):
        return "Success!"

    @base.expose("/test/")
    def test(self):
        return self.render("mock.html")

    @base.expose("/base/")
    def base(self):
        return self.render("admin/base.html")

    def _handle_view(self, name, **kwargs):
        if self.allow_call:
            return super()._handle_view(name, **kwargs)
        else:
            return "Failure!"

    def is_accessible(self):
        if self.allow_access:
            return super().is_accessible()

        return False

    def is_visible(self):
        if self.visible:
            return super().is_visible()

        return False


@pytest.mark.parametrize("initialise_using_init_app", [True, False])
def test_mounting_on_host_with_variable_is_unsupported(
    app, babel, initialise_using_init_app
):
    with pytest.raises(ValueError) as e:
        init_admin(
            app,
            using_init_app=initialise_using_init_app,
            admin_kwargs=dict(url="/", host="<blah>"),
        )

    assert str(e.value) == (
        "`host` must either be a host name with no variables, to serve all Flask-Admin "
        "routes from a single host, or `*` to match the current request's host."
    )


@pytest.mark.parametrize("initialise_using_init_app", [True, False])
def test_mounting_on_host_with_flask_mismatch(initialise_using_init_app):
    app = Flask(__name__, host_matching=False)

    with pytest.raises(ValueError) as e:
        init_admin(
            app=app,
            using_init_app=initialise_using_init_app,
            admin_kwargs=dict(url="/", host="host"),
        )

    assert str(e.value) == (
        "`host` should only be set if your Flask app is using `host_matching`."
    )


@pytest.mark.parametrize("initialise_using_init_app", [True, False])
def test_mounting_on_subdomain_and_host_is_rejected(
    app, babel, initialise_using_init_app
):
    with pytest.raises(ValueError) as e:
        init_admin(
            app,
            using_init_app=initialise_using_init_app,
            admin_kwargs=dict(url="/", subdomain="subdomain", host="host"),
        )

    assert str(e.value) == "`subdomain` and `host` are mutually-exclusive"


@pytest.mark.parametrize("initialise_using_init_app", [True, False])
def test_mounting_on_host(app, babel, initialise_using_init_app):
    admin = init_admin(
        app,
        using_init_app=initialise_using_init_app,
        admin_kwargs=dict(url="/", host="admin.test.localhost"),
    )
    admin.add_view(MockView())

    client = app.test_client()
    rv = client.get("/mockview/")
    assert rv.status_code == 404

    rv = client.get("/mockview/", headers={"Host": "admin.test.localhost"})
    assert rv.status_code == 200
    assert rv.data == b"Success!"

    client = app.test_client()
    rv = client.get("/mockview/base/")
    assert rv.status_code == 404

    rv = client.get("/mockview/base/", headers={"Host": "admin.test.localhost"})
    assert rv.status_code == 200

    # Check that static assets are embedded with the expected (relative) URLs
    assert (
        b'<link href="/static/admin/bootstrap/bootstrap4/swatch'
        b'/default/bootstrap.min.css?v=4.2.1"' in rv.data
    )
    assert (
        b'<script  src="/static/admin/vendor'
        b'/jquery.min.js?v=3.5.1" type="text/javascript">' in rv.data
    )

    # test static files when url='/'
    with app.test_request_context("/", headers={"Host": "admin.test.localhost"}):
        rv = client.get(
            url_for(
                "admin.static",
                filename="bootstrap/bootstrap4/css/bootstrap.min.css",
            )
        )
        rv.close()
        assert rv.status_code == 404

        rv = client.get(
            url_for(
                "admin.static",
                filename="bootstrap/bootstrap4/css/bootstrap.min.css",
            ),
            headers={"Host": "admin.test.localhost"},
        )
        rv.close()
        assert rv.status_code == 200


@pytest.mark.parametrize("initialise_using_init_app", [True, False])
def test_mounting_on_wildcard_host(app, babel, initialise_using_init_app):
    admin = init_admin(
        app,
        using_init_app=initialise_using_init_app,
        admin_kwargs=dict(url="/", host="*"),
    )
    admin.add_view(MockView())

    client = app.test_client()

    for host_header in [
        {},
        {"Host": "admin.test.localhost"},
        {"Host": "absolutely.any.value"},
    ]:
        rv = client.get("/mockview/base/", headers=host_header)
        rv.close()
        assert rv.status_code == 200

        # Check that static assets are embedded with the expected (relative) URLs
        assert (
            b'<link href="/static/admin/bootstrap/bootstrap4/swatch'
            b'/default/bootstrap.min.css?v=4.2.1"' in rv.data
        )
        assert (
            b'<script  src="/static/admin/vendor'
            b'/jquery.min.js?v=3.5.1" type="text/javascript">' in rv.data
        )

        # test static files when url='/'
        with app.test_request_context("/"):
            rv = client.get(
                url_for(
                    "admin.static",
                    filename="bootstrap/bootstrap4/css/bootstrap.min.css",
                    headers=host_header,
                ),
            )
            rv.close()
            assert rv.status_code == 200
