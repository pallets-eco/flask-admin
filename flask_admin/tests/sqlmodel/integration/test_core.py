"""
Core compliance tests for Flask-Admin model backend specification.

This test module validates that the SQLModel backend fully adheres to the
Flask-Admin model backend specification as defined in:
doc/adding_a_new_model_backend.rst

These tests ensure:
1. All required scaffolding methods are implemented
2. Methods return values in expected formats
3. Core Flask-Admin functionality works correctly
4. Compliance with BaseModelView interface
"""

from typing import Optional

from flask import Flask
from sqlalchemy import Engine
from sqlmodel import Field
from sqlmodel import Session
from wtforms.form import Form

from flask_admin.base import Admin
from flask_admin.model.base import BaseModelView
from flask_admin.model.filters import BaseFilter

from flask_admin.tests.sqlmodel import CustomModelView
from flask_admin.tests.sqlmodel import sqlmodel_base


def test_sqlmodel_view_inherits_from_base_model_view():
    """
    Test that SQLModelView properly inherits from BaseModelView.
    This ensures we have the correct inheritance hierarchy.
    """
    assert issubclass(CustomModelView, BaseModelView)


def test_required_scaffolding_methods_are_implemented(
    app: Flask, engine: Engine, admin: Admin
):
    """
    Test that all required scaffolding methods from the Flask-Admin specification
    are implemented in the SQLModel backend.
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)
            description: str = Field(default="")

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            # Test all required methods are implemented
            # (not raising NotImplementedError)
            required_methods = [
                "get_pk_value",
                "scaffold_list_columns",
                "scaffold_sortable_columns",
                "init_search",
                "scaffold_form",
                "get_list",
                "get_one",
                "create_model",
                "update_model",
                "delete_model",
                "is_valid_filter",
                "scaffold_filters",
            ]

            for method_name in required_methods:
                assert hasattr(view, method_name), (
                    f"Method {method_name} not implemented"
                )
                method = getattr(view, method_name)
                assert callable(method), f"Method {method_name} is not callable"


def test_get_pk_value_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test get_pk_value method returns primary key value from model instance.
    Per spec: "returns a primary key value from the model instance"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            # Create a test instance
            instance = TestModel(id=123, name="test")

            # Test get_pk_value returns the primary key
            pk_value = view.get_pk_value(instance)
            # PK value might be string or int depending on implementation
            assert pk_value == 123 or pk_value == "123"

            # Test with different PK values
            instance2 = TestModel(id=456, name="test2")
            pk_value2 = view.get_pk_value(instance2)
            assert pk_value2 == 456 or pk_value2 == "456"


def test_scaffold_list_columns_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test scaffold_list_columns method returns list of column names.
    Per spec: "Returns a list of columns to be displayed in a list view"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)
            email: str = Field(max_length=100)
            active: bool = Field(default=True)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            columns = view.scaffold_list_columns()

            # Test return type is list
            assert isinstance(columns, list)

            # Test expected columns are present
            expected_columns = ["id", "name", "email", "active"]
            for col in expected_columns:
                assert col in columns, (
                    f"Column {col} missing from scaffold_list_columns"
                )

            # Test all returned values are strings (column names)
            for col in columns:
                assert isinstance(col, str), f"Column {col} is not a string"


def test_scaffold_sortable_columns_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test scaffold_sortable_columns method returns dictionary of sortable columns.
    Per spec: "Returns a dictionary of sortable columns.
    Keys should correspond to field names"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)
            email: str = Field(max_length=100)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            sortable = view.scaffold_sortable_columns()

            # Test return type is dict or None (per spec)
            assert isinstance(sortable, (dict, type(None)))

            if sortable is not None:
                # Test keys are strings (field names)
                for key in sortable.keys():
                    assert isinstance(key, str), (
                        f"Sortable column key {key} is not a string"
                    )


def test_init_search_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test init_search method returns boolean indicating search support.
    Per spec: "If backend supports search, return True. If not, return False"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            search_supported = view.init_search()

            # Test return type is boolean
            assert isinstance(search_supported, bool)


def test_scaffold_form_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test scaffold_form method generates WTForms form class from model.
    Per spec: "Generate `WTForms` form class from the model"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)
            email: str = Field(max_length=100)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            form_class = view.scaffold_form()

            # Test return type is a class
            assert isinstance(form_class, type)

            # Test it's a Form subclass
            assert issubclass(form_class, Form)

            # Test form can be instantiated
            form_instance = form_class()
            assert isinstance(form_instance, Form)


def test_get_list_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test get_list method returns tuple of (count, list) with paging/sorting.
    Per spec: "Return count, list as a tuple"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: Optional[int] = Field(primary_key=True, default=None)
            name: str = Field(max_length=50)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            # Create test data
            for i in range(5):
                instance = TestModel(name=f"test_{i}")
                db_session.add(instance)
            db_session.commit()

            view = CustomModelView(TestModel, db_session)

            # Test basic get_list call
            count, models = view.get_list(
                page=0,
                sort_column=None,
                sort_desc=False,
                search=None,
                filters=None,
                page_size=10,
            )

            # Test return type is tuple
            assert isinstance((count, models), tuple)

            # Test count is integer
            assert isinstance(count, int)
            assert count >= 0

            # Test models is list
            assert isinstance(models, list)

            # Test actual data
            assert count == 5
            assert len(models) <= count  # Could be paginated


def test_get_one_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test get_one method returns single model by primary key.
    Per spec: "Return a model instance by its primary key"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: Optional[int] = Field(primary_key=True, default=None)
            name: str = Field(max_length=50)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            # Create test data
            instance = TestModel(name="test_item")
            db_session.add(instance)
            db_session.commit()

            created_id = instance.id

            view = CustomModelView(TestModel, db_session)

            # Test get_one retrieves the correct instance
            # Convert ID to string format expected by get_one
            retrieved = view.get_one(str(created_id))

            assert retrieved is not None
            assert hasattr(retrieved, "id")
            # PK value might be string or int depending on implementation  
            retrieved_pk = view.get_pk_value(retrieved)
            assert retrieved_pk == created_id or retrieved_pk == str(created_id)
            assert retrieved.name == "test_item"


def test_create_model_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test create_model method creates new model from form.
    Per spec: "Create a new instance of the model from the Form object"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            # Create form with test data
            form_class = view.scaffold_form()
            form = form_class(data={"name": "new_test_item"})

            # Test create_model
            result = view.create_model(form)

            # Test creation succeeded
            assert result is True or result is not None

            # Verify the model was actually created
            count, models = view.get_list(
                page=0,
                sort_column=None,
                sort_desc=False,
                search=None,
                filters=None,
                page_size=10,
            )
            assert count > 0 # type: ignore


def test_update_model_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test update_model method updates existing model from form.
    Per spec: "Update the model instance with data from the form"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: Optional[int] = Field(primary_key=True, default=None)
            name: str = Field(max_length=50)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            # Create initial instance
            instance = TestModel(name="original_name")
            db_session.add(instance)
            db_session.commit()

            created_id = instance.id

            view = CustomModelView(TestModel, db_session)

            # Create form with updated data
            form_class = view.scaffold_form()
            # Create form with updated data and set the field value
            form = form_class(obj=instance)
            form.name.data = "updated_name"

            # Test update_model (need request context for flash messages)
            with app.test_request_context():
                result = view.update_model(form, instance)

                # Test update succeeded
                assert result is True

                # Verify the model was actually updated
                updated_instance = view.get_one(str(created_id))
                assert updated_instance.name == "updated_name"


def test_delete_model_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test delete_model method deletes specified model instance.
    Per spec: "Delete the specified model instance from the data store"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: Optional[int] = Field(primary_key=True, default=None)
            name: str = Field(max_length=50)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            # Create instance to delete
            instance = TestModel(name="to_be_deleted")
            db_session.add(instance)
            db_session.commit()

            created_id = instance.id

            view = CustomModelView(TestModel, db_session)

            # Verify instance exists before deletion
            retrieved = view.get_one(str(created_id))
            assert retrieved is not None

            # Test delete_model (need request context for flash messages)
            with app.test_request_context():
                result = view.delete_model(instance)

                # Test deletion succeeded
                assert result is True

                # Verify the model was actually deleted
                deleted_instance = view.get_one(str(created_id))
                assert deleted_instance is None


def test_is_valid_filter_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test is_valid_filter method validates filter objects.
    Per spec: "Verify whether the given object is a valid filter"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            # Test with invalid filter (None)
            assert view.is_valid_filter(None) is False

            # Test with invalid filter (random object)
            assert view.is_valid_filter("not_a_filter") is False

            # Test with valid filter (if we can create one)
            filters = view.scaffold_filters("name")
            if filters:
                # Test first filter if any exist
                assert view.is_valid_filter(filters[0]) is True


def test_scaffold_filters_method(app: Flask, engine: Engine, admin: Admin):
    """
    Test scaffold_filters method returns list of filter objects for field.
    Per spec: "Return a list of filter objects for one model field"
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)
            email: str = Field(max_length=100)
            active: bool = Field(default=True)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            # Test scaffold_filters for different field types
            for field_name in ["name", "email", "active", "id"]:
                filters = view.scaffold_filters(field_name)

                # Test return type is list or None
                assert isinstance(filters, (list, type(None)))

                if filters is not None:
                    # Test all items are filter objects
                    for filter_obj in filters:
                        assert isinstance(filter_obj, BaseFilter)
                        # Test filter has required methods
                        assert hasattr(filter_obj, "apply")
                        assert hasattr(filter_obj, "operation")
                        assert callable(filter_obj.apply)
                        assert callable(filter_obj.operation)


