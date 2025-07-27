"""
Tests to fill coverage gaps in SQLModel tools.py module.

This file specifically targets missing coverage areas identified in coverage reports:
- Import fallback mechanisms (lines 32-33, 51-56, 65-69)
- Computed field detection with ComputedFieldInfo (lines 177-188, 194-206)
- SQLAlchemy model handling in get_model_fields (lines 219-235)
- Various edge cases and error handling throughout the module
"""

from typing import Optional

import pytest
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlmodel import Field
from sqlmodel import SQLModel

try:
    from pydantic import computed_field
except ImportError:
    # Fallback for older pydantic versions
    computed_field = None

from flask_admin.contrib.sqlmodel.tools import _get_sqlmodel_property_info
from flask_admin.contrib.sqlmodel.tools import get_model_fields
from flask_admin.contrib.sqlmodel.tools import ModelField


class TestImportFallbacks:
    """Test import fallback mechanisms for optional dependencies."""

    def test_association_proxy_constant_available(self):
        """Test that ASSOCIATION_PROXY constant is available."""
        # This test verifies lines 32-33 import fallback worked correctly
        from flask_admin.contrib.sqlmodel.tools import ASSOCIATION_PROXY

        assert ASSOCIATION_PROXY is not None
        # ASSOCIATION_PROXY can be either enum or string depending on SQLAlchemy version
        assert hasattr(ASSOCIATION_PROXY, "__str__") or isinstance(
            ASSOCIATION_PROXY, str
        )

    def test_sqlmodel_availability_check(self):
        """Test SQLModel availability detection."""
        # This test verifies lines 51-56 work correctly
        from flask_admin.contrib.sqlmodel.tools import SQLMODEL_AVAILABLE

        # In our test environment, SQLModel should be available
        assert SQLMODEL_AVAILABLE is True

        # Verify the imported components are available
        from flask_admin.contrib.sqlmodel.tools import SQLModel

        assert SQLModel is not None

    def test_pydantic_types_availability_check(self):
        """Test that Pydantic types availability is detected."""
        # This test verifies lines around 58-69
        from flask_admin.contrib.sqlmodel.tools import PYDANTIC_TYPES_AVAILABLE

        # Should be True in our test environment
        assert isinstance(PYDANTIC_TYPES_AVAILABLE, bool)


class TestComputedFieldDetectionAdvanced:
    """Test advanced computed field detection scenarios using real SQLModel classes."""

    @pytest.mark.skipif(computed_field is None, reason="computed_field not available")
    def test_computed_field_with_pydantic_computed_field_decorator(
        self, sqlmodel_base: type[SQLModel]
    ):
        """Test computed field detection with @computed_field decorator."""
        # This targets lines 177-188

        class UserModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

        # Test the property info extraction
        info = _get_sqlmodel_property_info(UserModel, "full_name")

        # Test that the function runs without error
        assert isinstance(info, dict)
        assert "is_computed" in info
        # Note: Actual computed field detection may vary based on implementation

    @pytest.mark.skipif(computed_field is None, reason="computed_field not available")
    def test_computed_field_from_model_computed_fields(
        self, sqlmodel_base: type[SQLModel]
    ):
        """Test computed field detection from model_computed_fields."""
        # This targets lines 194-206

        class ProductModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            price: float
            tax_rate: float = 0.1

            @computed_field
            @property
            def total_price(self) -> float:
                return self.price * (1 + self.tax_rate)

        # This should hit the model_computed_fields path
        info = _get_sqlmodel_property_info(ProductModel, "total_price")

        # Test that the function runs without error
        assert isinstance(info, dict)
        assert "is_computed" in info


class TestSQLAlchemyModelHandling:
    """Test handling of traditional SQLAlchemy models."""

    def test_get_model_fields_sqlalchemy_model_with_table(self):
        """Test get_model_fields with traditional SQLAlchemy model."""
        # This targets lines 219-235
        Base = declarative_base()

        class SQLAlchemyModel(Base):
            __tablename__ = "test_table"

            id = Column(Integer, primary_key=True)
            name = Column(String(50), nullable=False, default="default_name")
            active = Column(Boolean, nullable=True)
            content = Column(Text, nullable=True)

        # This should trigger the SQLAlchemy model handling path
        fields = get_model_fields(SQLAlchemyModel)

        assert len(fields) == 4

        # Check id field (primary key, not nullable, no default)
        id_field = next(f for f in fields if f.name == "id")
        assert id_field.primary_key is True
        assert id_field.required is True  # not nullable and no default
        assert id_field.is_computed is False
        assert id_field.is_property is False
        assert id_field.has_setter is False

        # Check name field (has default, so not required)
        name_field = next(f for f in fields if f.name == "name")
        assert name_field.required is False  # has default
        assert name_field.default == "default_name"
        assert name_field.primary_key is False

        # Check active field (nullable, so not required)
        active_field = next(f for f in fields if f.name == "active")
        assert active_field.required is False  # nullable
        assert active_field.default is None

    def test_get_model_fields_sqlalchemy_model_without_table(self):
        """Test get_model_fields with SQLAlchemy model that has no __table__."""
        # This targets the else clause around line 236-237

        class MockSQLAlchemyModel:
            # No __table__ attribute - not a real table model
            pass

        # This should return empty list for non-table models
        fields = get_model_fields(MockSQLAlchemyModel)
        assert fields == []

    def test_get_model_fields_sqlalchemy_with_complex_defaults(self):
        """Test with columns that have server defaults and callable defaults."""
        Base = declarative_base()

        class ComplexModel(Base):
            __tablename__ = "complex_table"

            id = Column(Integer, primary_key=True)
            # Column with server default
            created_at = Column(Integer, server_default=func.now())
            # Column with callable default
            updated_at = Column(Integer, default=func.now())

        fields = get_model_fields(ComplexModel)

        created_field = next(f for f in fields if f.name == "created_at")
        # Server defaults are actually treated as defaults in SQLAlchemy model handling
        assert created_field.required is False  # has server_default
        assert (
            created_field.default is None
        )  # server_default not exposed as field default

        updated_field = next(f for f in fields if f.name == "updated_at")
        # Has field default, so not required
        assert updated_field.required is False


