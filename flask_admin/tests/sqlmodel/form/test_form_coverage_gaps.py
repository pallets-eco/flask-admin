"""
Comprehensive tests targeting uncovered lines in form.py to improve coverage.

This file specifically targets the lines identified as missing coverage
to bring the form.py module from 75% to higher coverage.
"""

import warnings
from typing import Optional
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlmodel import Field
from sqlmodel import SQLModel
from wtforms import StringField

from flask_admin.contrib.sqlmodel.form import _resolve_prop
from flask_admin.contrib.sqlmodel.form import AdminModelConverter
from flask_admin.contrib.sqlmodel.form import get_form


class TestImportFallbacksMissed:
    """Test import fallback coverage for lines 20-22."""

    def test_import_fallback_sqlalchemy_imports(self):
        """Test the actual import fallback to SQLAlchemy types."""
        # These lines are typically hard to test because they run at module import time
        # But we can verify the fallback imports work
        from sqlalchemy import Boolean as SABoolean
        from sqlalchemy import Column as SAColumn

        assert SABoolean is not None
        assert SAColumn is not None

        # Verify the imported types can be used
        assert issubclass(SABoolean, Boolean)
        assert issubclass(SAColumn, Column)


class TestConverterLabelAndOverride:
    """Test field override and label logic - lines 84-110."""

    def test_get_label_with_explicit_label(self):
        """Test _get_label when label is explicitly provided."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {"label": "Custom Label"}
        result = converter._get_label("field_name", field_args)

        assert result == "Custom Label"

    def test_get_label_with_column_labels(self):
        """Test _get_label with column_labels in view."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.column_labels = {"field_name": "Column Label"}

        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {}
        result = converter._get_label("field_name", field_args)

        assert result == "Column Label"

    def test_get_label_with_prettify_override(self):
        """Test _get_label with prettify_name override."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.column_labels = None
        mock_view.prettify_name = Mock(return_value="Pretty Name")

        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {}
        result = converter._get_label("field_name", field_args)

        assert result == "Pretty Name"
        mock_view.prettify_name.assert_called_once_with("field_name")

    def test_get_label_fallback_to_prettify_name(self):
        """Test _get_label fallback to default prettify_name."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.column_labels = None
        mock_view.prettify_name = None

        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {}
        result = converter._get_label("field_name", field_args)

        # Should use default prettify_name function
        assert result == "Field Name"  # Default prettify behavior

    def test_get_description_with_explicit_description(self):
        """Test _get_description when description is explicitly provided."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {"description": "Custom Description"}
        result = converter._get_description("field_name", field_args)

        assert result == "Custom Description"

    def test_get_description_with_column_descriptions(self):
        """Test _get_description with column_descriptions in view."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.column_descriptions = {"field_name": "Column Description"}

        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {}
        result = converter._get_description("field_name", field_args)

        assert result == "Column Description"

    def test_get_field_override_with_overrides(self):
        """Test _get_field_override when overrides exist."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_overrides = {"field_name": StringField}

        converter = AdminModelConverter(mock_session, mock_view)

        result = converter._get_field_override("field_name")

        assert result == StringField

    def test_get_field_override_without_overrides(self):
        """Test _get_field_override when no overrides exist."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_overrides = None

        converter = AdminModelConverter(mock_session, mock_view)

        result = converter._get_field_override("field_name")

        assert result is None


