from flask_admin.babel import lazy_gettext
from flask_babelex import Babel

from . import setup
from .test_basic import CustomModelView, create_models


def test_column_label_translation():
    app, db, admin = setup()

    with app.app_context():
        Model1, _ = create_models(db)

        app.config['BABEL_DEFAULT_LOCALE'] = 'es'
        Babel(app)

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
