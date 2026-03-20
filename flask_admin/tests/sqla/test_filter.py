from datetime import datetime
from datetime import time

import pytest

from flask_admin.contrib.sqla import filters
from flask_admin.tests.sqla.test_basic import create_models
from flask_admin.tests.sqla.test_basic import CustomModelView
from flask_admin.tests.sqla.test_basic import fill_db


def test_column_filters(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, Model2 = create_models(sqla_db_ext)

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view1 = CustomModelView(Model1, param, column_filters=["test1"])
        admin.add_view(view1)

        client = app.test_client()
        assert view1._filters
        assert len(view1._filters) == 7

        # Generate views
        view2 = CustomModelView(Model2, param, column_filters=["model1"])

        view5 = CustomModelView(
            Model1, param, column_filters=["test1"], endpoint="_strings"
        )
        admin.add_view(view5)

        view6 = CustomModelView(Model2, param, column_filters=["int_field"])
        admin.add_view(view6)

        view7 = CustomModelView(
            Model1, param, column_filters=["bool_field"], endpoint="_bools"
        )
        admin.add_view(view7)

        view8 = CustomModelView(
            Model2, param, column_filters=["float_field"], endpoint="_float"
        )
        admin.add_view(view8)

        view9 = CustomModelView(
            Model2,
            param,
            endpoint="_model2",
            column_filters=["model1.bool_field"],
            column_list=[
                "string_field",
                "model1.id",
                "model1.bool_field",
            ],
        )
        admin.add_view(view9)

        view10 = CustomModelView(
            Model1,
            param,
            column_filters=["test1"],
            endpoint="_model3",
            named_filter_urls=True,
        )
        admin.add_view(view10)

        view11 = CustomModelView(
            Model1,
            param,
            column_filters=["date_field", "datetime_field", "time_field"],
            endpoint="_datetime",
        )
        admin.add_view(view11)

        view12 = CustomModelView(
            Model1, param, column_filters=["enum_field"], endpoint="_enumfield"
        )
        admin.add_view(view12)

        view13 = CustomModelView(
            Model2,
            param,
            column_filters=[filters.FilterEqual(Model1.test1, "Test1")],
            endpoint="_relation_test",
        )
        admin.add_view(view13)

        view14 = CustomModelView(
            Model1,
            param,
            column_filters=["enum_type_field"],
            endpoint="_enumtypefield",
        )
        admin.add_view(view14)
        # Test views
        assert view1._filter_groups
        assert [
            (f["index"], f["operation"]) for f in view1._filter_groups["Test1"]
        ] == [
            (0, "contains"),
            (1, "not contains"),
            (2, "equals"),
            (3, "not equal"),
            (4, "empty"),
            (5, "in list"),
            (6, "not in list"),
        ]
        assert view2._filter_groups
        # Test filter that references property0
        assert [
            (f["index"], f["operation"]) for f in view2._filter_groups["Model1 / Test1"]
        ] == [
            (0, "contains"),
            (1, "not contains"),
            (2, "equals"),
            (3, "not equal"),
            (4, "empty"),
            (5, "in list"),
            (6, "not in list"),
        ]

        assert [
            (f["index"], f["operation"]) for f in view2._filter_groups["Model1 / Test2"]
        ] == [
            (7, "contains"),
            (8, "not contains"),
            (9, "equals"),
            (10, "not equal"),
            (11, "empty"),
            (12, "in list"),
            (13, "not in list"),
        ]

        assert [
            (f["index"], f["operation"]) for f in view2._filter_groups["Model1 / Test3"]
        ] == [
            (14, "contains"),
            (15, "not contains"),
            (16, "equals"),
            (17, "not equal"),
            (18, "empty"),
            (19, "in list"),
            (20, "not in list"),
        ]

        assert [
            (f["index"], f["operation"]) for f in view2._filter_groups["Model1 / Test4"]
        ] == [
            (21, "contains"),
            (22, "not contains"),
            (23, "equals"),
            (24, "not equal"),
            (25, "empty"),
            (26, "in list"),
            (27, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Bool Field"]
        ] == [
            (28, "equals"),
            (29, "not equal"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Date Field"]
        ] == [
            (30, "equals"),
            (31, "not equal"),
            (32, "greater than"),
            (33, "smaller than"),
            (34, "between"),
            (35, "not between"),
            (36, "empty"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Time Field"]
        ] == [
            (37, "equals"),
            (38, "not equal"),
            (39, "greater than"),
            (40, "smaller than"),
            (41, "between"),
            (42, "not between"),
            (43, "empty"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Datetime Field"]
        ] == [
            (44, "equals"),
            (45, "not equal"),
            (46, "greater than"),
            (47, "smaller than"),
            (48, "between"),
            (49, "not between"),
            (50, "empty"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Email Field"]
        ] == [
            (51, "contains"),
            (52, "not contains"),
            (53, "equals"),
            (54, "not equal"),
            (55, "empty"),
            (56, "in list"),
            (57, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Enum Field"]
        ] == [
            (58, "equals"),
            (59, "not equal"),
            (60, "empty"),
            (61, "in list"),
            (62, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Enum Type Field"]
        ] == [
            (63, "equals"),
            (64, "not equal"),
            (65, "empty"),
            (66, "in list"),
            (67, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Choice Field"]
        ] == [
            (68, "contains"),
            (69, "not contains"),
            (70, "equals"),
            (71, "not equal"),
            (72, "empty"),
            (73, "in list"),
            (74, "not in list"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Sqla Utils Choice"]
        ] == [
            (75, "equals"),
            (76, "not equal"),
            (77, "contains"),
            (78, "not contains"),
            (79, "empty"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view2._filter_groups["Model1 / Sqla Utils Enum"]
        ] == [
            (80, "equals"),
            (81, "not equal"),
            (82, "contains"),
            (83, "not contains"),
            (84, "empty"),
        ]

        # Test filter with a dot
        view3 = CustomModelView(Model2, param, column_filters=["model1.bool_field"])
        assert view3._filter_groups
        assert [
            (f["index"], f["operation"])
            for f in view3._filter_groups["model1 / Model1 / Bool Field"]
        ] == [
            (0, "equals"),
            (1, "not equal"),
        ]

        # Test column_labels on filters
        view4 = CustomModelView(
            Model2,
            param,
            column_filters=["model1.bool_field", "string_field"],
            column_labels={
                "model1.bool_field": "Test Filter #1",
                "string_field": "Test Filter #2",
            },
        )
        assert view4._filter_groups
        assert list(view4._filter_groups.keys()) == ["Test Filter #1", "Test Filter #2"]

        fill_db(sqla_db_ext, Model1, Model2)

        # Test equals
        rv = client.get("/admin/model1/?flt0_0=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        # the filter value is always in "data"
        # need to check a different column than test1 for the expected row

        assert "test2_val_1" in data
        assert "test1_val_2" not in data

        # Test NOT IN filter
        rv = client.get("/admin/model1/?flt0_6=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")

        assert "test1_val_2" in data
        assert "test2_val_1" not in data

        # Test string filter
        assert view5._filter_groups
        assert [
            (f["index"], f["operation"]) for f in view5._filter_groups["Test1"]
        ] == [
            (0, "contains"),
            (1, "not contains"),
            (2, "equals"),
            (3, "not equal"),
            (4, "empty"),
            (5, "in list"),
            (6, "not in list"),
        ]

        # string - equals
        rv = client.get("/admin/_strings/?flt0_0=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test1_val_2" not in data

        # string - not equal
        rv = client.get("/admin/_strings/?flt0_1=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test1_val_2" in data

        # string - contains
        rv = client.get("/admin/_strings/?flt0_2=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test1_val_2" not in data

        # string - not contains
        rv = client.get("/admin/_strings/?flt0_3=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test1_val_2" in data

        # string - empty
        rv = client.get("/admin/_strings/?flt0_4=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "empty_obj" in data
        assert "test1_val_1" not in data
        assert "test1_val_2" not in data

        # string - not empty
        rv = client.get("/admin/_strings/?flt0_4=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "empty_obj" not in data
        assert "test1_val_1" in data
        assert "test1_val_2" in data

        # string - in list
        rv = client.get("/admin/_strings/?flt0_5=test1_val_1%2Ctest1_val_2")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test1_val_3" not in data
        assert "test1_val_4" not in data

        # string - not in list
        rv = client.get("/admin/_strings/?flt0_6=test1_val_1%2Ctest1_val_2")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test1_val_3" in data
        assert "test1_val_4" in data

        # Test integer filter
        assert view6._filter_groups
        assert [
            (f["index"], f["operation"]) for f in view6._filter_groups["Int Field"]
        ] == [
            (0, "equals"),
            (1, "not equal"),
            (2, "greater than"),
            (3, "smaller than"),
            (4, "empty"),
            (5, "in list"),
            (6, "not in list"),
        ]

        # integer - equals
        rv = client.get("/admin/model2/?flt0_0=5000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" in data
        assert "test2_val_4" not in data

        # integer - equals (huge number)
        rv = client.get("/admin/model2/?flt0_0=6169453081680413441")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_5" in data
        assert "test2_val_4" not in data

        # integer - equals - test validation
        rv = client.get("/admin/model2/?flt0_0=badval")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "Invalid Filter Value" in data

        # integer - not equal
        rv = client.get("/admin/model2/?flt0_1=5000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" not in data
        assert "test2_val_4" in data

        # integer - greater
        rv = client.get("/admin/model2/?flt0_2=6000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" not in data
        assert "test2_val_4" in data

        # integer - smaller
        rv = client.get("/admin/model2/?flt0_3=6000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" in data
        assert "test2_val_4" not in data

        # integer - empty
        rv = client.get("/admin/model2/?flt0_4=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test2_val_3" not in data
        assert "test2_val_4" not in data

        # integer - not empty
        rv = client.get("/admin/model2/?flt0_4=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test2_val_3" in data
        assert "test2_val_4" in data

        # integer - in list
        rv = client.get("/admin/model2/?flt0_5=5000%2C9000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test2_val_3" in data
        assert "test2_val_4" in data

        # integer - in list (huge number)
        rv = client.get("/admin/model2/?flt0_5=6169453081680413441")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_5" in data

        # integer - in list - test validation
        rv = client.get("/admin/model2/?flt0_5=5000%2Cbadval")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "Invalid Filter Value" in data

        # integer - not in list
        rv = client.get("/admin/model2/?flt0_6=5000%2C9000")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test2_val_3" not in data
        assert "test2_val_4" not in data
        # Test boolean filter
        assert view7._filter_groups
        assert [
            (f["index"], f["operation"]) for f in view7._filter_groups["Bool Field"]
        ] == [
            (0, "equals"),
            (1, "not equal"),
        ]

        # boolean - equals - Yes
        rv = client.get("/admin/_bools/?flt0_0=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" not in data
        assert "test2_val_3" not in data

        # boolean - equals - No
        rv = client.get("/admin/_bools/?flt0_0=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" in data
        assert "test2_val_3" in data

        # boolean - not equals - Yes
        rv = client.get("/admin/_bools/?flt0_1=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" in data
        assert "test2_val_3" in data

        # boolean - not equals - No
        rv = client.get("/admin/_bools/?flt0_1=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" not in data
        assert "test2_val_3" not in data
        # Test float filter
        assert view8._filter_groups
        assert [
            (f["index"], f["operation"]) for f in view8._filter_groups["Float Field"]
        ] == [
            (0, "equals"),
            (1, "not equal"),
            (2, "greater than"),
            (3, "smaller than"),
            (4, "empty"),
            (5, "in list"),
            (6, "not in list"),
        ]

        # float - equals
        rv = client.get("/admin/_float/?flt0_0=25.9")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" in data
        assert "test2_val_4" not in data

        # float - equals - test validation
        rv = client.get("/admin/_float/?flt0_0=badval")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "Invalid Filter Value" in data

        # float - not equal
        rv = client.get("/admin/_float/?flt0_1=25.9")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" not in data
        assert "test2_val_4" in data

        # float - greater
        rv = client.get("/admin/_float/?flt0_2=60.5")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" not in data
        assert "test2_val_4" in data

        # float - smaller
        rv = client.get("/admin/_float/?flt0_3=60.5")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_3" in data
        assert "test2_val_4" not in data

        # float - empty
        rv = client.get("/admin/_float/?flt0_4=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test2_val_3" not in data
        assert "test2_val_4" not in data

        # float - not empty
        rv = client.get("/admin/_float/?flt0_4=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test2_val_3" in data
        assert "test2_val_4" in data

        # float - in list
        rv = client.get("/admin/_float/?flt0_5=25.9%2C75.5")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" not in data
        assert "test2_val_2" not in data
        assert "test2_val_3" in data
        assert "test2_val_4" in data

        # float - in list - test validation
        rv = client.get("/admin/_float/?flt0_5=25.9%2Cbadval")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "Invalid Filter Value" in data

        # float - not in list
        rv = client.get("/admin/_float/?flt0_6=25.9%2C75.5")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" in data
        assert "test2_val_3" not in data
        assert "test2_val_4" not in data

        # Test filters to joined table field
        rv = client.get("/admin/_model2/?flt1_0=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2_val_1" in data
        assert "test2_val_2" not in data
        assert "test2_val_3" not in data
        assert "test2_val_4" not in data

        # Test human readable URLs
        rv = client.get("/admin/_model3/?flt1_test1_equals=test1_val_1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "test1_val_2" not in data
        # Test date, time, and datetime filters
        assert view11._filter_groups
        assert [
            (f["index"], f["operation"]) for f in view11._filter_groups["Date Field"]
        ] == [
            (0, "equals"),
            (1, "not equal"),
            (2, "greater than"),
            (3, "smaller than"),
            (4, "between"),
            (5, "not between"),
            (6, "empty"),
        ]

        assert [
            (f["index"], f["operation"])
            for f in view11._filter_groups["Datetime Field"]
        ] == [
            (7, "equals"),
            (8, "not equal"),
            (9, "greater than"),
            (10, "smaller than"),
            (11, "between"),
            (12, "not between"),
            (13, "empty"),
        ]

        assert [
            (f["index"], f["operation"]) for f in view11._filter_groups["Time Field"]
        ] == [
            (14, "equals"),
            (15, "not equal"),
            (16, "greater than"),
            (17, "smaller than"),
            (18, "between"),
            (19, "not between"),
            (20, "empty"),
        ]

        # date - equals
        rv = client.get("/admin/_datetime/?flt0_0=2014-11-17")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "date_obj1" in data
        assert "date_obj2" not in data

        # date - not equal
        rv = client.get("/admin/_datetime/?flt0_1=2014-11-17")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "date_obj1" not in data
        assert "date_obj2" in data

        # date - greater
        rv = client.get("/admin/_datetime/?flt0_2=2014-11-16")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "date_obj1" in data
        assert "date_obj2" not in data

        # date - smaller
        rv = client.get("/admin/_datetime/?flt0_3=2014-11-16")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "date_obj1" not in data
        assert "date_obj2" in data

        # date - between
        rv = client.get("/admin/_datetime/?flt0_4=2014-11-13+to+2014-11-20")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "date_obj1" in data
        assert "date_obj2" not in data

        # date - not between
        rv = client.get("/admin/_datetime/?flt0_5=2014-11-13+to+2014-11-20")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "date_obj1" not in data
        assert "date_obj2" in data

        # date - empty
        rv = client.get("/admin/_datetime/?flt0_6=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "date_obj1" not in data
        assert "date_obj2" not in data

        # date - empty
        rv = client.get("/admin/_datetime/?flt0_6=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "date_obj1" in data
        assert "date_obj2" in data

        # datetime - equals
        rv = client.get("/admin/_datetime/?flt0_7=2014-04-03+01%3A09%3A00")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "datetime_obj1" in data
        assert "datetime_obj2" not in data

        # datetime - not equal
        rv = client.get("/admin/_datetime/?flt0_8=2014-04-03+01%3A09%3A00")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "datetime_obj1" not in data
        assert "datetime_obj2" in data

        # datetime - greater
        rv = client.get("/admin/_datetime/?flt0_9=2014-04-03+01%3A08%3A00")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "datetime_obj1" in data
        assert "datetime_obj2" not in data

        # datetime - smaller
        rv = client.get("/admin/_datetime/?flt0_10=2014-04-03+01%3A08%3A00")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "datetime_obj1" not in data
        assert "datetime_obj2" in data

        # datetime - between
        rv = client.get(
            "/admin/_datetime"
            "/?flt0_11=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59"
        )
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "datetime_obj1" in data
        assert "datetime_obj2" not in data

        # datetime - not between
        rv = client.get(
            "/admin/_datetime"
            "/?flt0_12=2014-04-02+00%3A00%3A00+to+2014-11-20+23%3A59%3A59"
        )
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "datetime_obj1" not in data
        assert "datetime_obj2" in data

        # datetime - empty
        rv = client.get("/admin/_datetime/?flt0_13=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "datetime_obj1" not in data
        assert "datetime_obj2" not in data

        # datetime - not empty
        rv = client.get("/admin/_datetime/?flt0_13=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "datetime_obj1" in data
        assert "datetime_obj2" in data

        # time - equals
        rv = client.get("/admin/_datetime/?flt0_14=11%3A10%3A09")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "timeonly_obj1" in data
        assert "timeonly_obj2" not in data

        # time - not equal
        rv = client.get("/admin/_datetime/?flt0_15=11%3A10%3A09")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "timeonly_obj1" not in data
        assert "timeonly_obj2" in data

        # time - greater
        rv = client.get("/admin/_datetime/?flt0_16=11%3A09%3A09")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "timeonly_obj1" in data
        assert "timeonly_obj2" not in data

        # time - smaller
        rv = client.get("/admin/_datetime/?flt0_17=11%3A09%3A09")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "timeonly_obj1" not in data
        assert "timeonly_obj2" in data

        # time - between
        rv = client.get("/admin/_datetime/?flt0_18=10%3A40%3A00+to+11%3A50%3A59")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "timeonly_obj1" in data
        assert "timeonly_obj2" not in data

        # time - not between
        rv = client.get("/admin/_datetime/?flt0_19=10%3A40%3A00+to+11%3A50%3A59")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "timeonly_obj1" not in data
        assert "timeonly_obj2" in data

        # time - empty
        rv = client.get("/admin/_datetime/?flt0_20=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "timeonly_obj1" not in data
        assert "timeonly_obj2" not in data

        # time - not empty
        rv = client.get("/admin/_datetime/?flt0_20=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "timeonly_obj1" in data
        assert "timeonly_obj2" in data

        # Test enum filter
        # enum - equals
        rv = client.get("/admin/_enumfield/?flt0_0=model1_v1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "enum_obj1" in data
        assert "enum_obj2" not in data

        # enum - not equal
        rv = client.get("/admin/_enumfield/?flt0_1=model1_v1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "enum_obj1" not in data
        assert "enum_obj2" in data

        # enum - empty
        rv = client.get("/admin/_enumfield/?flt0_2=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "enum_obj1" not in data
        assert "enum_obj2" not in data

        # enum - not empty
        rv = client.get("/admin/_enumfield/?flt0_2=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "enum_obj1" in data
        assert "enum_obj2" in data

        # enum - in list
        rv = client.get("/admin/_enumfield/?flt0_3=model1_v1%2Cmodel1_v2")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "enum_obj1" in data
        assert "enum_obj2" in data

        # enum - not in list
        rv = client.get("/admin/_enumfield/?flt0_4=model1_v1%2Cmodel1_v2")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "enum_obj1" not in data
        assert "enum_obj2" not in data

        # Test enum type filter
        # enum type - equals
        rv = client.get("/admin/_enumtypefield/?flt0_0=first")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "enum_type_obj1" in data
        assert "enum_type_obj2" not in data

        # enum - not equal
        rv = client.get("/admin/_enumtypefield/?flt0_1=first")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "enum_type_obj1" not in data
        assert "enum_type_obj2" in data

        # enum - empty
        rv = client.get("/admin/_enumtypefield/?flt0_2=1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "enum_type_obj1" not in data
        assert "enum_type_obj2" not in data

        # enum - not empty
        rv = client.get("/admin/_enumtypefield/?flt0_2=0")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "enum_type_obj1" in data
        assert "enum_type_obj2" in data

        # enum - in list
        rv = client.get("/admin/_enumtypefield/?flt0_3=first%2Csecond")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" not in data
        assert "enum_type_obj1" in data
        assert "enum_type_obj2" in data

        # enum - not in list
        rv = client.get("/admin/_enumtypefield/?flt0_4=first%2Csecond")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1_val_1" in data
        assert "enum_type_obj1" not in data
        assert "enum_type_obj2" not in data

        # Test single custom filter on relation
        rv = client.get("/admin/_relation_test/?flt1_0=test1_val_1")
        data = rv.data.decode("utf-8")

        assert "test1_val_1" in data
        assert "test1_val_2" not in data


def test_url_for_simple(app, sqla_db_ext, admin, session_or_db):
    # with app.app_context():
    Model1, Model2 = create_models(sqla_db_ext)

    param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
    view = CustomModelView(
        Model1,
        param,
        endpoint="user",
        column_filters=["test1", "id", "test5", "bool_field"],
    )
    admin.add_view(view)

    with app.test_request_context("http://localhost/admin/user/"):
        filtered_url = view.url_for()
        assert filtered_url == "/admin/user/"

        filtered_url = view.url_for(search="exam", filters=[])
        assert filtered_url == "/admin/user/?search=exam"

        filtered_url = view.url_for(
            search="exam",
            filters=[
                filters.FilterLike(Model1.test1, "Email", url_value="test1"),
                filters.FilterLike(Model1.test1, "Email222", url_value="test1"),
                filters.BooleanEqualFilter(
                    Model1.bool_field, "active", url_value=False
                ),
                filters.IntInListFilter(Model1.id, "ID", url_value=[33, 30, 35]),
                filters.FloatGreaterFilter(Model1.test5, "Salary", url_value=50000.0),
                filters.FloatSmallerFilter(Model1.test5, "Salary", url_value=150000.0),
            ],
        )
        assert (
            filtered_url == "/admin/user/?search=exam&flt0_0=test1&flt1_0=test1&"
            "flt2_21=0&flt3_12=33,30,35&flt4_16=50000.0&flt5_17=150000.0"
        )

        view.named_filter_urls = True

        filtered_url = view.url_for(
            search="exam",
            filters=[
                filters.FilterLike(Model1.test1, "Email", url_value="test1"),
                filters.FilterLike(Model1.test1, "Email222", url_value="test1"),
                filters.BooleanEqualFilter(
                    Model1.bool_field, "active", url_value=False
                ),
                filters.IntInListFilter(Model1.id, "ID", url_value=[33, 30, 35]),
                filters.FloatGreaterFilter(Model1.test5, "Salary", url_value=50000.0),
            ],
        )
        assert (
            filtered_url == "/admin/user/?search=exam&"
            "flt0_test1_contains=test1&"
            "flt1_test1_contains=test1&"
            "flt2_bool_field_equals=0&"
            "flt3_id_in_list=33,30,35&"
            "flt4_test5_greater_than=50000.0"
        )


def create_filter_params():
    uuid1 = "a81bc81b-dead-4e5d-abff-90865d1e13b1"
    uuid2 = "344a5ad9-6b2a-410c-aa06-401d1ae8ea39"

    params = [
        (filters.FilterLike, "test1", "x", "flt0_0", "flt0_test1_contains", "x"),
        (filters.FilterNotLike, "test1", "x", "flt0_1", "flt0_test1_not_contains", "x"),
        (filters.FilterEqual, "test1", "x", "flt0_2", "flt0_test1_equals", "x"),
        (filters.FilterNotEqual, "test1", "x", "flt0_3", "flt0_test1_not_equal", "x"),
        (filters.FilterEmpty, "test1", "1", "flt0_4", "flt0_test1_empty", "1"),
        (
            filters.FilterInList,
            "test1",
            ["x", "y"],
            "flt0_5",
            "flt0_test1_in_list",
            "x,y",
        ),
        (
            filters.FilterNotInList,
            "test1",
            ["x", "y"],
            "flt0_6",
            "flt0_test1_not_in_list",
            "x,y",
        ),
        (filters.IntEqualFilter, "id", 30, "flt0_0", "flt0_id_equals", "30"),  # equals
        (
            filters.IntNotEqualFilter,
            "id",
            30,
            "flt0_1",
            "flt0_id_not_equal",
            "30",
        ),  # not equal
        (
            filters.IntGreaterFilter,
            "id",
            30,
            "flt0_2",
            "flt0_id_greater_than",
            "30",
        ),  # greater
        (
            filters.IntSmallerFilter,
            "id",
            30,
            "flt0_3",
            "flt0_id_smaller_than",
            "30",
        ),  # smaller
        (filters.FilterEmpty, "id", 1, "flt0_4", "flt0_id_empty", "1"),  # empty
        (
            filters.IntInListFilter,
            "id",
            [30, 35],
            "flt0_5",
            "flt0_id_in_list",
            "30,35",
        ),  # in list
        (
            filters.IntNotInListFilter,
            "id",
            [30, 35],
            "flt0_6",
            "flt0_id_not_in_list",
            "30,35",
        ),  # not in list
        (
            filters.FloatEqualFilter,
            "test5",
            1.5,
            "flt0_0",
            "flt0_test5_equals",
            "1.5",
        ),  # equals
        (
            filters.FloatNotEqualFilter,
            "test5",
            1.5,
            "flt0_1",
            "flt0_test5_not_equal",
            "1.5",
        ),  # not equal
        (
            filters.FloatGreaterFilter,
            "test5",
            1.5,
            "flt0_2",
            "flt0_test5_greater_than",
            "1.5",
        ),  # greater
        (
            filters.FloatSmallerFilter,
            "test5",
            1.5,
            "flt0_3",
            "flt0_test5_smaller_than",
            "1.5",
        ),  # smaller
        (filters.FilterEmpty, "test5", 1, "flt0_4", "flt0_test5_empty", "1"),  # empty
        (
            filters.FloatInListFilter,
            "test5",
            [1.5, 2.5],
            "flt0_5",
            "flt0_test5_in_list",
            "1.5,2.5",
        ),  # in list
        (
            filters.FloatNotInListFilter,
            "test5",
            [1.5, 2.5],
            "flt0_6",
            "flt0_test5_not_in_list",
            "1.5,2.5",
        ),  # not in list
        (
            filters.BooleanEqualFilter,
            "bool_field",
            True,
            "flt0_0",
            "flt0_bool_field_equals",
            "1",
        ),  # equals
        (
            filters.BooleanEqualFilter,
            "bool_field",
            False,
            "flt0_0",
            "flt0_bool_field_equals",
            "0",
        ),  # equals
        (
            filters.BooleanNotEqualFilter,
            "bool_field",
            True,
            "flt0_1",
            "flt0_bool_field_not_equal",
            "1",
        ),  # not equal
        (
            filters.BooleanNotEqualFilter,
            "bool_field",
            False,
            "flt0_1",
            "flt0_bool_field_not_equal",
            "0",
        ),  # not equal
        (
            filters.DateEqualFilter,
            "date_field",
            datetime(2025, 11, 1),
            "flt0_0",
            "flt0_date_field_equals",
            "2025-11-01",
        ),
        (
            filters.DateNotEqualFilter,
            "date_field",
            datetime(2025, 11, 1),
            "flt0_1",
            "flt0_date_field_not_equal",
            "2025-11-01",
        ),
        (
            filters.DateGreaterFilter,
            "date_field",
            datetime(2025, 11, 1),
            "flt0_2",
            "flt0_date_field_greater_than",
            "2025-11-01",
        ),
        (
            filters.DateSmallerFilter,
            "date_field",
            datetime(2025, 11, 1),
            "flt0_3",
            "flt0_date_field_smaller_than",
            "2025-11-01",
        ),
        (
            filters.DateBetweenFilter,
            "date_field",
            (datetime(2025, 11, 1), datetime(2025, 11, 15)),
            "flt0_4",
            "flt0_date_field_between",
            "2025-11-01+to+2025-11-15",
        ),
        (
            filters.DateNotBetweenFilter,
            "date_field",
            (datetime(2025, 11, 1), datetime(2025, 11, 15)),
            "flt0_5",
            "flt0_date_field_not_between",
            "2025-11-01+to+2025-11-15",
        ),
        (
            filters.FilterEmpty,
            "date_field",
            "1",
            "flt0_6",
            "flt0_date_field_empty",
            "1",
        ),
        (
            filters.DateTimeEqualFilter,
            "datetime_field",
            datetime(2025, 11, 1),
            "flt0_0",
            "flt0_datetime_field_equals",
            "2025-11-01+00:00:00",
        ),
        (
            filters.DateTimeNotEqualFilter,
            "datetime_field",
            datetime(2025, 11, 1),
            "flt0_1",
            "flt0_datetime_field_not_equal",
            "2025-11-01+00:00:00",
        ),
        (
            filters.DateTimeGreaterFilter,
            "datetime_field",
            datetime(2025, 11, 1),
            "flt0_2",
            "flt0_datetime_field_greater_than",
            "2025-11-01+00:00:00",
        ),
        (
            filters.DateTimeSmallerFilter,
            "datetime_field",
            datetime(2025, 11, 1),
            "flt0_3",
            "flt0_datetime_field_smaller_than",
            "2025-11-01+00:00:00",
        ),
        (
            filters.DateTimeBetweenFilter,
            "datetime_field",
            (datetime(2025, 11, 1), datetime(2025, 11, 15)),
            "flt0_4",
            "flt0_datetime_field_between",
            "2025-11-01+00:00:00+to+2025-11-15+00:00:00",
        ),
        (
            filters.DateTimeNotBetweenFilter,
            "datetime_field",
            (datetime(2025, 11, 1), datetime(2025, 11, 15)),
            "flt0_5",
            "flt0_datetime_field_not_between",
            "2025-11-01+00:00:00+to+2025-11-15+00:00:00",
        ),
        (
            filters.FilterEmpty,
            "datetime_field",
            "1",
            "flt0_6",
            "flt0_datetime_field_empty",
            "1",
        ),
        (
            filters.TimeEqualFilter,
            "time_field",
            time(6, 30, 0),
            "flt0_0",
            "flt0_time_field_equals",
            "06:30:00",
        ),
        (
            filters.UuidFilterEqual,
            "sqla_utils_uuid",
            uuid1,
            "flt0_0",
            "flt0_sqla_utils_uuid_equals",
            uuid1,
        ),
        (
            filters.UuidFilterNotEqual,
            "sqla_utils_uuid",
            uuid1,
            "flt0_1",
            "flt0_sqla_utils_uuid_not_equal",
            uuid1,
        ),
        (
            filters.FilterEmpty,
            "sqla_utils_uuid",
            "1",
            "flt0_2",
            "flt0_sqla_utils_uuid_empty",
            "1",
        ),
        (
            filters.UuidFilterInList,
            "sqla_utils_uuid",
            [uuid1, uuid2],
            "flt0_3",
            "flt0_sqla_utils_uuid_in_list",
            f"{uuid1},{uuid2}",
        ),
        (
            filters.UuidFilterNotInList,
            "sqla_utils_uuid",
            [uuid1, uuid2],
            "flt0_4",
            "flt0_sqla_utils_uuid_not_in_list",
            f"{uuid1},{uuid2}",
        ),
        (
            filters.DateTimeGreaterFilter,
            "sqla_utils_arrow",
            datetime(2025, 11, 1),
            "flt0_0",
            "flt0_sqla_utils_arrow_greater_than",
            "2025-11-01+00:00:00",
        ),
        (
            filters.DateTimeSmallerFilter,
            "sqla_utils_arrow",
            datetime(2025, 11, 1),
            "flt0_1",
            "flt0_sqla_utils_arrow_smaller_than",
            "2025-11-01+00:00:00",
        ),
        (
            filters.FilterEmpty,
            "sqla_utils_arrow",
            "1",
            "flt0_2",
            "flt0_sqla_utils_arrow_empty",
            "1",
        ),
    ]
    return params


@pytest.mark.parametrize(
    "FilterClass, col, filter_value, arg_key, arg_named_key, expected_value",
    create_filter_params(),
)
def test_url_for(
    app,
    sqla_db_ext,
    admin,
    session_or_db,
    FilterClass,
    col,
    filter_value,
    arg_key,
    arg_named_key,
    expected_value,
):
    # with app.app_context():
    Model1, Model2 = create_models(sqla_db_ext)

    col = getattr(Model1, col)

    param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
    view = CustomModelView(Model1, param, endpoint="user", column_filters=[col])
    admin.add_view(view)

    with app.test_request_context("http://localhost/admin/user/"):
        d1 = filter_value
        filtered_url = view.url_for(filters=[FilterClass(col, "f1", url_value=d1)])
        assert filtered_url == f"/admin/user/?{arg_key}={expected_value}"

        view.named_filter_urls = True

        d1 = filter_value
        filtered_url = view.url_for(filters=[FilterClass(col, "f1", url_value=d1)])
        assert filtered_url == f"/admin/user/?{arg_named_key}={expected_value}"


def create_filter_params_enums_and_choices():
    params = [
        (
            filters.EnumEqualFilter,
            "enum_field",
            "model1_v1",
            "flt0_0",
            "flt0_enum_field_equals",
            "model1_v1",
        ),
        (
            filters.EnumFilterNotEqual,
            "enum_field",
            "model1_v1",
            "flt0_1",
            "flt0_enum_field_not_equal",
            "model1_v1",
        ),
        (
            filters.EnumFilterEmpty,
            "enum_field",
            "1",
            "flt0_2",
            "flt0_enum_field_empty",
            "1",
        ),
        (
            filters.EnumFilterInList,
            "enum_field",
            ["model1_v1"],
            "flt0_3",
            "flt0_enum_field_in_list",
            "model1_v1",
        ),
        (
            filters.EnumFilterNotInList,
            "enum_field",
            ["model1_v1"],
            "flt0_4",
            "flt0_enum_field_not_in_list",
            "model1_v1",
        ),
        (
            filters.ChoiceTypeEqualFilter,
            "sqla_utils_choice",
            "choice-1",
            "flt0_0",
            "flt0_sqla_utils_choice_equals",
            "choice-1",
        ),
        (
            filters.ChoiceTypeNotEqualFilter,
            "sqla_utils_choice",
            "choice-1",
            "flt0_1",
            "flt0_sqla_utils_choice_not_equal",
            "choice-1",
        ),
        (
            filters.ChoiceTypeLikeFilter,
            "sqla_utils_choice",
            "choice-1",
            "flt0_2",
            "flt0_sqla_utils_choice_contains",
            "choice-1",
        ),
        (
            filters.ChoiceTypeNotLikeFilter,
            "sqla_utils_choice",
            "choice-1",
            "flt0_3",
            "flt0_sqla_utils_choice_not_contains",
            "choice-1",
        ),
        # (
        #     filters.FilterEmpty,
        #     "sqla_utils_choice",
        #     "1",
        #     "flt0_4",
        #     "flt0_sqla_utils_choice_empty",
        #     "1",
        # ),
    ]
    return params


@pytest.mark.parametrize(
    "FilterClass, col, filter_value, arg_key, arg_named_key, expected_value",
    create_filter_params_enums_and_choices(),
)
def test_url_for_enums_and_choices(
    app,
    sqla_db_ext,
    admin,
    session_or_db,
    FilterClass,
    col,
    filter_value,
    arg_key,
    arg_named_key,
    expected_value,
):
    Model1, Model2 = create_models(sqla_db_ext)

    col = getattr(Model1, col)

    param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
    view = CustomModelView(Model1, param, endpoint="user", column_filters=[col])
    admin.add_view(view)

    with app.test_request_context("http://localhost/admin/user/"):
        d1 = filter_value
        filtered_url = view.url_for(filters=[FilterClass(col, "f1", url_value=d1)])
        assert filtered_url == f"/admin/user/?{arg_key}={expected_value}"

        view.named_filter_urls = True
        d1 = filter_value
        filtered_url = view.url_for(filters=[FilterClass(col, "f1", url_value=d1)])
        assert filtered_url == f"/admin/user/?{arg_named_key}={expected_value}"


def test_column_filters_sqla_obj(app, sqla_db_ext, admin, session_or_db):
    with app.app_context():
        Model1, Model2 = create_models(sqla_db_ext)

        param = sqla_db_ext.db.session if session_or_db == "session" else sqla_db_ext.db
        view = CustomModelView(Model1, param, column_filters=[Model1.test1])
        admin.add_view(view)
        assert view._filters
        assert len(view._filters) == 7