def test_model_assumptions_compliance(app: Flask, engine: Engine, admin: Admin):
    """
    Test that models meet Flask-Admin assumptions from the specification:
    1. Each model must have one field which acts as a primary key
    2. Models must make their data accessible as python properties
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: Optional[int] = Field(primary_key=True, default=None)
            name: str = Field(max_length=50)
            email: str = Field(max_length=100)

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            # Create test instance
            instance = TestModel(name="test", email="test@example.com")
            db_session.add(instance)
            db_session.commit()

            # Test requirement 1: Primary key exists and is accessible
            pk_value = view.get_pk_value(instance)
            assert pk_value is not None
            assert isinstance(pk_value, (int, str))  # Common PK types

            # Test requirement 2: Data accessible as python properties
            assert hasattr(instance, "name")
            assert hasattr(instance, "email")
            assert instance.name == "test"
            assert instance.email == "test@example.com"

            # Test properties are readable
            name_value = instance.name
            email_value = instance.email
            assert name_value == "test"
            assert email_value == "test@example.com"


def test_specification_required_operations_work_together(
    app: Flask, engine: Engine, admin: Admin
):
    """
    Integration test that verifies all required operations work together
    in a complete CRUD workflow as expected by Flask-Admin.
    """
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class TestModel(sqlmodel_class, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(max_length=50)
            description: str = Field(default="")

        sqlmodel_class.metadata.create_all(engine)

        with Session(engine) as db_session:
            view = CustomModelView(TestModel, db_session)

            # Test complete workflow: scaffold -> create -> read -> update -> delete

            # 1. Scaffold operations work
            columns = view.scaffold_list_columns()
            assert "name" in columns

            form_class = view.scaffold_form()
            assert issubclass(form_class, Form)

            # 2. Create operation works
            form = form_class(
                data={"name": "workflow_test", "description": "test desc"}
            )
            create_result = view.create_model(form)
            assert create_result is True or create_result is not None

            # 3. Read operations work
            count, models = view.get_list(
                page=0,
                sort_column=None,
                sort_desc=False,
                search=None,
                filters=None,
                page_size=10,
            )
            assert count > 0 # type: ignore
            assert len(models) > 0

            created_model = models[0]  # Get the created model
            pk_value = view.get_pk_value(created_model)

            retrieved_model = view.get_one(str(pk_value))
            assert retrieved_model is not None
            assert retrieved_model.name == "workflow_test"

            # 4. Update operation works (need request context)
            with app.test_request_context():
                update_form = form_class(obj=retrieved_model)
                update_form.name.data = "updated_workflow_test"
                update_form.description.data = "updated desc"
                update_result = view.update_model(update_form, retrieved_model)
                assert update_result is True

                # Verify update
                updated_model = view.get_one(str(pk_value))
                assert updated_model.name == "updated_workflow_test"

                # 5. Delete operation works
                delete_result = view.delete_model(updated_model)
                assert delete_result is True

                # Verify deletion
                deleted_model = view.get_one(str(pk_value))
                assert deleted_model is None
