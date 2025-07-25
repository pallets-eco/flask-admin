"""
Integration tests for SQLModel property and computed field support in forms.

This module tests the enhanced Flask-Admin SQLModel integration that includes:
- @property decorators with and without setters
- @computed_field decorators from Pydantic v2
- Automatic inclusion of properties with setters in forms
- Explicit inclusion via form_columns configuration
- WTForms compatibility for editable properties and computed fields
"""

from typing import Optional

from pydantic import computed_field
from sqlalchemy import String
from sqlmodel import Field
from sqlmodel import SQLModel
from wtforms import fields

from flask_admin.contrib.sqlmodel.tools import get_readonly_fields
from flask_admin.contrib.sqlmodel.tools import get_wtform_compatible_fields
from flask_admin.contrib.sqlmodel.view import SQLModelView


class TestPropertyComputedFieldIntegration:
    """Integration tests for property and computed field support."""

    def test_property_with_setter_auto_inclusion(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test that properties with setters are automatically included in forms."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class PropertyTestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(sa_type=String)
            internal_value: Optional[str] = Field(default=None, sa_type=String)

            @property
            def display_name(self) -> str:
                """Property with setter - should be automatically included in forms."""
                return self.internal_value or f"Display: {self.name}"

            @display_name.setter
            def display_name(self, value: str):
                """Setter makes this property WTForms compatible."""
                self.internal_value = value

            @property
            def readonly_name(self) -> str:
                """Property without setter - should not be in forms by default."""
                return f"Readonly: {self.name}"

        view = SQLModelView(PropertyTestModel, session, name="Property Test")

        with app.app_context():
            # Test form generation
            form = view.create_form()

            # Property with setter should be included automatically
            assert "display_name" in form._fields
            assert isinstance(form.display_name, fields.StringField) # type: ignore

            # Property without setter should not be included by default
            assert "readonly_name" not in form._fields

            # Regular fields should still be included
            assert "name" in form._fields
            assert "internal_value" in form._fields

    def test_computed_field_explicit_inclusion(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test that computed fields with setters can be
        explicitly included via form_columns."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class ComputedFieldTestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(sa_type=String)
            age: int = Field()
            internal_score: Optional[int] = Field(default=None)

            @computed_field
            @property
            def computed_info(self) -> str:
                """Read-only computed field."""
                return f"{self.name}, age {self.age}"

            @computed_field
            @property
            def computed_score(self) -> int:
                """Computed field with custom setter method."""
                return self.internal_score or (self.age * 10)

            def set_computed_score(self, value: int):
                """Custom setter method enables WTForms compatibility."""
                self.internal_score = value

        # Test default view (computed fields not included by default)
        default_view = SQLModelView(ComputedFieldTestModel, session, name="Default")

        with app.app_context():
            default_form = default_view.create_form()
            assert "computed_info" not in default_form._fields
            assert "computed_score" not in default_form._fields

        # Test explicit inclusion via form_columns
        class ExplicitView(SQLModelView):
            form_columns = ["id", "name", "age", "computed_score"]

        explicit_view = ExplicitView(ComputedFieldTestModel, session, name="Explicit")

        with app.app_context():
            explicit_form = explicit_view.create_form()

            # Computed field with setter should be included when explicit
            assert "computed_score" in explicit_form._fields
            assert isinstance(explicit_form.computed_score, fields.IntegerField) # type: ignore

            # Read-only computed field should not be included even when explicit
            # (unless specifically configured to include read-only fields)
            assert "computed_info" not in explicit_form._fields

    def test_wtforms_compatibility_detection(self, sqlmodel_base: type[SQLModel]):
        """Test that WTForms compatibility detection works correctly."""

        class CompatibilityTestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(sa_type=String)
            internal_temp: Optional[int] = Field(default=None)

            # Property with setter - WTForms compatible
            @property
            def editable_prop(self) -> str:
                return f"Editable: {self.name}"

            @editable_prop.setter
            def editable_prop(self, value: str):
                pass

            # Property without setter - not WTForms compatible
            @property
            def readonly_prop(self) -> str:
                return f"Readonly: {self.name}"

            # Computed field with custom setter - WTForms compatible
            @computed_field
            @property
            def computed_editable(self) -> int:
                return self.internal_temp or 42

            def set_computed_editable(self, value: int):
                self.internal_temp = value

            # Computed field without setter - not WTForms compatible
            @computed_field
            @property
            def computed_readonly(self) -> str:
                return f"Computed: {self.name}"

        # Test field categorization
        wtform_compatible = get_wtform_compatible_fields(CompatibilityTestModel)
        readonly_fields = get_readonly_fields(CompatibilityTestModel)

        # Check WTForms compatible fields
        wtform_names = [f.name for f in wtform_compatible]
        assert "editable_prop" in wtform_names
        assert "computed_editable" in wtform_names
        assert "readonly_prop" not in wtform_names
        assert "computed_readonly" not in wtform_names

        # Check read-only fields
        readonly_names = [f.name for f in readonly_fields]
        assert "readonly_prop" in readonly_names
        assert "computed_readonly" in readonly_names
        assert "editable_prop" not in readonly_names
        assert "computed_editable" not in readonly_names

    def test_form_field_types_inference(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test that form field types are correctly inferred
        from property/computed field return types."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class TypeInferenceModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(sa_type=String)
            internal_int: Optional[int] = Field(default=None)
            internal_float: Optional[float] = Field(default=None)
            internal_bool: Optional[bool] = Field(default=None)

            @property
            def int_property(self) -> int:
                return self.internal_int or 0

            @int_property.setter
            def int_property(self, value: int):
                self.internal_int = value

            @property
            def float_property(self) -> float:
                return self.internal_float or 0.0

            @float_property.setter
            def float_property(self, value: float):
                self.internal_float = value

            @property
            def bool_property(self) -> bool:
                return self.internal_bool or False

            @bool_property.setter
            def bool_property(self, value: bool):
                self.internal_bool = value

        class TypedView(SQLModelView):
            form_columns = [
                "id",
                "name",
                "int_property",
                "float_property",
                "bool_property",
            ]

        view = TypedView(TypeInferenceModel, session, name="Type Test")

        with app.app_context():
            form = view.create_form()

            # Check that field types are correctly inferred
            assert isinstance(form.int_property, fields.IntegerField) # type: ignore
            assert isinstance(form.float_property, fields.DecimalField) # type: ignore
            assert isinstance(form.bool_property, fields.BooleanField) # type: ignore

    def test_form_population_with_properties(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test that form population works correctly
        with properties and computed fields."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class PopulationTestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(sa_type=String)
            internal_display: Optional[str] = Field(default=None, sa_type=String)
            internal_score: Optional[int] = Field(default=None)

            @property
            def display_name(self) -> str:
                return self.internal_display or f"Display: {self.name}"

            @display_name.setter
            def display_name(self, value: str):
                self.internal_display = value

            @computed_field
            @property
            def score(self) -> int:
                return self.internal_score or 100

            def set_score(self, value: int):
                self.internal_score = value

        class PopulationView(SQLModelView):
            form_columns = ["name", "display_name", "score"]

        view = PopulationView(PopulationTestModel, session, name="Population Test")

        with app.app_context():
            # Create test instance
            instance = PopulationTestModel(name="Test User") # type: ignore
            instance.display_name = "Custom Display"
            instance.set_score(150)

            # Test form population
            form = view.edit_form(instance)

            assert form.name.data == "Test User" # type: ignore
            assert form.display_name.data == "Custom Display" # type: ignore
            assert form.score.data == 150 # type: ignore

    def test_backward_compatibility(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test that the enhancements don't break existing SQLModel functionality."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class BasicModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str = Field(sa_type=String)
            age: int = Field()

        view = SQLModelView(BasicModel, session, name="Basic Model")

        with app.app_context():
            # Test that basic form generation still works
            form = view.create_form()

            assert "id" in form._fields
            assert "name" in form._fields
            assert "age" in form._fields
            assert isinstance(form.name, fields.StringField) # type: ignore
            assert isinstance(form.age, fields.IntegerField) # type: ignore

            # Test form functionality
            instance = BasicModel(name="John", age=30) # type: ignore
            edit_form = view.edit_form(instance)

            assert edit_form.name.data == "John" # type: ignore
            assert edit_form.age.data == 30 # type: ignore
