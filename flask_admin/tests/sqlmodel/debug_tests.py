#!/usr/bin/env python3
"""
Debug tests for SQLModel Flask-Admin development.

This file contains debugging utilities and tests to help understand the behavior
of various Flask-Admin SQLModel components during development. Unlike regular unit
tests, these tests are designed to print detailed output and investigate how
different parts of the SQLModel integration work.

Purpose:
--------
This file was created to help debug complex issues encountered during the
SQLModel Flask-Admin integration development, particularly around:

1. Filter group naming and display issues
2. Relationship handling and dot notation filters
3. Primary key detection in complex inheritance scenarios
4. Form scaffolding with concrete inheritance
5. SQL query generation and cartesian product warnings
6. Field discovery and column list generation

Usage Examples:
---------------
Run all debug tests:
    $ python -m flask_admin.tests.sqlmodel.debug_tests

Run individual debug functions:
    >>> from flask_admin.tests.sqlmodel.debug_tests import test_filter_group_naming
    >>> test_filter_group_naming()

Run specific test categories:
    >>> # Debug filter naming issues
    >>> test_filter_group_naming()
    >>> test_dot_notation_filter_naming()

    >>> # Debug inheritance problems
    >>> test_concrete_inheritance_field_discovery()
    >>> test_inheritance_variants()

    >>> # Debug relationship and join issues
    >>> test_relationship_filter_joins()
    >>> test_filter_joins_setup()

Key Features:
-------------
- Detailed console output with 🔍 markers for easy scanning
- Reproduction of exact failing test scenarios
- Comparison of different inheritance patterns
- Manual query testing to isolate SQL issues
- Warning capture to identify potential problems
- Form scaffolding debugging with step-by-step output

When to Use:
------------
- When tests are failing with mysterious SQLAlchemy errors
- When filter display names are not appearing correctly
- When investigating form field discovery issues
- When debugging relationship filter joins
- When reproducing user-reported bugs in a controlled environment
- During development of new SQLModel features

Note: These tests are meant for development/debugging purposes and may
produce verbose output. They are not part of the regular test suite.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flask import Flask
from sqlmodel import create_engine
from sqlmodel import Session

from flask_admin import Admin
from flask_admin.tests.sqlmodel import create_models
from flask_admin.tests.sqlmodel import CustomModelView


def test_filter_group_naming():
    """Debug test to check filter group naming conventions"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite://")
    Model1, Model2 = create_models(engine)

    with app.app_context():
        admin = Admin(app)

        with Session(engine) as db_session:
            print("=== Testing Filter Group Naming ===")

            # Test direct field filters
            view1 = CustomModelView(Model1, db_session, column_filters=["test1"])
            admin.add_view(view1)

            print("view1 (direct field 'test1'):")
            print(f"  Filter groups: {list(view1._filter_groups.keys())}")
            print(f"  Total filters: {len(view1._filters)}")

            # Test relationship filters
            view2 = CustomModelView(Model2, db_session, column_filters=["model1"])

            print("\nview2 (relationship field 'model1'):")
            print(f"  Filter groups (first 5): {list(view2._filter_groups.keys())[:5]}")
            print(f"  Total filter groups: {len(view2._filter_groups)}")
            print(f"  Total filters: {len(view2._filters)}")

            # Test dot notation filters
            view3 = CustomModelView(
                Model2, db_session, column_filters=["model1.bool_field"]
            )

            print("\nview3 (dot notation 'model1.bool_field'):")
            print(f"  Filter groups: {list(view3._filter_groups.keys())}")
            print(f"  Total filters: {len(view3._filters)}")


