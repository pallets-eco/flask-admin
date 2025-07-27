"""
Comprehensive tests for SQLModel tools module to maximize coverage.

This file focuses on testing functionality that's missing from test_tools_extended.py,
particularly around primary keys, relationships, computed fields,
queries, and edge cases.
"""

from typing import Any
from typing import Optional
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.schema import Table
from sqlmodel import Field
from sqlmodel import SQLModel

from flask_admin.contrib.sqlmodel.tools import filter_foreign_columns
from flask_admin.contrib.sqlmodel.tools import get_all_model_fields
from flask_admin.contrib.sqlmodel.tools import get_computed_fields
from flask_admin.contrib.sqlmodel.tools import get_field_with_path
from flask_admin.contrib.sqlmodel.tools import get_hybrid_properties
from flask_admin.contrib.sqlmodel.tools import get_model_table
from flask_admin.contrib.sqlmodel.tools import get_primary_key
from flask_admin.contrib.sqlmodel.tools import get_query_for_ids
from flask_admin.contrib.sqlmodel.tools import get_sqlmodel_column_names
from flask_admin.contrib.sqlmodel.tools import get_sqlmodel_field_names
from flask_admin.contrib.sqlmodel.tools import get_sqlmodel_fields
from flask_admin.contrib.sqlmodel.tools import get_sqlmodel_properties
from flask_admin.contrib.sqlmodel.tools import has_multiple_pks
from flask_admin.contrib.sqlmodel.tools import is_association_proxy
from flask_admin.contrib.sqlmodel.tools import is_computed_field
from flask_admin.contrib.sqlmodel.tools import is_hybrid_property
from flask_admin.contrib.sqlmodel.tools import is_relationship
from flask_admin.contrib.sqlmodel.tools import is_sqlmodel_property
from flask_admin.contrib.sqlmodel.tools import is_sqlmodel_table
from flask_admin.contrib.sqlmodel.tools import is_sqlmodel_table_model
from flask_admin.contrib.sqlmodel.tools import need_join
from flask_admin.contrib.sqlmodel.tools import SQLMODEL_AVAILABLE


# Test models for comprehensive testing
class BasicSQLModel(SQLModel, table=True):
    """Basic SQLModel with single primary key."""

    id: int = Field(primary_key=True)
    name: str
    email: Optional[str] = None


class MultiPKSQLModel(SQLModel, table=True):
    """SQLModel with multiple primary keys."""

    id1: int = Field(primary_key=True)
    id2: int = Field(primary_key=True)
    name: str


class SQLModelWithRelationship(SQLModel, table=True):
    """SQLModel with relationships."""

    id: int = Field(primary_key=True)
    name: str
    parent_id: Optional[int] = Field(foreign_key="basicSQLModel.id")


class NonTableSQLModel(SQLModel):
    """SQLModel without table=True."""

    id: int
    name: str


