from flask_admin.babel import lazy_gettext

from .test_basic import CustomModelView, create_models
from .. import flask_babel_test_decorator


@flask_babel_test_decorator
def test_column_label_translation(request, app):
    # We need to configure the default Babel locale _before_ the `babel` fixture is
    # initialised, so we have to use `request.getfixturevalue` to pull the fixture
    # within the test function rather than the test signature. The `admin` fixture
    # pulls in the `babel` fixture, which will then use the configuration here.
    app.config['BABEL_DEFAULT_LOCALE'] = 'es'
    db = request.getfixturevalue('db')
    admin = request.getfixturevalue('admin')

    with app.app_context():
        Model1, _ = create_models(db)

        label = lazy_gettext('Name')

        view = CustomModelView(Model1, db.session,
                               column_list=['test1', 'test3'],
                               column_labels=dict(test1=label),
                               column_filters=('test1',))
        admin.add_view(view)

        client = app.test_client()

        rv = client.get('/admin/model1/?flt1_0=test')
        assert rv.status_code == 200
        assert '{"Nombre":' in rv.data.decode('utf-8')