def test_column_list_with_relationships():
    """Debug test to check column list behavior with relationships"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite://")
    Model1, Model2 = create_models(engine)

    with app.app_context():
        admin = Admin(app)

        with Session(engine) as db_session:
            print("\n=== Testing Column List with Relationships ===")

            # Test Model1 columns
            view1 = CustomModelView(Model1, db_session)
            admin.add_view(view1)

            columns1 = view1.get_list_columns()
            print("Model1 columns:")
            for col in columns1:
                print(f"  {col[0]}: {col[1]}")

            # Test Model2 columns
            view2 = CustomModelView(Model2, db_session)

            columns2 = view2.get_list_columns()
            print("\nModel2 columns:")
            for col in columns2:
                print(f"  {col[0]}: {col[1]}")


def test_relationship_field_handling():
    """Debug test to check how relationship fields are handled"""
    from flask_admin.contrib.sqlmodel import tools

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite://")
    Model1, Model2 = create_models(engine)

    with app.app_context():
        print("\n=== Testing Relationship Field Handling ===")

        # Test relationship detection
        model1_attr = getattr(Model1, "model2", None)
        model2_attr = getattr(Model2, "model1", None)

        print(f"Model1.model2 exists: {model1_attr is not None}")
        if model1_attr:
            print(f"  Is relationship: {tools.is_relationship(model1_attr)}")
            print(f"  Has property: {hasattr(model1_attr, 'property')}")
            tmp_output = (
                hasattr(model1_attr.property, "mapper")
                if hasattr(model1_attr, "property")
                else False
            )
            print(f"  Has mapper: {tmp_output}")

        print(f"\nModel2.model1 exists: {model2_attr is not None}")
        if model2_attr:
            print(f"  Is relationship: {tools.is_relationship(model2_attr)}")
            print(f"  Has property: {hasattr(model2_attr, 'property')}")
            tmp_output = (
                hasattr(model2_attr.property, "mapper")
                if hasattr(model2_attr, "property")
                else False
            )
            print(f"  Has mapper: {tmp_output}")


def test_primary_key_detection():
    """Debug test to check primary key detection"""
    from flask_admin.contrib.sqlmodel import tools

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite://")
    Model1, Model2 = create_models(engine)

    with app.app_context():
        print("\n=== Testing Primary Key Detection ===")

        # Test primary key detection
        pk1 = tools.get_primary_key(Model1)
        pk2 = tools.get_primary_key(Model2)

        print(f"Model1 primary key: {pk1}")
        print(f"Model2 primary key: {pk2}")

        # Test multiple primary keys detection
        multiple_pk1 = tools.has_multiple_pks(Model1)
        multiple_pk2 = tools.has_multiple_pks(Model2)

        print(f"Model1 has multiple PKs: {multiple_pk1}")
        print(f"Model2 has multiple PKs: {multiple_pk2}")


def test_field_type_detection():
    """Debug test to check field type detection for filters"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite://")
    Model1, Model2 = create_models(engine)

    with app.app_context():
        print("\n=== Testing Field Type Detection ===")

        # Test various field types
        test_fields = [
            "test1",
            "bool_field",
            "date_field",
            "datetime_field",
            "enum_field",
        ]

        for field_name in test_fields:
            attr = getattr(Model1, field_name, None)
            if attr:
                print(f"{field_name}:")
                print(f"  Has type: {hasattr(attr, 'type')}")
                if hasattr(attr, "type"):
                    print(f"  Type: {type(attr.type).__name__}")
                    print(f"  Type str: {attr.type}")