class SQLModelWithProperties(SQLModel, table=True):
    """SQLModel with properties and computed fields."""

    id: int = Field(primary_key=True)
    first_name: str
    last_name: str

    @property
    def full_name(self) -> str:
        """Property without setter."""
        return f"{self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        """Property with setter."""
        return getattr(self, "_display_name", self.full_name)

    @display_name.setter
    def display_name(self, value: str):
        self._display_name = value


# Traditional SQLAlchemy model for comparison
class SQLAlchemyModel:
    """Traditional SQLAlchemy model."""

    __tablename__ = "sqlalchemy_model"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))


class TestPrimaryKeyFunctions:
    """Test primary key related functions."""

    def test_get_primary_key_single_pk_sqlmodel(self) -> None:
        """Test get_primary_key with single PK SQLModel."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        pk = get_primary_key(BasicSQLModel)
        assert pk == "id"

    def test_get_primary_key_multi_pk_sqlmodel(self) -> None:
        """Test get_primary_key with multiple PK SQLModel."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        pk = get_primary_key(MultiPKSQLModel)
        assert pk == ("id1", "id2")

    def test_get_primary_key_sqlalchemy_model(self) -> None:
        """Test get_primary_key with SQLAlchemy model."""
        # Mock SQLAlchemy model with _sa_class_manager
        mock_model: Mock = Mock()
        mock_mapper: Mock = Mock()
        mock_prop = Mock()
        mock_prop.key = "id"
        mock_column = Mock()
        mock_mapper.get_property_by_column.return_value = mock_prop
        mock_mapper.primary_key = [mock_column]
        mock_model._sa_class_manager.mapper = mock_mapper

        pk = get_primary_key(mock_model)
        assert pk == "id"

    def test_get_primary_key_with_inspection(self) -> None:
        """Test get_primary_key using SQLAlchemy inspection."""
        with patch("flask_admin.contrib.sqlmodel.tools.inspect") as mock_inspect:
            mock_mapper = Mock()
            mock_prop = Mock()
            mock_prop.key = "test_id"
            mock_column = Mock()
            mock_mapper.get_property_by_column.return_value = mock_prop
            mock_mapper.primary_key = [mock_column]
            mock_inspect.return_value = mock_mapper

            mock_model = Mock()
            # No _sa_class_manager to trigger inspection path
            del mock_model._sa_class_manager

            pk = get_primary_key(mock_model)
            assert pk == "test_id"

    def test_get_primary_key_no_pk(self) -> None:
        """Test get_primary_key with no primary key."""
        mock_model = Mock()
        mock_mapper = Mock()
        mock_mapper.primary_key = []
        mock_model._sa_class_manager.mapper = mock_mapper

        pk = get_primary_key(mock_model)
        assert pk is None

    def test_has_multiple_pks_sqlmodel_single(self) -> None:
        """Test has_multiple_pks with single PK SQLModel."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        result = has_multiple_pks(BasicSQLModel)
        assert result is False

    def test_has_multiple_pks_sqlmodel_multi(self) -> None:
        """Test has_multiple_pks with multiple PK SQLModel."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        result = has_multiple_pks(MultiPKSQLModel)
        assert result is True

    def test_has_multiple_pks_sqlalchemy_model(self) -> None:
        """Test has_multiple_pks with SQLAlchemy model."""
        mock_model = Mock()
        mock_mapper = Mock()
        mock_mapper.primary_key = [Mock(), Mock()]  # Two PKs
        mock_model._sa_class_manager.mapper = mock_mapper

        result = has_multiple_pks(mock_model)
        assert result is True

    def test_has_multiple_pks_with_inspection(self) -> None:
        """Test has_multiple_pks using SQLAlchemy inspection."""
        with patch("flask_admin.contrib.sqlmodel.tools.inspect") as mock_inspect:
            mock_mapper = Mock()
            mock_mapper.primary_key = [Mock()]  # Single PK
            mock_inspect.return_value = mock_mapper

            mock_model = Mock()
            del mock_model._sa_class_manager

            result = has_multiple_pks(mock_model)
            assert result is False


class TestModelTableFunctions:
    """Test model table related functions."""

    def test_get_model_table_sqlmodel_with_table(self) -> None:
        """Test get_model_table with SQLModel table=True."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        table: Optional[Table] = get_model_table(BasicSQLModel)
        assert table is not None
        assert hasattr(table, "columns")

    def test_get_model_table_sqlmodel_without_table(self) -> None:
        """Test get_model_table with SQLModel without table."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        table: Optional[Table] = get_model_table(NonTableSQLModel)
        assert table is None

    def test_get_model_table_sqlalchemy_model(self) -> None:
        """Test get_model_table with SQLAlchemy model."""
        mock_model: Mock = Mock()
        mock_table: Mock = Mock()
        mock_model.__table__ = mock_table

        table: Optional[Table] = get_model_table(mock_model)
        assert table == mock_table

    def test_get_model_table_no_table_attr(self) -> None:
        """Test get_model_table with no __table__ attribute."""
        mock_model: Mock = Mock()
        del mock_model.__table__

        table: Optional[Any] = get_model_table(mock_model)
        assert table is None

    def test_is_sqlmodel_table_model_true(self) -> None:
        """Test is_sqlmodel_table_model with table model."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        result: bool = is_sqlmodel_table_model(BasicSQLModel)
        assert result is True

    def test_is_sqlmodel_table_model_false(self) -> None:
        """Test is_sqlmodel_table_model with non-table model."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        result: bool = is_sqlmodel_table_model(NonTableSQLModel)
        assert result is False

    def test_is_sqlmodel_table_alias(self) -> None:
        """Test is_sqlmodel_table alias function."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        result: bool = is_sqlmodel_table(BasicSQLModel)
        assert result is True

    def test_get_sqlmodel_column_names(self) -> None:
        """Test get_sqlmodel_column_names."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        columns: list[str] = get_sqlmodel_column_names(BasicSQLModel)
        assert "id" in columns
        assert "name" in columns
        assert "email" in columns

    def test_get_sqlmodel_column_names_non_table_error(self) -> None:
        """Test get_sqlmodel_column_names with non-table model."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        with pytest.raises(TypeError, match="must be a SQLModel table"):
            get_sqlmodel_column_names(NonTableSQLModel)

    def test_get_sqlmodel_field_names(self) -> None:
        """Test get_sqlmodel_field_names."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        fields: list[str] = get_sqlmodel_field_names(BasicSQLModel)
        assert "id" in fields
        assert "name" in fields
        assert "email" in fields

    def test_get_sqlmodel_field_names_non_sqlmodel_error(self) -> None:
        """Test get_sqlmodel_field_names with non-SQLModel."""
        with pytest.raises(TypeError, match="must be a SQLModel class"):
            get_sqlmodel_field_names(str)

    def test_get_sqlmodel_fields(self) -> None:
        """Test get_sqlmodel_fields."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        fields: dict[str, Any] = get_sqlmodel_fields(BasicSQLModel)
        assert "id" in fields
        assert "name" in fields
        assert "email" in fields

    def test_get_sqlmodel_fields_non_sqlmodel_error(self) -> None:
        """Test get_sqlmodel_fields with non-SQLModel."""
        with pytest.raises(TypeError, match="must be a SQLModel class"):
            get_sqlmodel_fields(str)

    def test_get_sqlmodel_fields_no_sqlmodel_available(self) -> None:
        """Test get_sqlmodel_fields when SQLModel not available."""
        with patch("flask_admin.contrib.sqlmodel.tools.SQLMODEL_AVAILABLE", False):
            with pytest.raises(ImportError, match="SQLModel is not available"):
                get_sqlmodel_fields(BasicSQLModel)

    def test_get_all_model_fields_sqlmodel(self) -> None:
        """Test get_all_model_fields with SQLModel."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        fields: dict[str, Any] = get_all_model_fields(BasicSQLModel)
        assert "id" in fields
        assert "name" in fields

    def test_get_all_model_fields_sqlalchemy(self) -> None:
        """Test get_all_model_fields with SQLAlchemy model."""
        with patch("flask_admin.contrib.sqlmodel.tools.inspect") as mock_inspect:
            mock_mapper = Mock()
            mock_prop = Mock()
            mock_prop.key = "test_field"
            mock_prop.columns = [Mock()]  # Has columns attribute
            mock_mapper.iterate_properties.return_value = [mock_prop]
            mock_inspect.return_value = mock_mapper

            mock_model = Mock()
            fields: dict[str, Any] = get_all_model_fields(mock_model)

            assert "test_field" in fields
            assert fields["test_field"] == mock_prop


class TestRelationshipFunctions:
    """Test relationship related functions."""

    def test_is_relationship_true(self) -> None:
        """Test is_relationship with actual relationship."""
        mock_attr: Mock = Mock()
        mock_attr.property.direction = "ONETOMANY"

        result: bool = is_relationship(mock_attr)
        assert result is True

    def test_is_relationship_false(self) -> None:
        """Test is_relationship with non-relationship."""
        mock_attr: Mock = Mock()
        del mock_attr.property

        result: bool = is_relationship(mock_attr)
        assert result is False

    def test_is_association_proxy_true(self) -> None:
        """Test is_association_proxy with association proxy."""
        from flask_admin.contrib.sqlmodel.tools import ASSOCIATION_PROXY

        # Create a mock that doesn't have a parent attribute
        mock_attr: Mock = Mock(spec_set=["extension_type"])
        mock_attr.extension_type = ASSOCIATION_PROXY

        result: bool = is_association_proxy(mock_attr)
        assert result is True

    def test_is_association_proxy_with_parent(self) -> None:
        """Test is_association_proxy with parent attribute."""
        from flask_admin.contrib.sqlmodel.tools import ASSOCIATION_PROXY

        mock_attr = Mock()
        mock_parent = Mock()
        mock_parent.extension_type = ASSOCIATION_PROXY
        mock_attr.parent = mock_parent
        del mock_attr.extension_type

        result: bool = is_association_proxy(mock_attr)
        assert result is True

    def test_is_association_proxy_false(self) -> None:
        """Test is_association_proxy with regular attribute."""
        mock_attr = Mock()
        del mock_attr.extension_type
        del mock_attr.parent

        result: bool = is_association_proxy(mock_attr)
        assert result is False

    def test_need_join_sqlmodel_true(self) -> None:
        """Test need_join with SQLModel requiring join."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        with patch("flask_admin.contrib.sqlmodel.tools.inspect") as mock_inspect:
            mock_mapper = Mock()
            mock_table = Mock()
            mock_mapper.tables = [Mock()]  # Different table
            mock_inspect.return_value = mock_mapper

            result: bool = need_join(BasicSQLModel, mock_table)
            assert result is True

    def test_need_join_sqlmodel_false(self) -> None:
        """Test need_join with SQLModel not requiring join."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        with patch("flask_admin.contrib.sqlmodel.tools.inspect") as mock_inspect:
            mock_mapper = Mock()
            mock_table = Mock()
            mock_mapper.tables = [mock_table]  # Same table
            mock_inspect.return_value = mock_mapper

            result: bool = need_join(BasicSQLModel, mock_table)
            assert result is False

    def test_need_join_sqlalchemy_model(self) -> None:
        """Test need_join with SQLAlchemy model."""
        mock_model = Mock()
        mock_mapper = Mock()
        mock_table = Mock()
        mock_mapper.tables = [mock_table]
        mock_model._sa_class_manager.mapper = mock_mapper

        result: bool = need_join(mock_model, mock_table)
        assert result is False

    def test_need_join_with_inspection_fallback(self) -> None:
        """Test need_join using inspection fallback."""
        with patch("flask_admin.contrib.sqlmodel.tools.inspect") as mock_inspect:
            mock_mapper = Mock()
            mock_table = Mock()
            mock_mapper.tables = [Mock()]  # Different table
            mock_inspect.return_value = mock_mapper

            mock_model = Mock()
            del mock_model._sa_class_manager
            del mock_model.__table__

            result: bool = need_join(mock_model, mock_table)
            assert result is True


class TestComputedFieldFunctions:
    """Test computed field and property functions."""

    def test_get_computed_fields_sqlmodel(self) -> None:
        """Test get_computed_fields with SQLModel."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        # Mock model with computed fields
        mock_model = Mock()
        mock_model.model_computed_fields = {"test_field": Mock()}

        with patch(
            "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class", return_value=True
        ):
            fields: dict[str, Any] = get_computed_fields(mock_model)
            assert "test_field" in fields

    def test_get_computed_fields_with_decorated_methods(self) -> None:
        """Test get_computed_fields with @computed_field decorated methods."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        mock_model = Mock()
        mock_model.model_computed_fields = {}

        # Mock dir() to return our test method
        mock_method = Mock()
        mock_method.__pydantic_computed_field__ = Mock()

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class",
                return_value=True,
            ),
            patch("builtins.dir", return_value=["test_computed_method"]),
            patch.object(mock_model, "test_computed_method", mock_method),
        ):
            fields: dict[str, Any] = get_computed_fields(mock_model)
            assert "test_computed_method" in fields

    def test_get_computed_fields_non_sqlmodel_error(self) -> None:
        """Test get_computed_fields with non-SQLModel."""
        with pytest.raises(TypeError, match="must be a SQLModel class"):
            get_computed_fields(str)

    def test_get_sqlmodel_properties(self) -> None:
        """Test get_sqlmodel_properties."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        mock_model: Mock = Mock()
        mock_property: property = property(lambda self: "test")

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class",
                return_value=True,
            ),
            patch("builtins.dir", return_value=["test_prop"]),
            patch.object(mock_model, "test_prop", mock_property),
        ):
            props: dict[str, Any] = get_sqlmodel_properties(mock_model)
            assert "test_prop" in props

    def test_get_sqlmodel_properties_non_sqlmodel_error(self) -> None:
        """Test get_sqlmodel_properties with non-SQLModel."""
        with pytest.raises(TypeError, match="must be a SQLModel class"):
            get_sqlmodel_properties(str)

    def test_is_computed_field_true(self) -> None:
        """Test is_computed_field with computed field."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        mock_model = Mock()

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_computed_fields",
                return_value={"test_field": Mock()},
            ),
        ):
            result: bool = is_computed_field(mock_model, "test_field")
            assert result is True

    def test_is_computed_field_false(self) -> None:
        """Test is_computed_field with non-computed field."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        mock_model = Mock()

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_computed_fields",
                return_value={},
            ),
        ):
            result: bool = is_computed_field(mock_model, "test_field")
            assert result is False

    def test_is_computed_field_non_sqlmodel(self) -> None:
        """Test is_computed_field with non-SQLModel."""
        result: bool = is_computed_field(str, "test_field")
        assert result is False

    def test_is_sqlmodel_property_true(self) -> None:
        """Test is_sqlmodel_property with property."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        mock_model = Mock()

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_sqlmodel_properties",
                return_value={"test_prop": property(lambda self: "test")},
            ),
        ):
            result: bool = is_sqlmodel_property(mock_model, "test_prop")
            assert result is True

    def test_is_sqlmodel_property_false(self) -> None:
        """Test is_sqlmodel_property with non-property."""
        if not SQLMODEL_AVAILABLE:
            pytest.skip("SQLModel not available")

        mock_model = Mock()

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_sqlmodel_properties",
                return_value={},
            ),
        ):
            result: bool = is_sqlmodel_property(mock_model, "test_prop")
            assert result is False

    def test_is_sqlmodel_property_non_sqlmodel(self) -> None:
        """Test is_sqlmodel_property with non-SQLModel."""
        result: bool = is_sqlmodel_property(str, "test_prop")
        assert result is False

    def test_get_hybrid_properties(self) -> None:
        """Test get_hybrid_properties."""
        with patch("flask_admin.contrib.sqlmodel.tools.inspect") as mock_inspect:
            from sqlalchemy.ext.hybrid import hybrid_property

            mock_hybrid: Any = hybrid_property(lambda self: "test")
            mock_regular = Mock()

            mock_descriptor_dict = {
                "hybrid_prop": mock_hybrid,
                "regular_prop": mock_regular,
            }

            mock_mapper = Mock()
            mock_mapper.all_orm_descriptors = mock_descriptor_dict
            mock_inspect.return_value = mock_mapper

            mock_model = Mock()
            result: dict[str, Any] = get_hybrid_properties(mock_model)

            assert "hybrid_prop" in result
            assert "regular_prop" not in result

    def test_is_hybrid_property_true(self) -> None:
        """Test is_hybrid_property with hybrid property."""
        mock_model = Mock()

        with patch(
            "flask_admin.contrib.sqlmodel.tools.get_hybrid_properties",
            return_value={"test_hybrid": Mock()},
        ):
            result: bool = is_hybrid_property(mock_model, "test_hybrid")
            assert result is True

    def test_is_hybrid_property_false(self) -> None:
        """Test is_hybrid_property with non-hybrid property."""
        mock_model = Mock()

        with patch(
            "flask_admin.contrib.sqlmodel.tools.get_hybrid_properties", return_value={}
        ):
            result: bool = is_hybrid_property(mock_model, "test_field")
            assert result is False


class TestQueryFunctions:
    """Test query related functions."""

    def test_get_query_for_ids_single_pk(self) -> None:
        """Test get_query_for_ids with single primary key."""
        mock_query: Mock = Mock()
        mock_model: Mock = Mock()
        mock_model_pk = Mock()
        mock_model.test_id = mock_model_pk

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.has_multiple_pks",
                return_value=False,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_primary_key",
                return_value="test_id",
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_primary_key_types",
                return_value={"test_id": int},
            ),
        ):
            _result: Any = get_query_for_ids(mock_query, mock_model, [1, 2, 3])

            mock_query.filter.assert_called_once()
            mock_model_pk.in_.assert_called_once_with([1, 2, 3])

    def test_get_query_for_ids_multi_pk_with_tuple_support(self) -> None:
        """Test get_query_for_ids with multiple PKs and tuple support."""

        mock_query = Mock()
        mock_model = Mock()
        mock_pk1 = Mock()
        mock_pk2 = Mock()
        mock_model.id1 = mock_pk1
        mock_model.id2 = mock_pk2

        # Mock successful query execution
        mock_filtered_query = Mock()
        mock_filtered_query.all.return_value = []
        mock_query.filter.return_value = mock_filtered_query

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.has_multiple_pks", return_value=True
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_primary_key",
                return_value=("id1", "id2"),
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_primary_key_types",
                return_value={"id1": int, "id2": int},
            ),
            patch("flask_admin.contrib.sqlmodel.tools.tuple_") as mock_tuple,
            patch(
                "flask_admin.contrib.sqlmodel.tools.iterdecode", side_effect=lambda x: x
            ),
        ):
            mock_tuple.return_value.in_.return_value = "tuple_filter"

            _result: Any = get_query_for_ids(mock_query, mock_model, [(1, 2), (3, 4)])

            mock_tuple.assert_called_once()
            mock_query.filter.assert_called_once()

    def test_get_query_for_ids_multi_pk_tuple_fallback(self) -> None:
        """Test get_query_for_ids with multiple PKs
        falling back to tuple_operator_in."""
        from sqlalchemy.exc import DBAPIError

        mock_query = Mock()
        mock_model = Mock()
        mock_pk1 = Mock()
        mock_pk2 = Mock()
        mock_model.id1 = mock_pk1
        mock_model.id2 = mock_pk2

        # Mock query that raises DBAPIError on execution
        mock_filtered_query = Mock()
        mock_filtered_query.all.side_effect = DBAPIError("statement", "params", "orig")
        mock_query.filter.return_value = mock_filtered_query

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.has_multiple_pks", return_value=True
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_primary_key",
                return_value=("id1", "id2"),
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_primary_key_types",
                return_value={"id1": int, "id2": int},
            ),
            patch("flask_admin.contrib.sqlmodel.tools.tuple_") as mock_tuple,
            patch(
                "flask_admin.contrib.sqlmodel.tools.tuple_operator_in"
            ) as mock_tuple_op,
            patch(
                "flask_admin.contrib.sqlmodel.tools.iterdecode", side_effect=lambda x: x
            ),
        ):
            mock_tuple.return_value.in_.return_value = "tuple_filter"
            mock_tuple_op.return_value = "fallback_filter"

            _result: Any = get_query_for_ids(mock_query, mock_model, [(1, 2), (3, 4)])

            # Should call tuple_operator_in as fallback
            mock_tuple_op.assert_called_once()

    def test_get_query_for_ids_multi_pk_single_pk_name(self) -> None:
        """Test get_query_for_ids with multiple PKs but single name returned."""
        mock_query = Mock()
        mock_model = Mock()
        mock_pk = Mock()
        mock_model.composite_id = mock_pk

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.has_multiple_pks", return_value=True
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_primary_key",
                return_value="composite_id",
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_primary_key_types",
                return_value={"composite_id": int},
            ),
            patch("flask_admin.contrib.sqlmodel.tools.tuple_") as mock_tuple,
            patch(
                "flask_admin.contrib.sqlmodel.tools.iterdecode", side_effect=lambda x: x
            ),
        ):
            mock_tuple.return_value.in_.return_value = "tuple_filter"
            mock_filtered_query = Mock()
            mock_filtered_query.all.return_value = []
            mock_query.filter.return_value = mock_filtered_query

            _result: Any = get_query_for_ids(mock_query, mock_model, [(1,), (2,)])

            mock_query.filter.assert_called_once()


class TestFieldPathFunctions:
    """Test field path and join related functions."""

    def test_get_field_with_path_string_simple(self) -> None:
        """Test get_field_with_path with simple string field."""
        mock_model = Mock()
        mock_attr = Mock()
        mock_model.test_field = mock_attr

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_association_proxy",
                return_value=False,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_relationship", return_value=False
            ),
        ):
            attr, path = get_field_with_path(mock_model, "test_field")

            assert attr == mock_attr
            assert path == []

    def test_get_field_with_path_string_with_relationship(self) -> None:
        """Test get_field_with_path with relationship in path."""
        mock_model = Mock()
        mock_relation = Mock()
        mock_relation.property.mapper.class_ = Mock()
        mock_relation.property.mapper.class_.__table__ = Mock()
        mock_model.relation = mock_relation

        mock_target_attr = Mock()
        mock_relation.property.mapper.class_.target_field = mock_target_attr

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_association_proxy",
                return_value=False,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_relationship",
                side_effect=lambda x: x == mock_relation,
            ),
            patch("flask_admin.contrib.sqlmodel.tools.need_join", return_value=True),
        ):
            attr, path = get_field_with_path(mock_model, "relation.target_field")

            assert attr == mock_target_attr
            assert len(path) == 1
            assert path[0] == mock_relation

    def test_get_field_with_path_association_proxy(self) -> None:
        """Test get_field_with_path with association proxy."""
        mock_model = Mock()
        mock_proxy = Mock()
        mock_proxy.attr = [Mock()]
        mock_proxy.remote_attr = Mock()
        mock_model.proxy_field = mock_proxy

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_association_proxy",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_relationship", return_value=False
            ),
        ):
            attr, path = get_field_with_path(
                mock_model, "proxy_field", return_remote_proxy_attr=True
            )

            assert attr == mock_proxy.remote_attr

    def test_get_field_with_path_non_string_attribute(self) -> None:
        """Test get_field_with_path with non-string attribute."""

        mock_attr = Mock(spec=InstrumentedAttribute)
        mock_column = Mock()
        mock_column.table = Mock()

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_columns_for_field",
                return_value=[mock_column],
            ),
            patch("flask_admin.contrib.sqlmodel.tools.need_join", return_value=True),
        ):
            attr, path = get_field_with_path(Mock(), mock_attr)

            assert attr == mock_attr
            assert len(path) == 1
            assert path[0] == mock_column.table

    def test_get_field_with_path_multiple_columns_error(self) -> None:
        """Test get_field_with_path with multiple columns raises error."""

        mock_attr = Mock(spec=InstrumentedAttribute)

        with patch(
            "flask_admin.contrib.sqlmodel.tools.get_columns_for_field",
            return_value=[Mock(), Mock()],
        ):
            with pytest.raises(Exception, match="Can only handle one column"):
                get_field_with_path(Mock(), mock_attr)


class TestFilterForeignColumns:
    """Test filter_foreign_columns function."""

    def test_filter_foreign_columns_matching(self) -> None:
        """Test filter_foreign_columns with matching table."""
        mock_table = Mock()
        mock_column1 = Mock()
        mock_column1.table = mock_table
        mock_column2 = Mock()
        mock_column2.table = Mock()  # Different table

        columns: list[Any] = [mock_column1, mock_column2]
        result: list[Any] = filter_foreign_columns(mock_table, columns)

        assert len(result) == 1
        assert result[0] == mock_column1

    def test_filter_foreign_columns_empty(self) -> None:
        """Test filter_foreign_columns with no matching columns."""
        mock_table = Mock()
        mock_column = Mock()
        mock_column.table = Mock()  # Different table

        columns: list[Any] = [mock_column]
        result: list[Any] = filter_foreign_columns(mock_table, columns)

        assert len(result) == 0


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""

    def test_get_columns_for_field_invalid_field(self) -> None:
        """Test get_columns_for_field with invalid field."""
        from flask_admin.contrib.sqlmodel.tools import get_columns_for_field

        # Test with None
        with pytest.raises(Exception, match="Invalid field"):
            get_columns_for_field(None)

        # Test with field without property
        mock_field = Mock()
        del mock_field.property
        with pytest.raises(Exception, match="Invalid field"):
            get_columns_for_field(mock_field)

        # Test with field without columns
        mock_field = Mock()
        mock_field.property.columns = []
        with pytest.raises(Exception, match="Invalid field"):
            get_columns_for_field(mock_field)

    def test_complex_path_resolution(self) -> None:
        """Test complex path resolution with nested relationships."""
        # Test the complex path resolution in is_hybrid_property and is_computed_field
        mock_model = Mock()
        mock_attr = Mock()
        mock_attr.property.argument = "TargetModel"
        mock_attr.remote_attr = Mock()
        mock_model.relation = mock_attr

        # Mock _clsregistry_resolve_name
        mock_resolver = Mock()
        mock_resolver.return_value = Mock()
        mock_attr.property._clsregistry_resolve_name = mock_resolver

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_association_proxy",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_computed_fields",
                return_value={"target_field": Mock()},
            ),
        ):
            _result: bool = is_computed_field(mock_model, "relation.target_field")
            # This tests the complex path resolution logic

    def test_class_resolver_handling(self) -> None:
        """Test handling of _class_resolver in path resolution."""
        from sqlalchemy.orm.clsregistry import _class_resolver

        mock_model = Mock()
        mock_model._decl_class_registry = {"TestModel": Mock()}

        mock_attr = Mock()
        mock_resolver = _class_resolver("TestModel", None, None, None)
        mock_attr.property.argument = mock_resolver
        mock_model.relation = mock_attr

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_association_proxy",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_computed_fields",
                return_value={},
            ),
        ):
            _result: bool = is_computed_field(mock_model, "relation.target_field")
            # This tests the _class_resolver handling

    def test_function_type_handling(self) -> None:
        """Test handling of function types in path resolution."""
        mock_model = Mock()
        mock_attr = Mock()

        def mock_function():
            return Mock()

        mock_attr.property.argument = mock_function
        mock_model.relation = mock_attr

        with (
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_sqlmodel_class",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.is_association_proxy",
                return_value=True,
            ),
            patch(
                "flask_admin.contrib.sqlmodel.tools.get_computed_fields",
                return_value={},
            ),
        ):
            _result: bool = is_computed_field(mock_model, "relation.target_field")
            # This tests the function type handling
