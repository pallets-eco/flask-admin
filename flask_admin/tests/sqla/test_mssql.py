import sqlalchemy as sa

from .test_basic import CustomModelView


def test_pagination(app, mssql_db, mssql_admin):
    with app.app_context():

        class Model3(mssql_db.Model):  # type: ignore[name-defined]
            def __init__(self, id=None, test1=None):
                self.id = id
                self.test1 = test1

            id = mssql_db.Column(sa.Integer, primary_key=True)
            test1 = mssql_db.Column(sa.String(20))

        mssql_db.drop_all()
        mssql_db.create_all()

        view3 = CustomModelView(Model3, mssql_db.session, page_size=10)
        mssql_admin.add_view(view3)

        for i in range(1, 100):
            m = Model3(id=i, test1=f"test-{i}")
            mssql_db.session.add(m)

        assert Model3.query.count() == 99

        client = app.test_client()

        # test default page
        rv = client.get("/admin/model3/")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-1" in data
        assert "test-10" in data
        assert "test-11" not in data

        # test second page
        rv = client.get("/admin/model3/?page=1")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-10" not in data
        assert "test-11" in data
        assert "test-20" in data
        assert "test-21" not in data


def test_pagination_2_PKs(app, mssql_db, mssql_admin):
    with app.app_context():

        class Model4(mssql_db.Model):  # type: ignore[name-defined]
            def __init__(self, id=None, id2=None, test1=None):
                self.id = id
                self.id2 = id2
                self.test1 = test1

            id = mssql_db.Column(sa.Integer, primary_key=True)
            id2 = mssql_db.Column(sa.Integer, primary_key=True)
            test1 = mssql_db.Column(sa.String(20))

        mssql_db.drop_all()
        mssql_db.create_all()

        view4 = CustomModelView(
            Model4, mssql_db.session, page_size=10, endpoint="model4"
        )
        mssql_admin.add_view(view4)

        for i in range(1, 100):
            m = Model4(id=i, id2=i, test1=f"test-{i}")
            mssql_db.session.add(m)

        assert Model4.query.count() == 99

        client = app.test_client()

        # test first default page
        rv = client.get("/admin/model4/")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-1" in data
        assert "test-10" in data
        assert "test-11" not in data

        # test second page
        rv = client.get("/admin/model4/?page=1")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-10" not in data
        assert "test-11" in data
        assert "test-20" in data
        assert "test-21" not in data

        # test second page
        rv = client.get("/admin/model4/?page=1&sort=bougs")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-10" not in data
        assert "test-11" in data
        assert "test-20" in data
        assert "test-21" not in data