def test_dot_notation_filter_naming():
    """Debug test to check dot notation filter naming"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite://")
    Model1, Model2 = create_models(engine)

    with app.app_context():
        with Session(engine) as db_session:
            print("\n=== Testing Dot Notation Filter Naming ===")

            view3 = CustomModelView(
                Model2, db_session, column_filters=["model1.bool_field"]
            )

            print("Test case: column_filters=['model1.bool_field']")
            print("Expected: 'model1 / Model1 / Bool Field'")
            print(f"Actual  : {list(view3._filter_groups.keys())}")

            # Test multiple dot notation filters
            view4 = CustomModelView(
                Model2, db_session, column_filters=["model1.test1", "model1.bool_field"]
            )

            print("\nTest case: column_filters=['model1.test1', 'model1.bool_field']")
            print(
                "Expected: ['model1 / Model1 / Test1', 'model1 / Model1 / Bool Field']"
            )
            print(f"Actual  : {list(view4._filter_groups.keys())}")

            # Test with custom column labels
            view5 = CustomModelView(
                Model2,
                db_session,
                column_filters=["model1.bool_field", "string_field"],
                column_labels={
                    "model1.bool_field": "Test Filter #1",
                    "string_field": "Test Filter #2",
                },
            )

            print("\nTest case: column_filters with custom labels")
            print("Expected: ['Test Filter #1', 'Test Filter #2']")
            print(f"Actual  : {list(view5._filter_groups.keys())}")

            # Additional debug - check if column_labels are being processed
            print(f"Column labels: {view5.column_labels}")
            tmp_output = list(view5._filter_groups.keys()) == [
                "Test Filter #1",
                "Test Filter #2",
            ]
            print(f"Filter groups match expected: {tmp_output}")


def test_filter_joins_setup():
    """Debug test to check filter joins setup"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite://")
    Model1, Model2 = create_models(engine)

    with app.app_context():
        with Session(engine) as db_session:
            print("\n=== Testing Filter Joins Setup ===")

            # Test relationship filter joins
            view1 = CustomModelView(Model2, db_session, column_filters=["model1"])

            print("Relationship filter joins:")
            print(f"  _filter_joins keys: {list(view1._filter_joins.keys())}")

            # Test dot notation filter joins
            view2 = CustomModelView(
                Model2, db_session, column_filters=["model1.bool_field"]
            )

            print("\nDot notation filter joins:")
            print(f"  _filter_joins keys: {list(view2._filter_joins.keys())}")

            # Test direct field filter joins (should be empty)
            view3 = CustomModelView(Model1, db_session, column_filters=["test1"])

            print("\nDirect field filter joins:")
            print(f"  _filter_joins keys: {list(view3._filter_joins.keys())}")


def test_concrete_inheritance_field_discovery():
    """Debug test to check field discovery with concrete inheritance"""
    from sqlmodel import Field
    from sqlmodel import SQLModel

    from flask_admin.contrib.sqlmodel import SQLModelView

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite://")

    with app.app_context():
        # Create inheritance models
        class Parent(SQLModel):
            id: int = Field(primary_key=True)
            test: str

        class Child(Parent, table=True):
            id2: int = Field(primary_key=True)
            name: str
            __mapper_args__ = {"concrete": True}

        SQLModel.metadata.create_all(engine)

        print("\n=== Testing Concrete Inheritance Field Discovery ===")

        # Test mapper attributes
        print(f"Parent annotations: {Parent.__annotations__}")
        print(f"Child annotations: {Child.__annotations__}")

        print(f"Child mapper attrs: {[p.key for p in Child.__mapper__.attrs]}")
        print(f"Child table columns: {[col.name for col in Child.__table__.columns]}")
        print(
            "Child primary key columns: "
            + f"{[col.name for col in Child.__table__.primary_key.columns]}"
        )

        # Key finding: Child annotations don't include inherited fields!
        print("🔍 KEY ISSUE: Child annotations missing inherited 'id' field!")
        print(
            "   Child has 'id' in mapper: "
            + f"{'id' in [p.key for p in Child.__mapper__.attrs]}"
        )
        print(f"   Child has 'id' in annotations: {'id' in Child.__annotations__}")
        print(
            "   Child has 'id' in table: "
            + f"{'id' in [col.name for col in Child.__table__.columns]}"
        )

        # Test field discovery in form generation
        with Session(engine) as db_session:
            # Test SQLModelView field discovery
            view = SQLModelView(Child, db_session)
            list_columns = view.get_list_columns()

            print(f"SQLModelView list columns: {[col[0] for col in list_columns]}")

            # Test form scaffolding
            try:
                form = view.scaffold_form()
                scaffolded_fields = [
                    field_name for field_name in form._formfields.keys()
                ]
                print(f"Scaffolded form fields: {scaffolded_fields}")
                print(f"Form includes 'id': {'id' in scaffolded_fields}")
                print(f"Form includes 'id2': {'id2' in scaffolded_fields}")
            except Exception as e:
                print(f"Form scaffolding error: {e}")

            # Test manual field discovery using mapper vs annotations
            print("\n📊 Field Discovery Sources:")
            print(f"   From mapper.attrs: {[p.key for p in Child.__mapper__.attrs]}")
            print(f"   From annotations: {list(Child.__annotations__.keys())}")
            print(
                "   From table columns: "
                + f"{[col.name for col in Child.__table__.columns]}"
            )
            tmp_output = (
                list(Child.__fields__.keys())
                if hasattr(Child, "__fields__")
                else "No __fields__"
            )
            print(f"   From SQLModel fields: {tmp_output}")