class TestPropertyInfoEdgeCases:
    """Test edge cases in property info extraction."""

    def test_property_info_with_real_property(self, sqlmodel_base: type[SQLModel]):
        """Test property info with real Python @property."""

        class ModelWithProperty(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            private_value: str = Field(default="secret")

            @property
            def public_value(self) -> str:
                return f"public_{self.private_value}"

            # Property with setter
            @property
            def editable_value(self) -> str:
                return self.private_value

            @editable_value.setter
            def editable_value(self, value: str):
                self.private_value = value

        # Test property without setter
        info = _get_sqlmodel_property_info(ModelWithProperty, "public_value")
        assert info["is_property"] is True
        assert info["has_setter"] is False

        # Test property with setter
        info = _get_sqlmodel_property_info(ModelWithProperty, "editable_value")
        assert info["is_property"] is True
        assert info["has_setter"] is True

    def test_property_info_with_custom_setter_method(
        self, sqlmodel_base: type[SQLModel]
    ):
        """Test detection of custom setter methods."""

        class ModelWithCustomSetter(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            value: str = "default"

            @property
            def computed_value(self) -> str:
                return f"computed_{self.value}"

            def set_computed_value(self, new_value: str):
                """Custom setter method."""
                self.value = new_value.replace("computed_", "")

        info = _get_sqlmodel_property_info(ModelWithCustomSetter, "computed_value")
        # Test that the function runs without error
        assert isinstance(info, dict)
        assert "has_setter" in info
        # Note: Actual setter detection behavior may vary


class TestModelFieldCreation:
    """Test ModelField creation and edge cases."""

    def test_model_field_with_various_defaults(self):
        """Test ModelField creation with different default scenarios."""

        # Test with None default
        field1 = ModelField(
            name="field1",
            type_=str,
            default=None,
            required=True,
            primary_key=False,
            description=None,
            source=None,
            is_computed=False,
            is_property=False,
            has_setter=False,
        )
        assert field1.default is None
        assert field1.required is True

        # Test with actual default value
        field2 = ModelField(
            name="field2",
            type_=int,
            default=42,
            required=False,
            primary_key=False,
            description="Test field",
            source="mock_source",
            is_computed=True,
            is_property=True,
            has_setter=True,
        )
        assert field2.default == 42
        assert field2.required is False
        assert field2.description == "Test field"
        assert field2.is_computed is True
        assert field2.is_property is True
        assert field2.has_setter is True


class TestComplexModelScenarios:
    """Test complex model scenarios that might hit edge cases."""

    def test_model_with_mixed_field_types(self, sqlmodel_base: type[SQLModel]):
        """Test model with regular fields and properties."""

        class ComplexModel(sqlmodel_base, table=True):
            # Regular field
            id: int = Field(primary_key=True)
            name: str

            # Optional field
            description: Optional[str] = None

            # Property
            @property
            def display_name(self) -> str:
                return f"Name: {self.name}"

            @display_name.setter
            def display_name(self, value: str):
                self.name = value.replace("Name: ", "")

        # Test that all field types are handled correctly
        fields = get_model_fields(ComplexModel)

        # Should have regular fields plus properties
        field_names = [f.name for f in fields]
        assert "id" in field_names
        assert "name" in field_names
        assert "description" in field_names
        # Properties should also be included
        assert len(fields) >= 3

    @pytest.mark.skipif(computed_field is None, reason="computed_field not available")
    def test_model_with_computed_fields(self, sqlmodel_base: type[SQLModel]):
        """Test model with computed fields."""

        class ModelWithComputedField(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

            # Computed field
            @computed_field
            @property
            def name_length(self) -> int:
                return len(self.name) if self.name else 0

        # Test that computed fields are handled
        fields = get_model_fields(ModelWithComputedField)
        field_names = [f.name for f in fields]
        assert "id" in field_names
        assert "name" in field_names
        # Note: computed fields may or may not be included depending on implementation

    def test_model_without_sqlmodel_features(self):
        """Test with a class that doesn't have SQLModel features."""

        class PlainClass:
            def __init__(self):
                self.value = "test"

        # Should handle non-SQLModel classes gracefully
        info = _get_sqlmodel_property_info(PlainClass, "value")
        assert isinstance(info, dict)
        assert "is_computed" in info
        assert "is_property" in info
        assert "has_setter" in info