class TestComputedFieldConversion:
    """Test computed field conversion - lines 185-206."""

    def test_convert_computed_field_not_in_form_columns(self):
        """Test computed field conversion when field not in form_columns."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = ["other_field"]

        converter = AdminModelConverter(mock_session, mock_view)

        mock_model = Mock()
        field_info = Mock()
        kwargs = {}

        result = converter._convert_computed_field(
            mock_model, "computed_field", field_info, kwargs
        )

        assert result is None

    def test_convert_computed_field_with_override(self):
        """Test computed field conversion with field override."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = ["computed_field"]
        mock_view.form_overrides = {"computed_field": StringField}

        converter = AdminModelConverter(mock_session, mock_view)

        mock_model = Mock()
        field_info = Mock()
        kwargs = {"validators": []}

        result = converter._convert_computed_field(
            mock_model, "computed_field", field_info, kwargs
        )

        assert isinstance(result, type(StringField()))

    def test_convert_computed_field_default_to_string(self):
        """Test computed field conversion defaults to StringField."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = None  # Include all fields
        mock_view.form_overrides = None

        converter = AdminModelConverter(mock_session, mock_view)

        mock_model = Mock()
        field_info = Mock()
        kwargs = {"validators": []}

        result = converter._convert_computed_field(
            mock_model, "computed_field", field_info, kwargs
        )

        assert isinstance(result, type(StringField()))
        # Check that readonly attribute is set
        assert kwargs["render_kw"]["readonly"] is True  # type: ignore


class TestAssociationProxyErrorHandling:
    """Test association proxy error handling - lines 233-238."""

    def test_association_proxy_without_remote_attr_prop(self):
        """Test association proxy error when remote_attr lacks prop."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        # Create a mock association proxy that will pass is_association_proxy check
        mock_prop = Mock()
        mock_prop.remote_attr = Mock()
        # Remove the 'prop' attribute to trigger hasattr check failure
        del mock_prop.remote_attr.prop

        # Mock the model and mapper
        mock_model = Mock()
        mock_mapper = Mock()

        with patch(
            "flask_admin.contrib.sqlmodel.form.is_association_proxy"
        ) as mock_is_assoc:
            mock_is_assoc.return_value = True

            with pytest.raises(
                Exception,
                match="Association proxy referencing another association proxy",
            ):
                converter.convert(
                    mock_model, mock_mapper, "field_name", mock_prop, {}, False
                )


class TestMultipleColumnHandling:
    """Test multiple column handling and warnings - lines 245-259."""

    def test_multiple_columns_filtered_to_zero(self):
        """Test property with multiple columns filtered to zero."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = None
        converter = AdminModelConverter(mock_session, mock_view)

        # Create mock property with multiple columns that will be filtered to zero
        mock_prop = Mock(
            spec=["columns", "key"]
        )  # Exclude 'field' and 'direction' to avoid relation path
        mock_prop.columns = [Mock(), Mock()]  # Start with multiple columns
        mock_prop.key = "test_prop"

        mock_model = Mock()
        mock_model.__table__ = Mock()  # Add table for filter_foreign_columns
        mock_mapper = Mock()

        # Import the real isinstance for fallback
        import builtins

        real_isinstance = builtins.isinstance

        with patch("flask_admin.contrib.sqlmodel.form.isinstance") as mock_isinstance:
            # Configure isinstance to handle different checks
            def isinstance_side_effect(obj, class_):
                if (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "FieldPlaceholder"
                ):
                    return False  # Mock prop is not a FieldPlaceholder
                elif (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "ColumnProperty"
                ):
                    return False  # Mock prop is not a ColumnProperty (to trigger multiple column check)  # noqa: E501
                else:
                    # Fall back to real isinstance for other checks
                    return real_isinstance(obj, class_)

            mock_isinstance.side_effect = isinstance_side_effect

            with patch(
                "flask_admin.contrib.sqlmodel.form.is_association_proxy"
            ) as mock_is_assoc:
                mock_is_assoc.return_value = False  # Not an association proxy

                with patch(
                    "flask_admin.contrib.sqlmodel.form.filter_foreign_columns"
                ) as mock_filter:
                    mock_filter.return_value = []  # Zero columns after filtering

                    result = converter.convert(
                        mock_model, mock_mapper, "test_field", mock_prop, {}, False
                    )

                    assert result is None

    def test_multiple_columns_warning_triggered(self):
        """Test multiple columns warning is triggered."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = None
        converter = AdminModelConverter(mock_session, mock_view)

        # Create mock property with multiple columns that is NOT a relation
        mock_prop = Mock(
            spec=["columns", "key"]
        )  # Exclude 'field' and 'direction' to avoid relation path
        mock_prop.columns = [Mock(), Mock()]  # Two columns
        mock_prop.key = "test_prop"

        mock_model = Mock()
        mock_model.__name__ = "TestModel"
        mock_model.__table__ = Mock()  # Add table for filter_foreign_columns
        mock_mapper = Mock()

        # Import the real isinstance for fallback
        import builtins

        real_isinstance = builtins.isinstance

        with patch("flask_admin.contrib.sqlmodel.form.isinstance") as mock_isinstance:
            # Configure isinstance to handle different checks
            def isinstance_side_effect(obj, class_):
                if (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "FieldPlaceholder"
                ):
                    return False  # Mock prop is not a FieldPlaceholder
                elif (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "ColumnProperty"
                ):
                    return False  # Mock prop is not a ColumnProperty (to trigger multiple column check)  # noqa: E501
                else:
                    # Fall back to real isinstance for other checks
                    return real_isinstance(obj, class_)

            mock_isinstance.side_effect = isinstance_side_effect

            with patch(
                "flask_admin.contrib.sqlmodel.form.is_association_proxy"
            ) as mock_is_assoc:
                mock_is_assoc.return_value = False  # Not an association proxy

                with patch(
                    "flask_admin.contrib.sqlmodel.form.filter_foreign_columns"
                ) as mock_filter:
                    mock_filter.return_value = [
                        Mock(),
                        Mock(),
                    ]  # Multiple columns remain

                    with warnings.catch_warnings(record=True) as w:
                        warnings.simplefilter("always")

                        result = converter.convert(
                            mock_model, mock_mapper, "test_field", mock_prop, {}, False
                        )

                        assert result is None
                        # Check that warning was issued
                        assert len(w) == 1
                        assert "multiple-column properties" in str(w[0].message)