def test_form_data_processing():
    """Debug test to reproduce the exact form data processing issue"""
    from sqlmodel import Field
    from sqlmodel import SQLModel

    from flask_admin import Admin
    from flask_admin.contrib.sqlmodel import SQLModelView

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite:///:memory:")

    with app.app_context():
        # Recreate the exact test scenario
        class Parent(SQLModel):
            id: int = Field(primary_key=True)
            test: str

        class Child(Parent, table=True):
            id2: int = Field(primary_key=True)
            name: str
            __mapper_args__ = {"concrete": True}

        SQLModel.metadata.create_all(engine)

        print("\n=== Testing Form Data Processing Issue ===")

        admin = Admin(app)

        with Session(engine) as db_session:
            # Create a custom view with debug output like PkModelView
            class DebugModelView(SQLModelView):
                def create_model(self, form):
                    print(f"🔍 Form data received: {form.data}")
                    print(f"🔍 Form fields: {list(form._fields.keys())}")

                    model = self.model()
                    print(f"🔍 Empty model before populate: {model}")

                    form.populate_obj(model)
                    print(f"🔍 Model after populate: {model}")

                    return model

                def scaffold_form(self):
                    print(f"🔍 Scaffolding form for model: {self.model}")
                    print(f"🔍 Model mapper class: {self.model.__mapper__.class_}")
                    print(
                        "🔍 Are they equal? "
                        + f"{self.model == self.model.__mapper__.class_}"
                    )
                    try:
                        form = super().scaffold_form()
                        if form is None:
                            print("🔍 scaffold_form() returned None!")
                        else:
                            print(f"🔍 Form class created: {form}")
                            tmp_output = (
                                list(form._fields.keys())
                                if hasattr(form, "_fields")
                                else "No _fields"
                            )
                            print(f"🔍 Form fields: {tmp_output}")
                        return form
                    except Exception as e:
                        print(f"🔍 scaffold_form() failed: {e}")
                        import traceback

                        traceback.print_exc()
                        return None

            view = DebugModelView(Child, db_session)
            admin.add_view(view)

            # Create a test form manually to see what fields are created
            form_class = view.scaffold_form()
            print(f"🔍 Form class: {form_class}")

            if form_class is not None:
                # Create form instance with the test data
                form_data = {"id": 1, "id2": 2, "test": "foo", "name": "bar"}
                form = form_class(data=form_data)
                print(f"🔍 Form instance fields: {list(form._fields.keys())}")
                print(f"🔍 Form data: {form.data}")

                # Test model creation
                model = view.create_model(form)
                print(f"🔍 Final model: {model}")
            else:
                print("🔍 Cannot test form creation - scaffold_form() returned None")


def test_inheritance_variants():
    """Debug test to compare different inheritance patterns"""
    from sqlmodel import Field
    from sqlmodel import SQLModel

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite://")

    with app.app_context():
        print("\n=== Testing Different Inheritance Patterns ===")

        # Test 1: Single table inheritance
        class SingleParent(SQLModel):
            id: int = Field(primary_key=True)
            test: str

        class SingleChild(SingleParent, table=True):
            name: str

        SQLModel.metadata.create_all(engine)

        print("Single table inheritance:")
        print(
            "  SingleChild mapper attrs: "
            + f"{[p.key for p in SingleChild.__mapper__.attrs]}"
        )
        print(
            "  SingleChild table columns: "
            + f"{[col.name for col in SingleChild.__table__.columns]}"
        )

        # Test 2: Concrete inheritance
        class ConcreteParent(SQLModel):
            id: int = Field(primary_key=True)
            test: str

        class ConcreteChild(ConcreteParent, table=True):
            name: str
            __mapper_args__ = {"concrete": True}

        SQLModel.metadata.create_all(engine)

        print("\nConcrete inheritance:")
        print(
            "  ConcreteChild mapper attrs: "
            + f"{[p.key for p in ConcreteChild.__mapper__.attrs]}"
        )
        print(
            "  ConcreteChild table columns: "
            + f"{[col.name for col in ConcreteChild.__table__.columns]}"
        )

        # Test 3: Concrete inheritance with multiple PKs
        class MultiPKParent(SQLModel):
            id: int = Field(primary_key=True)
            test: str

        class MultiPKChild(MultiPKParent, table=True):
            id2: int = Field(primary_key=True)
            name: str
            __mapper_args__ = {"concrete": True}

        SQLModel.metadata.create_all(engine)

        print("\nConcrete inheritance with multiple PKs:")
        print(
            "  MultiPKChild mapper attrs: "
            + f"{[p.key for p in MultiPKChild.__mapper__.attrs]}"
        )
        print(
            "  MultiPKChild table columns: "
            + f"{[col.name for col in MultiPKChild.__table__.columns]}"
        )
        print(
            "  MultiPKChild primary key columns: +"
            f"{[col.name for col in MultiPKChild.__table__.primary_key.columns]}"
        )


