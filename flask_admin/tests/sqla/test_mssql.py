import sqlalchemy as sa

from flask_admin.contrib.sqla import ModelView


def test_pagination(app, mssql_db, mssql_admin):
    with app.app_context():

        class Model3(mssql_db.Model):  # type: ignore[name-defined, misc]
            def __init__(self, id=None, test1=None):
                self.id = id
                self.test1 = test1

            id = mssql_db.Column(sa.Integer, primary_key=True)
            test1 = mssql_db.Column(sa.String(20))

        mssql_db.drop_all()
        mssql_db.create_all()

        view3 = ModelView(Model3, mssql_db.session)
        view3.page_size = 10
        view3.column_default_sort = ("test1", False)
        mssql_admin.add_view(view3)

        models = [Model3(id=i, test1=f"test-{i:02d}") for i in range(10, 100)]
        mssql_db.session.add_all(models)
        mssql_db.session.commit()

        client = app.test_client()

        # test default page
        rv = client.get("/admin/model3/")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-10" in data
        assert "test-12" in data
        assert "test-13" in data
        assert "test-19" in data
        assert "test-20" not in data

        # test second page
        rv = client.get("/admin/model3/?page=1")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-11" not in data
        assert "test-21" in data
        assert "test-22" in data
        assert "test-23" in data
        assert "test-29" in data

        # test third page
        rv = client.get("/admin/model3/?page=2")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-11" not in data
        assert "test-21" not in data
        assert "test-31" in data
        assert "test-32" in data
        assert "test-39" in data


def test_pagination_2_PKs(app, mssql_db, mssql_admin):
    with app.app_context():

        class Model4(mssql_db.Model):  # type: ignore[name-defined, misc]
            def __init__(self, id=None, id2=None, test1=None):
                self.id = id
                self.id2 = id2
                self.test1 = test1

            id = mssql_db.Column(sa.Integer, primary_key=True)
            id2 = mssql_db.Column(sa.Integer, primary_key=True)
            test1 = mssql_db.Column(sa.String(20))

        mssql_db.drop_all()
        mssql_db.create_all()

        view4 = ModelView(Model4, mssql_db.session, endpoint="model4")
        view4.page_size = 10
        view4.column_default_sort = ("test1", False)
        mssql_admin.add_view(view4)

        models = [Model4(id=i, id2=i, test1=f"test-{i:02d}") for i in range(10, 100)]
        mssql_db.session.add_all(models)
        mssql_db.session.commit()

        assert Model4.query.count() == 90

        client = app.test_client()

        # test first default page
        rv = client.get("/admin/model4/")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-10" in data
        assert "test-11" in data
        assert "test-12" in data
        assert "test-20" not in data

        # test second page
        rv = client.get("/admin/model4/?page=1")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-19" not in data
        assert "test-21" in data
        assert "test-22" in data
        assert "test-30" not in data

        # test second page
        rv = client.get("/admin/model4/?page=1&sort=bougs")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert "test-19" not in data
        assert "test-21" in data
        assert "test-29" in data
        assert "test-30" not in data