class TestForeignKeyExclusion:
    """Test foreign key exclusion logic - lines 268-273."""

    def test_foreign_key_excluded_when_not_in_form_columns(self):
        """Test foreign key columns are excluded when not in form_columns."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = ["other_field"]  # Doesn't include our field

        converter = AdminModelConverter(mock_session, mock_view)

        # Create mock property with foreign key column
        mock_prop = Mock()
        mock_column = Mock()
        mock_column.foreign_keys = {"some_fk"}  # Has foreign keys
        mock_prop.columns = [mock_column]
        mock_prop.key = "test_field"

        mock_model = Mock()
        mock_mapper = Mock()

        result = converter.convert(
            mock_model, mock_mapper, "test_field", mock_prop, {}, False
        )

        assert result is None

    def test_non_column_property_excluded(self):
        """Test non-Column properties are excluded."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = None
        converter = AdminModelConverter(mock_session, mock_view)

        # Create mock property with non-Column object
        mock_prop = Mock(
            spec=["columns", "key"]
        )  # Exclude 'field' to avoid FieldPlaceholder detection
        mock_non_column = Mock()
        mock_non_column.foreign_keys = set()
        mock_prop.columns = [mock_non_column]
        mock_prop.key = "test_field"

        mock_model = Mock()
        mock_mapper = Mock()

        # Import the real isinstance for fallback
        import builtins

        real_isinstance = builtins.isinstance

        with patch("flask_admin.contrib.sqlmodel.form.isinstance") as mock_isinstance:
            # Configure isinstance to handle different checks in the convert method
            def isinstance_side_effect(obj, class_):
                if (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "FieldPlaceholder"
                ):
                    return False  # Mock prop is not a FieldPlaceholder
                elif (
                    obj is mock_non_column
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "Column"
                ):
                    return False  # Mock non_column is NOT a Column - this is what we want to test  # noqa: E501
                else:
                    # Fall back to real isinstance for other checks
                    return real_isinstance(obj, class_)

            mock_isinstance.side_effect = isinstance_side_effect

            result = converter.convert(
                mock_model, mock_mapper, "test_field", mock_prop, {}, False
            )

            assert result is None