def test_relationship_filter_joins():
    """Debug test for relationship filter join issues"""
    import warnings

    import sqlalchemy

    from flask_admin import Admin
    from flask_admin.contrib.sqlmodel import SQLModelView
    from flask_admin.contrib.sqlmodel.tools import get_field_with_path

    # Capture SQL warnings
    caught_warnings = []

    def warning_handler(message, category, filename, lineno, file=None, line=None):
        if category == sqlalchemy.exc.SAWarning:
            caught_warnings.append(str(message))

    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite:///:memory:")
    admin = Admin(app)

    print("\n=== Testing Relationship Filter Joins ===")

    with app.app_context():
        Model1, Model2 = create_models(engine)

        with Session(engine) as db_session:
            # Test basic relationship filter setup
            print("🔍 Testing get_field_with_path for 'model1.bool_field':")
            attr, path = get_field_with_path(Model2, "model1.bool_field")
            print(f"   attr: {attr}")
            print(f"   path: {path}")

            # Test filter scaffolding
            class TestView(SQLModelView):
                column_filters = ["model1.bool_field"]

            view = TestView(Model2, db_session)

            print("🔍 Filter joins setup:")
            print(f"   _filter_joins: {view._filter_joins}")
            print(f"   _filters count: {len(view._filters)}")

            # Add some test data
            m1 = Model1(test1="test", test2="test2")
            m2 = Model2(string_field="test", model1=m1)
            db_session.add_all([m1, m2])
            db_session.commit()

            admin.add_view(view)

            # Test the query building
            print("🔍 Testing query building:")
            try:
                # This should trigger the cartesian product warning
                count, data = view.get_list(0, None, None, None, None)
                print(f"   Query succeeded: count={count}, data_len={len(data)}")
            except Exception as e:
                print(f"   Query failed: {e}")

            # Test with actual filter applied
            print("🔍 Testing with filter applied:")
            try:
                # Apply a filter to see the actual query
                filters = [(0, "bool_field", True)]  # Filter index 0, field name, value
                count, data = view.get_list(0, None, None, None, filters)
                print(
                    f"   Filtered query succeeded: count={count}, data_len={len(data)}"
                )
            except Exception as e:
                print(f"   Filtered query failed: {e}")

            # Check if warnings were captured
            if caught_warnings:
                print("🔍 SQL Warnings captured:")
                for warning in caught_warnings:
                    print(f"   {warning}")
            else:
                print("🔍 No SQL warnings captured")

            # Test manual query to understand the issue
            print("🔍 Testing manual query:")
            try:
                from sqlmodel import select

                query = select(Model2)

                # Check what happens when we apply the filter manually
                filter_obj = view._filters[0]
                print(f"   Filter object: {filter_obj}")
                print(f"   Filter column: {filter_obj.column}")

                # Try to apply the filter
                filtered_query = filter_obj.apply(query, True)
                print(f"   Filtered query: {filtered_query}")

                # Execute the query
                result = db_session.exec(filtered_query).all()
                print(f"   Result: {result}")

            except Exception as e:
                print(f"   Manual query failed: {e}")
                import traceback

                traceback.print_exc()

    # Restore original warning handler
    warnings.showwarning = old_showwarning


