"""
Extended tests for SQLModel AJAX module to improve coverage.
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel

from flask_admin.contrib.sqlmodel.ajax import create_ajax_loader
from flask_admin.contrib.sqlmodel.ajax import QueryAjaxModelLoader


# Test models
class AjaxTestUser(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    email: str
    active: bool = True

    def __str__(self):
        return f"User({self.name})"


class AjaxTestPost(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    content: str
    user_id: int = Field(foreign_key="ajaxtestuser.id")

    def __str__(self):
        return f"Post({self.title})"


class AjaxTestMultiPKModel(SQLModel, table=True):
    id1: int = Field(primary_key=True)
    id2: int = Field(primary_key=True)
    name: str

    def __str__(self):
        return f"MultiPK({self.name})"


class AjaxTestSQLAlchemyModel:
    """Mock SQLAlchemy model for testing."""

    __tablename__ = "sqlalchemy_model"

    def __init__(self):
        self.id = Column(Integer, primary_key=True)
        self.name = Column(String(50))


class TestQueryAjaxModelLoader:
    """Test QueryAjaxModelLoader class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.mock_session.query.return_value = Mock()
        self.mock_session.scalar.return_value = None
        self.mock_session.scalars.return_value.all.return_value = []
        self.mock_session.no_autoflush = Mock()
        self.mock_session.no_autoflush.__enter__ = Mock(return_value=self.mock_session)
        self.mock_session.no_autoflush.__exit__ = Mock(return_value=False)

    def test_init_with_fields(self):
        """Test initialization with string fields."""
        options = {"fields": ["name", "email"]}

        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        assert loader.name == "test_loader"
        assert loader.session == self.mock_session
        assert loader.model == AjaxTestUser
        assert loader.fields == ["name", "email"]
        assert len(loader._cached_fields) == 2

    def test_init_with_direct_fields(self):
        """Test initialization with direct field objects."""
        mock_field1 = Mock()
        mock_field2 = Mock()

        options = {"fields": [mock_field1, mock_field2]}

        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        assert len(loader._cached_fields) == 2
        assert loader._cached_fields[0] == mock_field1
        assert loader._cached_fields[1] == mock_field2

    def test_init_without_fields_raises_error(self):
        """Test initialization without fields raises ValueError."""
        with pytest.raises(
            ValueError, match="AJAX loading requires `fields` to be specified"
        ):
            QueryAjaxModelLoader("test_loader", self.mock_session, AjaxTestUser)

    def test_init_with_multi_pk_model_raises_error(self):
        """Test initialization with multi-PK model raises NotImplementedError."""
        options = {"fields": ["name"]}

        with patch(
            "flask_admin.contrib.sqlmodel.ajax.has_multiple_pks"
        ) as mock_has_multi_pks:
            mock_has_multi_pks.return_value = True

            with pytest.raises(
                NotImplementedError,
                match="Flask-Admin does not support multi-pk AJAX model loading",
            ):
                QueryAjaxModelLoader(
                    "test_loader", self.mock_session, AjaxTestMultiPKModel, **options
                )

    def test_init_with_order_by_and_filters(self):
        """Test initialization with order_by and filters options."""
        options = {"fields": ["name"], "order_by": "name", "filters": ["active = true"]}

        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        assert loader.order_by == "name"
        assert loader.filters == ["active = true"]

    def test_process_fields_with_string_names(self):
        """Test _process_fields with string field names."""
        options = {"fields": ["name", "email"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        fields = loader._process_fields()

        assert len(fields) == 2
        # Fields should be resolved to actual model attributes
        assert all(hasattr(field, "key") or hasattr(field, "name") for field in fields)

    def test_process_fields_with_nonexistent_field(self):
        """Test _process_fields with nonexistent field raises ValueError."""
        options = {"fields": ["nonexistent_field"]}

        with pytest.raises(
            ValueError, match=".*AjaxTestUser.*nonexistent_field does not exist"
        ):
            QueryAjaxModelLoader(
                "test_loader", self.mock_session, AjaxTestUser, **options
            )

    def test_format_with_model(self):
        """Test format method with model instance."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        user = AjaxTestUser(id=1, name="Test User", email="test@example.com")

        with patch("flask_admin.contrib.sqlmodel.ajax.get_primary_key") as mock_get_pk:
            mock_get_pk.return_value = "id"

            result = loader.format(user)

            assert result is not None
            assert result[0] == 1  # PK value
            assert "Test User" in str(result[1])  # String representation

    def test_format_with_none(self):
        """Test format method with None."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        result = loader.format(None)
        assert result is None

    def test_get_query(self):
        """Test get_query method."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        result = loader.get_query()

        self.mock_session.query.assert_called_once_with(AjaxTestUser)
        assert result == self.mock_session.query.return_value

    def test_get_one(self):
        """Test get_one method."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        with patch("flask_admin.contrib.sqlmodel.ajax.select") as mock_select:
            mock_stmt = Mock()
            mock_select.return_value.where.return_value = mock_stmt

            with patch(
                "flask_admin.contrib.sqlmodel.ajax.get_primary_key"
            ) as mock_get_pk:
                mock_get_pk.return_value = "id"

                _result = loader.get_one(123)

                # Check that session.scalar was called with the statement
                self.mock_session.scalar.assert_called_once_with(mock_stmt)

                # Check that no_autoflush context manager was used
                self.mock_session.no_autoflush.__enter__.assert_called_once()

    def test_get_list_basic(self):
        """Test get_list method with basic parameters."""
        options = {"fields": ["name", "email"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        # Mock the select and filter chain
        mock_stmt = Mock()
        mock_filtered_stmt = Mock()
        mock_limited_stmt = Mock()

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.select") as mock_select,
            patch("flask_admin.contrib.sqlmodel.ajax.cast") as mock_cast,
            patch("flask_admin.contrib.sqlmodel.ajax.or_") as mock_or,
        ):
            mock_select.return_value = mock_stmt
            mock_stmt.filter.return_value = mock_filtered_stmt
            mock_filtered_stmt.offset.return_value.limit.return_value = (
                mock_limited_stmt
            )

            # Mock cast and or_ for filter generation
            mock_cast.return_value.ilike.return_value = "filter_condition"
            mock_or.return_value = "combined_filters"

            _result = loader.get_list("search_term", offset=10, limit=20)

            # Verify the select statement was created
            mock_select.assert_called_once_with(AjaxTestUser)

            # Verify filter was applied
            mock_stmt.filter.assert_called_once()

            # Verify pagination
            mock_filtered_stmt.offset.assert_called_once_with(10)

            # Verify session.scalars was called
            self.mock_session.scalars.assert_called_once()

    def test_get_list_with_filters(self):
        """Test get_list method with additional filters."""
        options = {"fields": ["name"], "filters": ["active = true", "role = 'user'"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        mock_stmt = Mock()
        mock_filtered_stmt = Mock()
        mock_filtered_again_stmt = Mock()
        mock_limited_stmt = Mock()

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.select") as mock_select,
            patch("flask_admin.contrib.sqlmodel.ajax.cast") as mock_cast,
            patch("flask_admin.contrib.sqlmodel.ajax.or_") as mock_or,
            patch("flask_admin.contrib.sqlmodel.ajax.and_") as mock_and,
            patch("flask_admin.contrib.sqlmodel.ajax.text") as mock_text,
        ):
            mock_select.return_value = mock_stmt
            mock_stmt.filter.return_value = mock_filtered_stmt
            mock_filtered_stmt.filter.return_value = mock_filtered_again_stmt
            mock_filtered_again_stmt.offset.return_value.limit.return_value = (
                mock_limited_stmt
            )

            # Mock the filter generation
            mock_cast.return_value.ilike.return_value = "search_filter"
            mock_or.return_value = "search_filters"
            mock_text.side_effect = lambda x: f"text({x})"
            mock_and.return_value = "additional_filters"

            _result = loader.get_list("search", offset=0, limit=10)

            # Verify additional filters were applied
            assert mock_text.call_count == 2  # Two filters
            mock_and.assert_called_once()

    def test_get_list_with_order_by(self):
        """Test get_list method with order_by option."""
        options = {"fields": ["name"], "order_by": "name"}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        mock_stmt = Mock()
        mock_filtered_stmt = Mock()
        mock_ordered_stmt = Mock()
        mock_limited_stmt = Mock()

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.select") as mock_select,
            patch("flask_admin.contrib.sqlmodel.ajax.cast") as mock_cast,
            patch("flask_admin.contrib.sqlmodel.ajax.or_") as mock_or,
        ):
            mock_select.return_value = mock_stmt
            mock_stmt.filter.return_value = mock_filtered_stmt
            mock_filtered_stmt.order_by.return_value = mock_ordered_stmt
            mock_ordered_stmt.offset.return_value.limit.return_value = mock_limited_stmt

            mock_cast.return_value.ilike.return_value = "filter_condition"
            mock_or.return_value = "combined_filters"

            _result = loader.get_list("search")

            # Verify order_by was called
            mock_filtered_stmt.order_by.assert_called_once_with("name")

    def test_get_list_default_pagination(self):
        """Test get_list method with default pagination."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, AjaxTestUser, **options
        )

        mock_stmt = Mock()
        mock_filtered_stmt = Mock()
        mock_limited_stmt = Mock()

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.select") as mock_select,
            patch("flask_admin.contrib.sqlmodel.ajax.cast") as mock_cast,
            patch("flask_admin.contrib.sqlmodel.ajax.or_") as mock_or,
        ):
            mock_select.return_value = mock_stmt
            mock_stmt.filter.return_value = mock_filtered_stmt
            mock_filtered_stmt.offset.return_value.limit.return_value = (
                mock_limited_stmt
            )

            mock_cast.return_value.ilike.return_value = "filter"
            mock_or.return_value = "filters"

            _result = loader.get_list("search")

            # Verify default offset and limit (DEFAULT_PAGE_SIZE is typically 20)
            mock_filtered_stmt.offset.assert_called_once_with(0)
            # Just verify limit was called, the default value may vary
            mock_filtered_stmt.offset.return_value.limit.assert_called_once()


class TestCreateAjaxLoader:
    """Test create_ajax_loader function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)

    def test_create_ajax_loader_success(self):
        """Test successful creation of AJAX loader."""
        options = {"fields": ["name"]}  # Use "name" field which exists on AjaxTestUser

        with patch("flask_admin.contrib.sqlmodel.ajax.is_relationship") as mock_is_rel:
            mock_is_rel.return_value = True

            # Mock the relationship attribute
            mock_attr = Mock()
            mock_attr.property.mapper.class_ = AjaxTestUser

            # Use patch.object to temporarily add the user attribute
            with patch.object(AjaxTestPost, "user", mock_attr, create=True):
                result = create_ajax_loader(
                    AjaxTestPost, self.mock_session, "user_loader", "user", options
                )

                assert isinstance(result, QueryAjaxModelLoader)
                assert result.name == "user_loader"
                assert result.session == self.mock_session
                assert result.model == AjaxTestUser

    def test_create_ajax_loader_field_not_exists(self):
        """Test create_ajax_loader with non-existent field."""
        options = {"fields": ["title"]}

        with pytest.raises(
            ValueError, match="Model .* does not have field nonexistent"
        ):
            create_ajax_loader(
                AjaxTestPost, self.mock_session, "test_loader", "nonexistent", options
            )

    def test_create_ajax_loader_not_relationship(self):
        """Test create_ajax_loader with non-relationship field."""
        options = {"fields": ["title"]}

        with patch("flask_admin.contrib.sqlmodel.ajax.is_relationship") as mock_is_rel:
            mock_is_rel.return_value = False

            with pytest.raises(
                ValueError, match=".*AjaxTestPost.*title is not a relation"
            ):
                create_ajax_loader(
                    AjaxTestPost, self.mock_session, "test_loader", "title", options
                )

    def test_create_ajax_loader_with_complex_relationship(self):
        """Test create_ajax_loader with complex relationship setup."""
        options = {
            "fields": ["name", "email"],
            "order_by": "name",
            "filters": ["active = true"],
        }

        with patch("flask_admin.contrib.sqlmodel.ajax.is_relationship") as mock_is_rel:
            mock_is_rel.return_value = True

            # Mock a complex relationship
            mock_attr = Mock()
            mock_mapper = Mock()
            mock_mapper.class_ = AjaxTestUser
            mock_attr.property.mapper = mock_mapper

            # Use patch.object to temporarily add the user attribute
            with patch.object(AjaxTestPost, "user", mock_attr, create=True):
                result = create_ajax_loader(
                    AjaxTestPost, self.mock_session, "complex_loader", "user", options
                )

                assert isinstance(result, QueryAjaxModelLoader)
                assert result.order_by == "name"
                assert result.filters == ["active = true"]
                assert len(result._cached_fields) == 2


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.mock_session.query.return_value = Mock()
        self.mock_session.scalar.return_value = None
        self.mock_session.scalars.return_value.all.return_value = []
        self.mock_session.no_autoflush = Mock()
        self.mock_session.no_autoflush.__enter__ = Mock(return_value=self.mock_session)
        self.mock_session.no_autoflush.__exit__ = Mock(return_value=False)

    def test_loader_with_computed_field(self):
        """Test loader with computed field in fields list."""
        # Create a mock computed field
        mock_computed_field = Mock()
        mock_computed_field.key = "computed_field"

        options = {"fields": [mock_computed_field]}

        loader = QueryAjaxModelLoader(
            "computed_loader", self.mock_session, AjaxTestUser, **options
        )

        assert len(loader._cached_fields) == 1
        assert loader._cached_fields[0] == mock_computed_field

    def test_loader_with_mixed_field_types(self):
        """Test loader with mixed string and object fields."""
        mock_field_obj = Mock()
        mock_field_obj.key = "custom_field"

        options = {"fields": ["name", mock_field_obj]}

        loader = QueryAjaxModelLoader(
            "mixed_loader", self.mock_session, AjaxTestUser, **options
        )

        assert len(loader._cached_fields) == 2
        # First should be resolved from string, second should be the object
        assert loader._cached_fields[1] == mock_field_obj

    def test_format_with_custom_pk(self):
        """Test format method with custom primary key."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "custom_pk_loader", self.mock_session, AjaxTestUser, **options
        )

        user = AjaxTestUser(id=42, name="Custom User", email="custom@example.com")

        with patch("flask_admin.contrib.sqlmodel.ajax.get_primary_key") as mock_get_pk:
            mock_get_pk.return_value = "id"

            result = loader.format(user)

            assert result[0] == 42
            assert "Custom User" in str(result[1])

    def test_get_list_with_empty_search(self):
        """Test get_list with empty search term."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "empty_search_loader", self.mock_session, AjaxTestUser, **options
        )

        mock_stmt = Mock()
        mock_filtered_stmt = Mock()
        mock_limited_stmt = Mock()

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.select") as mock_select,
            patch("flask_admin.contrib.sqlmodel.ajax.cast") as mock_cast,
            patch("flask_admin.contrib.sqlmodel.ajax.or_") as mock_or,
        ):
            mock_select.return_value = mock_stmt
            mock_stmt.filter.return_value = mock_filtered_stmt
            mock_filtered_stmt.offset.return_value.limit.return_value = (
                mock_limited_stmt
            )

            # Empty search term should still create filters
            mock_cast.return_value.ilike.return_value = "empty_filter"
            mock_or.return_value = "empty_filters"

            _result = loader.get_list("")

            # Should still apply filters even with empty term
            mock_stmt.filter.assert_called_once()

    def test_get_one_with_complex_pk(self):
        """Test get_one with complex primary key handling."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "complex_pk_loader", self.mock_session, AjaxTestUser, **options
        )

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.select") as mock_select,
            patch("flask_admin.contrib.sqlmodel.ajax.get_primary_key") as mock_get_pk,
        ):
            mock_stmt = Mock()
            mock_where_stmt = Mock()
            mock_select.return_value = mock_stmt
            mock_stmt.where.return_value = mock_where_stmt
            mock_get_pk.return_value = "custom_id"

            # Mock the model to have custom_id attribute
            mock_attr = Mock()
            with patch.object(AjaxTestUser, "custom_id", mock_attr, create=True):
                _result = loader.get_one("123")

                # Verify where clause was applied correctly
                mock_stmt.where.assert_called_once()

    def test_error_handling_in_process_fields(self):
        """Test error handling in _process_fields method."""
        # Test with a field that exists but has no attribute
        options = {"fields": ["__class__"]}  # This exists but isn't a field

        # This should work as getattr will return the class
        loader = QueryAjaxModelLoader(
            "error_loader", self.mock_session, AjaxTestUser, **options
        )
        fields = loader._process_fields()
        assert len(fields) == 1

    def test_session_scalars_integration(self):
        """Test integration with session.scalars method."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "scalars_loader", self.mock_session, AjaxTestUser, **options
        )

        # Mock return values more realistically
        mock_user1 = AjaxTestUser(id=1, name="User 1", email="user1@example.com")
        mock_user2 = AjaxTestUser(id=2, name="User 2", email="user2@example.com")

        self.mock_session.scalars.return_value.all.return_value = [
            mock_user1,
            mock_user2,
        ]

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.select"),
            patch("flask_admin.contrib.sqlmodel.ajax.cast"),
            patch("flask_admin.contrib.sqlmodel.ajax.or_"),
        ):
            result = loader.get_list("User")

            # Verify the result contains the mocked users
            assert result == [mock_user1, mock_user2]