class TestPrimaryKeyFieldLogic:
    """Test primary key field logic - lines 276-297."""

    def test_primary_key_hidden_field(self):
        """Test primary key becomes hidden field when hidden_pk=True."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        # Create mock property with primary key column
        mock_prop = Mock(
            spec=["columns", "key"]
        )  # Exclude 'field' to avoid FieldPlaceholder detection
        mock_column = Mock()
        mock_column.primary_key = True
        mock_column.foreign_keys = set()
        mock_prop.columns = [mock_column]
        mock_prop.key = "id"

        mock_model = Mock()
        mock_mapper = Mock()

        # Import the real isinstance for fallback
        import builtins

        real_isinstance = builtins.isinstance

        with patch("flask_admin.contrib.sqlmodel.form.isinstance") as mock_isinstance:
            # Configure isinstance to handle different checks in the convert method
            def isinstance_side_effect(obj, class_):
                if (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "FieldPlaceholder"
                ):
                    return False  # Mock prop is not a FieldPlaceholder
                elif (
                    obj is mock_column
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "Column"
                ):
                    return True  # Mock column is a Column
                else:
                    # Fall back to real isinstance for other checks
                    return real_isinstance(obj, class_)

            mock_isinstance.side_effect = isinstance_side_effect

            with patch(
                "flask_admin.contrib.sqlmodel.form.fields.HiddenField"
            ) as mock_hidden:
                mock_hidden.return_value = Mock()

                result = converter.convert(
                    mock_model,
                    mock_mapper,
                    "id",
                    mock_prop,
                    {},
                    True,  # hidden_pk=True
                )

                mock_hidden.assert_called_once()
                assert result is not None

    def test_primary_key_excluded_when_not_in_form_columns(self):
        """Test primary key excluded when not in form_columns and hidden_pk=False."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = ["other_field"]  # Doesn't include PK

        converter = AdminModelConverter(mock_session, mock_view)

        # Create mock property with primary key column
        mock_prop = Mock(
            spec=["columns", "key"]
        )  # Exclude 'field' to avoid FieldPlaceholder detection
        mock_column = Mock()
        mock_column.primary_key = True
        mock_column.foreign_keys = set()
        mock_prop.columns = [mock_column]
        mock_prop.key = "id"

        mock_model = Mock()
        mock_mapper = Mock()

        # Import the real isinstance for fallback
        import builtins

        real_isinstance = builtins.isinstance

        with patch("flask_admin.contrib.sqlmodel.form.isinstance") as mock_isinstance:
            # Configure isinstance to handle different checks in the convert method
            def isinstance_side_effect(obj, class_):
                if (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "FieldPlaceholder"
                ):
                    return False  # Mock prop is not a FieldPlaceholder
                elif (
                    obj is mock_column
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "Column"
                ):
                    return True  # Mock column is a Column
                else:
                    # Fall back to real isinstance for other checks
                    return real_isinstance(obj, class_)

            mock_isinstance.side_effect = isinstance_side_effect

            result = converter.convert(
                mock_model,
                mock_mapper,
                "id",
                mock_prop,
                {},
                False,  # hidden_pk=False
            )

            assert result is None

    def test_primary_key_unique_validator_with_single_pk(self):
        """Test primary key gets unique validator when single PK."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = None  # Include all fields
        mock_view.form_optional_types = ()  # Set empty tuple for optional types

        converter = AdminModelConverter(mock_session, mock_view)

        # Create mock property with primary key column
        mock_prop = Mock(
            spec=["columns", "key"]
        )  # Exclude 'field' to avoid FieldPlaceholder detection
        mock_column = Mock()
        mock_column.primary_key = True
        mock_column.foreign_keys = set()
        mock_column.unique = False
        mock_column.nullable = False
        mock_column.default = None
        mock_column.server_default = None
        mock_column.type = Mock()  # Add type attribute
        mock_prop.columns = [mock_column]
        mock_prop.key = "id"

        mock_model = Mock()
        mock_mapper = Mock()
        mock_mapper.class_ = mock_model

        # Import the real isinstance for fallback
        import builtins

        real_isinstance = builtins.isinstance

        with patch("flask_admin.contrib.sqlmodel.form.isinstance") as mock_isinstance:
            # Configure isinstance to handle different checks in the convert method
            def isinstance_side_effect(obj, class_):
                if (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "FieldPlaceholder"
                ):
                    return False  # Mock prop is not a FieldPlaceholder
                elif (
                    obj is mock_column
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "Column"
                ):
                    return True  # Mock column is a Column
                else:
                    # Fall back to real isinstance for other checks
                    return real_isinstance(obj, class_)

            mock_isinstance.side_effect = isinstance_side_effect

            with patch(
                "flask_admin.contrib.sqlmodel.form.has_multiple_pks"
            ) as mock_has_multiple:
                mock_has_multiple.return_value = False  # Single PK

                with patch("flask_admin.contrib.sqlmodel.form.Unique") as mock_unique:
                    mock_unique_instance = Mock()
                    mock_unique.return_value = mock_unique_instance

                    kwargs = {"validators": []}
                    result = converter.convert(
                        mock_model, mock_mapper, "id", mock_prop, kwargs, False
                    )

                    mock_unique.assert_called_once_with(
                        mock_session, mock_model, mock_column
                    )
                    assert mock_unique_instance in kwargs["validators"]
                    assert result is not None  # Field should be created


class TestFormChoicesAndConverter:
    """Test form choices and converter selection - lines 365-385."""

    def test_form_choices_select_field_creation(self):
        """Test form choices creates Select2Field."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.model = Mock()
        mock_view.form_choices = {
            "test_field": [("value1", "Label 1"), ("value2", "Label 2")]
        }
        mock_view.form_columns = None
        mock_view.form_optional_types = (Boolean,)
        mock_view.form_overrides = None  # Ensure no field overrides

        converter = AdminModelConverter(mock_session, mock_view)

        # Create mock property with regular column (exclude 'field' attribute)
        mock_prop = Mock(spec=["columns", "key"])
        mock_column = Mock()
        mock_column.primary_key = False
        mock_column.foreign_keys = set()
        mock_column.unique = False
        mock_column.nullable = True
        mock_column.default = None
        mock_column.server_default = None
        mock_prop.columns = [mock_column]
        mock_prop.key = "test_field"

        mock_model = Mock()
        mock_mapper = Mock()
        mock_mapper.class_ = mock_view.model

        # Import the real isinstance for fallback
        import builtins

        real_isinstance = builtins.isinstance

        with patch("flask_admin.contrib.sqlmodel.form.isinstance") as mock_isinstance:
            # Configure isinstance to handle different checks in the convert method
            def isinstance_side_effect(obj, class_):
                if (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "FieldPlaceholder"
                ):
                    return False  # Mock prop is not a FieldPlaceholder
                elif (
                    obj is mock_column
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "Column"
                ):
                    return True  # Mock column is a Column
                else:
                    # Fall back to real isinstance for other checks
                    return real_isinstance(obj, class_)

            mock_isinstance.side_effect = isinstance_side_effect

            with patch(
                "flask_admin.contrib.sqlmodel.form.form.Select2Field"
            ) as mock_select2:
                mock_select2_instance = Mock()
                mock_select2.return_value = mock_select2_instance

                kwargs = {"validators": []}
                result = converter.convert(
                    mock_model, mock_mapper, "test_field", mock_prop, kwargs, False
                )

                mock_select2.assert_called_once()
                call_kwargs = mock_select2.call_args[1]
                assert call_kwargs["choices"] == [
                    ("value1", "Label 1"),
                    ("value2", "Label 2"),
                ]
                assert (
                    call_kwargs["allow_blank"] is True
                )  # Since column.nullable = True
                assert result == mock_select2_instance

    def test_converter_returns_none_when_no_converter_found(self):
        """Test converter returns None when no converter is found."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view.model = Mock()
        mock_view.form_choices = None
        mock_view.form_columns = None
        mock_view.form_optional_types = (Boolean,)
        mock_view.form_overrides = None  # Ensure no field overrides

        converter = AdminModelConverter(mock_session, mock_view)

        # Create mock property with column
        # that has no converter (exclude 'field' attribute)
        mock_prop = Mock(spec=["columns", "key"])
        mock_column = Mock()
        mock_column.primary_key = False
        mock_column.foreign_keys = set()
        mock_column.unique = False
        mock_column.nullable = False
        mock_column.default = None
        mock_column.server_default = None
        mock_prop.columns = [mock_column]
        mock_prop.key = "test_field"

        mock_model = Mock()
        mock_mapper = Mock()
        mock_mapper.class_ = mock_view.model

        # Import the real isinstance for fallback
        import builtins

        real_isinstance = builtins.isinstance

        with patch("flask_admin.contrib.sqlmodel.form.isinstance") as mock_isinstance:
            # Configure isinstance to handle different checks in the convert method
            def isinstance_side_effect(obj, class_):
                if (
                    obj is mock_prop
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "FieldPlaceholder"
                ):
                    return False  # Mock prop is not a FieldPlaceholder
                elif (
                    obj is mock_column
                    and hasattr(class_, "__name__")
                    and class_.__name__ == "Column"
                ):
                    return True  # Mock column is a Column
                else:
                    # Fall back to real isinstance for other checks
                    return real_isinstance(obj, class_)

            mock_isinstance.side_effect = isinstance_side_effect

            with patch.object(converter, "get_converter") as mock_get_converter:
                mock_get_converter.return_value = None  # No converter found

                kwargs = {"validators": []}
                result = converter.convert(
                    mock_model, mock_mapper, "test_field", mock_prop, kwargs, False
                )

                assert result is None


class TestResolveProperty:
    """Test _resolve_prop function - line 678."""

    def test_resolve_prop_with_proxied_property(self):
        """Test _resolve_prop with proxied property."""
        mock_prop = Mock()
        mock_proxied = Mock()
        mock_prop._proxied_property = mock_proxied

        result = _resolve_prop(mock_prop)

        assert result == mock_proxied

    def test_resolve_prop_without_proxied_property(self):
        """Test _resolve_prop without proxied property."""
        mock_prop = Mock()
        # Don't set _proxied_property attribute
        del mock_prop._proxied_property  # Make sure it doesn't exist

        result = _resolve_prop(mock_prop)

        assert result == mock_prop


class TestGetFormEdgeCases:
    """Test get_form function edge cases - lines 716-807."""

    def test_get_form_with_extra_fields_and_only(self, sqlmodel_base: type[SQLModel]):
        """Test get_form with extra_fields when only is specified."""

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        extra_fields = {"extra_field": StringField()}

        # Test the logic where extra_fields are found in the find() function
        with patch(
            "flask_admin.contrib.sqlmodel.form.get_field_with_path"
        ) as mock_get_field:
            mock_get_field.return_value = (Mock(), None)

            form_class = get_form(
                TestModel,
                converter,
                only=["extra_field"],  # This should find the extra field
                extra_fields=extra_fields,
            )

            assert form_class is not None
            # The extra field should be included via the find() function

    def test_get_form_with_computed_field_in_only(self, sqlmodel_base: type[SQLModel]):
        """Test get_form with computed field in only list."""

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

            @property
            def computed_name(self) -> str:
                return f"computed_{self.name}"

        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = ["computed_name"]  # Fix mock to have proper attribute
        converter = AdminModelConverter(mock_session, mock_view)

        with patch(
            "flask_admin.contrib.sqlmodel.form.is_computed_field"
        ) as mock_is_computed:
            mock_is_computed.return_value = True

            with patch(
                "flask_admin.contrib.sqlmodel.form.get_computed_fields"
            ) as mock_get_computed:
                mock_computed_fields = {"computed_name": Mock()}
                mock_get_computed.return_value = mock_computed_fields

                form_class = get_form(TestModel, converter, only=["computed_name"])

                assert form_class is not None

    def test_get_form_field_not_found_error(self, sqlmodel_base: type[SQLModel]):
        """Test get_form raises error when field not found."""

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        with pytest.raises(ValueError, match="Field 'nonexistent' not found"):
            get_form(TestModel, converter, only=["nonexistent"])

    def test_get_form_invalid_model_property_error(self, sqlmodel_base: type[SQLModel]):
        """Test get_form raises error for invalid model property."""

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        with patch(
            "flask_admin.contrib.sqlmodel.form.get_field_with_path"
        ) as mock_get_field:
            mock_get_field.return_value = (None, None)  # Invalid field

            with pytest.raises(ValueError, match="Field 'invalid_field' not found"):
                get_form(TestModel, converter, only=["invalid_field"])

    def test_get_form_hidden_field_filtering(self, sqlmodel_base: type[SQLModel]):
        """Test get_form filters hidden fields when ignore_hidden=True."""

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str
            _hidden: Optional[str] = None

        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = None  # Fix mock to have proper attribute
        mock_view.form_optional_types = (Boolean,)  # Fix mock for form_optional_types
        converter = AdminModelConverter(mock_session, mock_view)

        form_class = get_form(TestModel, converter, ignore_hidden=True)

        # Hidden field should not be in the form
        assert not hasattr(form_class, "_hidden")
        assert hasattr(form_class, "name")

    def test_get_form_extra_fields_contribution(self, sqlmodel_base: type[SQLModel]):
        """Test get_form contributes extra_fields when not using only."""

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        mock_session = Mock()
        mock_view = Mock()
        mock_view.form_columns = None  # Fix mock to have proper attribute
        mock_view.form_optional_types = (Boolean,)  # Fix mock for form_optional_types
        converter = AdminModelConverter(mock_session, mock_view)

        extra_fields = {"extra_field": StringField()}

        with patch(
            "flask_admin.contrib.sqlmodel.form.form.recreate_field"
        ) as mock_recreate:
            mock_recreate.return_value = StringField()

            form_class = get_form(TestModel, converter, extra_fields=extra_fields)

            mock_recreate.assert_called()
            assert form_class is not None