def test_property_filtering_pagination():
    """Debug test for property filtering pagination issue"""
    import uuid

    from sqlmodel import Field
    from sqlmodel import SQLModel

    from flask_admin import Admin
    from flask_admin.contrib.sqlmodel import SQLModelView

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite:///:memory:")

    with app.app_context():
        # Create test model with property
        class PropertyTestModel(SQLModel, table=True):
            __tablename__ = "property_test"

            id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
            first_name: str
            last_name: str
            category: str

            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

            @full_name.setter
            def full_name(self, value: str):
                if value and value.strip():
                    parts = value.split(" ", 1)
                    self.first_name = parts[0]
                    self.last_name = parts[1] if len(parts) > 1 else ""

        SQLModel.metadata.create_all(engine)

        print("\n=== Testing Property Filtering Pagination Issue ===")

        admin = Admin(app)

        with Session(engine) as db_session:
            # Create test data
            test_records = []

            # 10 Smith records (should match "smith" filter)
            for i in range(10):
                record = PropertyTestModel(
                    first_name=f"Person{i}", last_name="Smith", category="A"
                )
                test_records.append(record)

            # 5 Johnson records (should not match "smith" filter)
            for i in range(5):
                record = PropertyTestModel(
                    first_name=f"User{i}", last_name="Johnson", category="B"
                )
                test_records.append(record)

            # Save all records
            for record in test_records:
                db_session.add(record)
            db_session.commit()

            print(f"🔍 Created {len(test_records)} total records:")
            print("   10 Smith records (should match 'smith' filter)")
            print("   5 Johnson records (should not match)")

            # Create view with small page size
            class PropertyTestModelView(SQLModelView):
                page_size = 3  # Small page size to test pagination
                column_list = ["id", "first_name", "last_name", "full_name", "category"]
                column_filters = ["first_name", "last_name", "full_name", "category"]

            view = PropertyTestModelView(PropertyTestModel, db_session)
            admin.add_view(view)

            print(f"🔍 View page_size: {view.page_size}")
            print(f"🔍 View filters: {view.column_filters}")
            print(f"🔍 Total filters created: {len(view._filters)}")

            # Test client requests
            client = app.test_client()

            print("\n🔍 Testing basic list view (no filters):")
            try:
                rv = client.get("/admin/propertytestmodel/")
                print(f"   Status: {rv.status_code}")
                if rv.status_code == 200:
                    # Count records shown on first page
                    smith_count = rv.text.count("Smith")
                    johnson_count = rv.text.count("Johnson")
                    print(f"   Page 0 - Smith: {smith_count}, Johnson: {johnson_count}")
                else:
                    print("   Error response")
            except Exception as e:
                print(f"   Exception: {e}")

            print("\n🔍 Testing property filter (full_name contains 'smith'):")

            # Determine which filter index corresponds to full_name
            for i, flt in enumerate(view._filters):
                if hasattr(flt, "column") and isinstance(flt.column, property):
                    # This might be our full_name property filter
                    print(
                        f"   Filter {i}: {flt.__class__.__name__}"
                        + f" on property {flt.column}"
                    )
                    break

            # Test different filter parameter formats
            test_urls = [
                f"/admin/propertytestmodel/?flt{i}_2=smith"
                for i in range(min(5, len(view._filters)))
            ]

            for test_url in test_urls:
                print(f"\n🔍 Testing: {test_url}")
                try:
                    rv = client.get(test_url)
                    print(f"   Status: {rv.status_code}")

                    if rv.status_code == 200:
                        smith_count = rv.text.count("Smith")
                        johnson_count = rv.text.count("Johnson")
                        print(f"   Smith: {smith_count}, Johnson: {johnson_count}")

                        if smith_count > 0 and johnson_count == 0:
                            print(f"   ✓ Property filter working! URL: {test_url}")

                            # Test pagination of filtered results
                            print("   🔍 Testing pagination of filtered results:")
                            print(
                                f"       Expected: page_size={view.page_size}, "
                                + f"so should show {view.page_size} "
                                + "Smith records per page"
                            )
                            print(
                                f"       Actual: showing {smith_count}"
                                + " Smith records on page 0"
                            )

                            if smith_count == view.page_size:
                                print(
                                    "       ✓ Correct pagination! Showing exactly "
                                    + f"{view.page_size} records"
                                )
                            elif smith_count < view.page_size:
                                print(
                                    "       ⚠ PAGINATION ISSUE: Showing only "
                                    + f"{smith_count} of expected {view.page_size} "
                                    + "records"
                                )
                                print(
                                    "         This indicates post-query filtering is "
                                    + "happening AFTER pagination"
                                )
                            else:
                                print(
                                    "       ⚠ Unexpected: Showing more records "
                                    + f"({smith_count}) than page size "
                                    + f"({view.page_size})"
                                )

                            # Test second page
                            page1_url = test_url + "&page=1"
                            print(f"   🔍 Testing page 1: {page1_url}")
                            try:
                                rv1 = client.get(page1_url)
                                if rv1.status_code == 200:
                                    smith_count_p1 = rv1.text.count("Smith")
                                    print(f"Page 1 Smith records: {smith_count_p1}")
                                    if smith_count_p1 == view.page_size:
                                        print("Page 1 has correct number of records")
                                    elif smith_count_p1 > 0:
                                        print(
                                            "Page 1 has some records "
                                            + "(pagination working)"
                                        )
                                    else:
                                        print(
                                            "Page 1 has no records (pagination issue)"
                                        )
                                else:
                                    print(f"       Page 1 error: {rv1.status_code}")
                            except Exception as e:
                                print(f"       Page 1 exception: {e}")

                            break
                    else:
                        print(f"   Error status: {rv.status_code}")

                except Exception as e:
                    print(f"   Exception: {e}")

            print("\n🔍 Testing regular field filter for comparison:")
            try:
                # Test regular field filter (category)
                rv = client.get(
                    "/admin/propertytestmodel/?flt1_0=A"
                )  # category equals A
                print(f"   Status: {rv.status_code}")
                if rv.status_code == 200:
                    a_count = (
                        rv.text.count('category="A"')
                        + rv.text.count("category='A'")
                        + rv.text.count(">A<")
                    )
                    print(f"   Category A records shown: {a_count}")
                    print(f"   Regular field filtering working: {a_count > 0}")
            except Exception as e:
                print(f"   Regular filter exception: {e}")


