"""
Simple tests for SQLModel AJAX module to improve coverage.
"""

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel

from flask_admin.contrib.sqlmodel.ajax import create_ajax_loader
from flask_admin.contrib.sqlmodel.ajax import QueryAjaxModelLoader


# Simple test model
class SimpleUser(SQLModel, table=True):
    __tablename__ = "simple_user"  # type: ignore # Explicit table name

    id: int = Field(primary_key=True)
    name: str
    email: str


class TestQueryAjaxModelLoaderSimple:
    """Test QueryAjaxModelLoader class with simple cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.mock_session.query.return_value = Mock()
        self.mock_session.scalar.return_value = None
        self.mock_session.scalars.return_value.all.return_value = []
        self.mock_session.no_autoflush = Mock()
        self.mock_session.no_autoflush.__enter__ = Mock(return_value=self.mock_session)
        self.mock_session.no_autoflush.__exit__ = Mock(return_value=False)

    def test_init_basic(self):
        """Test basic initialization."""
        options = {"fields": ["name"]}

        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, SimpleUser, **options
        )

        assert loader.name == "test_loader"
        assert loader.session == self.mock_session
        assert loader.model == SimpleUser
        assert loader.fields == ["name"]

    def test_init_without_fields_raises_error(self):
        """Test initialization without fields raises ValueError."""
        with pytest.raises(
            ValueError, match="AJAX loading requires `fields` to be specified"
        ):
            QueryAjaxModelLoader("test_loader", self.mock_session, SimpleUser)

    def test_format_with_model(self):
        """Test format method with model instance."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, SimpleUser, **options
        )

        user = SimpleUser(id=1, name="Test User", email="test@example.com")

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
            "test_loader", self.mock_session, SimpleUser, **options
        )

        result = loader.format(None)
        assert result is None

    def test_get_query(self):
        """Test get_query method."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, SimpleUser, **options
        )

        result = loader.get_query()

        self.mock_session.query.assert_called_once_with(SimpleUser)
        assert result == self.mock_session.query.return_value

    def test_get_one(self):
        """Test get_one method."""
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, SimpleUser, **options
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
        options = {"fields": ["name"]}
        loader = QueryAjaxModelLoader(
            "test_loader", self.mock_session, SimpleUser, **options
        )

        with (
            patch("flask_admin.contrib.sqlmodel.ajax.select") as mock_select,
            patch("flask_admin.contrib.sqlmodel.ajax.cast") as mock_cast,
            patch("flask_admin.contrib.sqlmodel.ajax.or_") as mock_or,
        ):
            mock_stmt = Mock()
            mock_filtered_stmt = Mock()
            mock_limited_stmt = Mock()

            mock_select.return_value = mock_stmt
            mock_stmt.filter.return_value = mock_filtered_stmt
            mock_filtered_stmt.offset.return_value.limit.return_value = (
                mock_limited_stmt
            )

            # Mock cast and or_ for filter generation
            mock_cast.return_value.ilike.return_value = "filter_condition"
            mock_or.return_value = "combined_filters"

            _result = loader.get_list("search_term")

            # Verify the select statement was created
            mock_select.assert_called_once_with(SimpleUser)

            # Verify filter was applied
            mock_stmt.filter.assert_called_once()

            # Verify session.scalars was called
            self.mock_session.scalars.assert_called_once()


class TestCreateAjaxLoaderSimple:
    """Test create_ajax_loader function with simple cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)

    def test_create_ajax_loader_field_not_exists(self):
        """Test create_ajax_loader with non-existent field."""
        options = {"fields": ["title"]}

        with pytest.raises(
            ValueError, match="Model .* does not have field nonexistent"
        ):
            create_ajax_loader(
                SimpleUser, self.mock_session, "test_loader", "nonexistent", options
            )

    def test_create_ajax_loader_not_relationship(self):
        """Test create_ajax_loader with non-relationship field."""
        options = {"fields": ["title"]}

        with patch("flask_admin.contrib.sqlmodel.ajax.is_relationship") as mock_is_rel:
            mock_is_rel.return_value = False

            with pytest.raises(
                ValueError, match=".*SimpleUser.*name is not a relation"
            ):
                create_ajax_loader(
                    SimpleUser, self.mock_session, "test_loader", "name", options
                )


class TestAjaxEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)

    def test_loader_with_none_session(self):
        """Test loader behavior with None session."""
        options = {"fields": ["name"]}

        # This should still create the loader, but operations will fail
        loader = QueryAjaxModelLoader(
            "none_session_loader", None, SimpleUser, **options
        )

        assert loader.session is None
        assert loader.model == SimpleUser

    def test_loader_with_mixed_field_types(self):
        """Test loader with mixed string and object fields."""
        mock_field_obj = Mock()
        mock_field_obj.key = "custom_field"

        options = {"fields": ["name", mock_field_obj]}

        loader = QueryAjaxModelLoader(
            "mixed_loader", self.mock_session, SimpleUser, **options
        )

        assert len(loader._cached_fields) == 2
        # First should be resolved from string, second should be the object
        assert loader._cached_fields[1] == mock_field_obj