class TestEdgeCasesAndErrorConditions:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)

    def test_loader_with_none_session(self):
        """Test loader behavior with None session."""
        options = {"fields": ["name"]}

        # This should still create the loader, but operations will fail
        loader = QueryAjaxModelLoader(
            "none_session_loader", None, AjaxTestUser, **options
        )

        assert loader.session is None
        assert loader.model == AjaxTestUser

    def test_loader_with_string_types_compatibility(self):
        """Test compatibility with string_types from _compat."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "compat_loader", self.mock_session, AjaxTestUser, **options
        )

        # Test that string field names are handled via string_types check
        fields = loader._process_fields()
        assert len(fields) >= 1

    def test_create_ajax_loader_attribute_error(self):
        """Test create_ajax_loader when getattr fails."""
        options = {"fields": ["name"]}

        # Use a model that doesn't have the requested field
        class MinimalModel(SQLModel):
            id: int = Field(primary_key=True)

        with pytest.raises(ValueError, match="does not have field"):
            create_ajax_loader(
                MinimalModel, self.mock_session, "test", "nonexistent", options
            )

    def test_loader_initialization_edge_cases(self):
        """Test loader initialization with edge case parameters."""
        # Test with empty options
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "edge_loader", self.mock_session, AjaxTestUser, **options
        )

        assert loader.order_by is None
        assert loader.filters is None

    def test_get_list_filter_generation_edge_cases(self):
        """Test get_list filter generation with edge cases."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "filter_edge_loader", self.mock_session, AjaxTestUser, **options
        )

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.select") as mock_select,
            patch("flask_admin.contrib.sqlmodel.ajax.cast") as mock_cast,
            patch("flask_admin.contrib.sqlmodel.ajax.or_") as mock_or,
        ):
            mock_stmt = Mock()
            mock_select.return_value = mock_stmt
            mock_stmt.filter.return_value = mock_stmt
            mock_stmt.offset.return_value.limit.return_value = mock_stmt

            # Test with special characters in search term
            mock_cast.return_value.ilike.return_value = "special_filter"
            mock_or.return_value = "combined_special_filters"

            _result = loader.get_list("search with spaces & symbols!")

            # Should handle special characters gracefully
            mock_or.assert_called_once()

    def test_format_with_unicode_strings(self):
        """Test format method with unicode strings."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "unicode_loader", self.mock_session, AjaxTestUser, **options
        )

        user = AjaxTestUser(id=1, name="Üñíçødé Ñämé", email="unicode@example.com")

        with patch("flask_admin.contrib.sqlmodel.ajax.get_primary_key") as mock_get_pk:
            mock_get_pk.return_value = "id"

            result = loader.format(user)

            assert result is not None
            assert result[0] == 1
            # Unicode should be preserved in string representation
            assert "Üñíçødé" in str(result[1])

    def test_mock_dependencies_integration(self):
        """Test integration with mocked dependencies."""
        options = {"fields": ["name"]}

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.get_primary_key") as mock_get_pk,
            patch(
                "flask_admin.contrib.sqlmodel.ajax.has_multiple_pks"
            ) as mock_has_multi_pks,
        ):
            mock_get_pk.return_value = "custom_pk"
            mock_has_multi_pks.return_value = False

            loader = QueryAjaxModelLoader(
                "mock_deps_loader", self.mock_session, AjaxTestUser, **options
            )

            assert loader.pk == "custom_pk"
            mock_has_multi_pks.assert_called_once_with(AjaxTestUser)