def test_filter_joins_detailed():
    """Debug test for detailed filter joins analysis (from debug_filter_joins.py)"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite:///:memory:")
    Model1, Model2 = create_models(engine)

    with app.app_context():
        with Session(engine) as db_session:
            print("\n=== Testing Detailed Filter Joins ===")

            # Test the problematic view: Model2 with "model1.bool_field" filter
            view = CustomModelView(
                Model2, db_session, column_filters=["model1.bool_field"]
            )

            print(f"🔍 Model: {view.model}")
            print(f"🔍 Column filters: {view.column_filters}")
            print(f"🔍 _filter_joins keys: {list(view._filter_joins.keys())}")
            print(
                "🔍 _filter_name_to_joins keys: "
                + f"{list(view._filter_name_to_joins.keys())}"
            )
            print(f"🔍 Number of filters: {len(view._filters) if view._filters else 0}")

            if view._filters:
                for i, flt in enumerate(view._filters):
                    print(f"🔍 Filter {i}:")
                    print(f"   Name: {flt.name}")
                    print(f"   Column: {flt.column}")
                    print(f"   Column key: {getattr(flt.column, 'key', 'N/A')}")
                    print(f"   Key name: {getattr(flt, 'key_name', 'N/A')}")
                    print(f"   Type: {type(flt).__name__}")

            # Try to get the list to see where the cartesian product happens
            try:
                count, data = view.get_list(0, None, None, None, None)
                print(f"✓ Success! Count: {count}, Data length: {len(data)}")
            except Exception as e:
                print(f"✗ Error during get_list: {e}")
                import traceback

                traceback.print_exc()


def test_uuid_type_names():
    """Debug test for UUID type name analysis (from debug_uuid_types.py)"""
    import inspect
    import uuid
    from typing import Optional

    from sqlalchemy import Column
    from sqlalchemy.sql.sqltypes import Uuid as SQLAlchemyUuid
    from sqlmodel import create_engine
    from sqlmodel import Field
    from sqlmodel import SQLModel

    engine = create_engine("sqlite:///:memory:")

    # Test SQLModel with UUID field
    class UUIDTestModel(SQLModel, table=True):
        __tablename__ = "uuid_test"

        id: int = Field(primary_key=True)
        uuid_field: uuid.UUID = Field(sa_column=Column(SQLAlchemyUuid()))
        optional_uuid: Optional[uuid.UUID] = Field(
            default=None, sa_column=Column(SQLAlchemyUuid())
        )
        native_uuid: uuid.UUID = Field(
            default_factory=uuid.uuid4
        )  # Native SQLModel UUID

    SQLModel.metadata.create_all(engine)
    print("\n=== Testing UUID Type Names ===")

    # Get the mapper for the test model
    mapper = UUIDTestModel._sa_class_manager.mapper

    # Check each property
    for prop in mapper.attrs:
        if "uuid" in prop.key.lower():
            print(f"\n🔍 Property: {prop.key}")
            if hasattr(prop, "columns") and prop.columns:
                column = prop.columns[0]
                print(f"   Column type: {type(column.type)}")
                print(f"   Column type name: {type(column.type).__name__}")
                print(f"   Column type module: {type(column.type).__module__}")
                print(
                    "   Full type string: "
                    + f"{type(column.type).__module__}.{type(column.type).__name__}"
                )

                # Show MRO (Method Resolution Order)
                mro = inspect.getmro(type(column.type))
                print("   MRO (Method Resolution Order):")
                for i, cls in enumerate(mro[:3]):  # Show first 3 levels
                    type_string = f"{cls.__module__}.{cls.__name__}"
                    print(f"     {i}: {type_string}")

    # Test with pure Python UUID type
    print("\n🔍 Pure Python UUID Type:")
    print(f"   uuid.UUID module: {uuid.UUID.__module__}")
    print(f"   uuid.UUID name: {uuid.UUID.__name__}")
    print(f"   uuid.UUID full string: {uuid.UUID.__module__}.{uuid.UUID.__name__}")


def test_column_filters_minimal():
    """Minimal test to reproduce the column filters issue"""
    import warnings

    import sqlalchemy

    from flask_admin import Admin

    # Treat warnings as errors to catch the issue
    warnings.filterwarnings("error", category=sqlalchemy.exc.SAWarning)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False

    engine = create_engine("sqlite:///:memory:")
    admin = Admin(app)

    print("\n=== Testing Column Filters Minimal ===")

    with app.app_context():
        Model1, Model2 = create_models(engine)

        with Session(engine) as db_session:
            # Create the same view configuration as in the failing test
            view9 = CustomModelView(
                Model2,
                db_session,
                endpoint="_model2",
                column_filters=["model1.bool_field"],
                column_list=[
                    "string_field",
                    "model1.id",
                    "model1.bool_field",
                ],
            )
            admin.add_view(view9)

            # Add some test data
            from flask_admin.tests.sqlmodel import fill_db

            fill_db(db_session, Model1, Model2)

            # Test the web request that was failing
            client = app.test_client()

            print("🔍 Testing web request that was failing:")
            try:
                rv = client.get("/admin/_model2/")
                print(f"   Status: {rv.status_code}")
                print("   Success!")
            except Exception as e:
                print(f"   Failed: {e}")
                import traceback

                traceback.print_exc()


if __name__ == "__main__":
    print("Running SQLModel Flask-Admin Debug Tests")
    print("=" * 50)

    test_filter_group_naming()
    test_column_list_with_relationships()
    test_relationship_field_handling()
    test_primary_key_detection()
    test_field_type_detection()
    test_dot_notation_filter_naming()
    test_filter_joins_setup()
    test_concrete_inheritance_field_discovery()
    test_form_data_processing()
    test_inheritance_variants()
    test_relationship_filter_joins()
    test_property_filtering_pagination()
    test_filter_joins_detailed()
    test_uuid_type_names()
    test_column_filters_minimal()

    print("\nDebug tests completed!")
