"""
Advanced tests for SQLModel form module covering SQLAlchemy utils converters
and inline model converters to improve coverage.

This file targets the remaining uncovered areas including:
- SQLAlchemy utils converters (lines 456-623)
- Inline model converters (lines 810-1055)
"""

from enum import Enum
from typing import Optional
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from sqlmodel import Field
from sqlmodel import SQLModel
from wtforms import StringField
from wtforms import validators

from flask_admin.contrib.sqlmodel.form import AdminModelConverter
from flask_admin.contrib.sqlmodel.form import choice_type_coerce_factory
from flask_admin.contrib.sqlmodel.form import InlineModelConverter
from flask_admin.contrib.sqlmodel.form import InlineOneToOneModelConverter
from flask_admin.model.form import InlineFormAdmin


class TestSQLAlchemyExtendedMixin:
    """Test SQLAlchemy-utils functionality via the new mixin architecture."""

    def test_mixin_basic_converters(self):
        """Test basic mixin converter methods."""
        from flask_admin.contrib.sqlmodel.mixins import SQLAlchemyExtendedMixin

        mixin = SQLAlchemyExtendedMixin()

        # Test email converter
        mock_column = Mock()
        mock_column.nullable = True
        field_args = {"validators": []}
        result = mixin._convert_email_type(mock_column, field_args)
        assert isinstance(result, type(StringField()))
        assert any(isinstance(v, validators.Email) for v in field_args["validators"])

        # Test URL converter
        field_args = {"validators": []}
        result = mixin._convert_url_type(field_args)
        assert isinstance(result, type(StringField()))
        assert any(isinstance(v, validators.URL) for v in field_args["validators"])
        assert len(field_args["filters"]) > 0

        # Test IP address converter
        field_args = {"validators": []}
        result = mixin._convert_ip_address_type(field_args)
        assert isinstance(result, type(StringField()))
        assert any(
            isinstance(v, validators.IPAddress) for v in field_args["validators"]
        )

        # Test color converter
        field_args = {"validators": []}
        result = mixin._convert_color_type(field_args)
        assert isinstance(result, type(StringField()))
        assert len(field_args["validators"]) > 0
        assert len(field_args["filters"]) > 0

        # Test currency converter
        field_args = {"validators": []}
        result = mixin._convert_currency_type(field_args)
        assert isinstance(result, type(StringField()))
        assert len(field_args["validators"]) > 0
        assert len(field_args["filters"]) > 0

    def test_mixin_choice_type_converter(self):
        """Test choice type converter with different scenarios."""
        from flask_admin.contrib.sqlmodel.mixins import SQLAlchemyExtendedMixin

        mixin = SQLAlchemyExtendedMixin()

        # Test with tuple choices
        mock_column = Mock()
        mock_column.nullable = True
        mock_column.type = Mock()
        mock_column.type.choices = [("value1", "Label 1"), ("value2", "Label 2")]
        field_args = {"validators": []}

        result = mixin._convert_choice_type(mock_column, field_args)
        assert result is not None
        assert field_args["allow_blank"] is True
        assert field_args["choices"] == [("value1", "Label 1"), ("value2", "Label 2")]

        # Test with enum choices
        class TestEnum(Enum):
            OPTION1 = "option1"
            OPTION2 = "option2"

        mock_column.type.choices = TestEnum
        field_args = {"validators": []}

        result = mixin._convert_choice_type(mock_column, field_args)
        assert result is not None
        expected_choices = [(f.value, f.name) for f in TestEnum]
        assert field_args["choices"] == expected_choices

    def test_mixin_timezone_converter(self):
        """Test timezone converter."""
        from flask_admin.contrib.sqlmodel.mixins import SQLAlchemyExtendedMixin

        mixin = SQLAlchemyExtendedMixin()

        mock_column = Mock()
        mock_column.type = Mock()
        mock_column.type._coerce = Mock()
        field_args = {"validators": []}

        result = mixin._convert_timezone_type(mock_column, field_args)
        assert isinstance(result, type(StringField()))
        assert len(field_args["validators"]) > 0

    def test_mixin_arrow_converter(self):
        """Test arrow time converter."""
        from flask_admin.contrib.sqlmodel.mixins import SQLAlchemyExtendedMixin

        mixin = SQLAlchemyExtendedMixin()
        field_args = {}

        result = mixin._convert_arrow_type(field_args)
        assert result is not None  # Should return DateTimeField

    def test_handle_integer_types_with_unsigned(self):
        """Test integer type handling with unsigned constraint."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        mock_column = Mock()
        mock_column.type = Mock()
        mock_column.type.unsigned = True
        field_args = {"validators": []}

        result = converter.handle_integer_types(mock_column, field_args)

        assert result is not None
        # Should add NumberRange validator with min=0
        number_range_validators = [
            v for v in field_args["validators"] if isinstance(v, validators.NumberRange)
        ]
        assert len(number_range_validators) > 0
        assert number_range_validators[0].min == 0

    def test_handle_decimal_types_with_places(self):
        """Test decimal type handling sets places to None."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        mock_column = Mock()
        field_args = {}

        result = converter.handle_decimal_types(mock_column, field_args)

        assert result is not None
        assert field_args["places"] is None

    def test_conv_pg_inet_with_label_and_validator(self):
        """Test PostgreSQL INET converter."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {"validators": []}

        result = converter.conv_PGInet(field_args)

        assert isinstance(result, type(StringField()))
        assert field_args["label"] == "IP Address"
        # Check that IPAddress validator was added
        ip_validators = [
            v for v in field_args["validators"] if isinstance(v, validators.IPAddress)
        ]
        assert len(ip_validators) > 0

    def test_conv_pg_macaddr_with_label_and_validator(self):
        """Test PostgreSQL MACADDR converter."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {"validators": []}

        result = converter.conv_PGMacaddr(field_args)

        assert isinstance(result, type(StringField()))
        assert field_args["label"] == "MAC Address"
        # Check that MacAddress validator was added
        mac_validators = [
            v for v in field_args["validators"] if isinstance(v, validators.MacAddress)
        ]
        assert len(mac_validators) > 0

    def test_conv_pg_uuid_with_filters_and_validator(self):
        """Test PostgreSQL UUID converter."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {"validators": []}

        result = converter.conv_PGUuid(field_args)

        assert isinstance(result, type(StringField()))
        assert field_args["label"] == "UUID"
        # Check that UUID validator was added
        uuid_validators = [
            v for v in field_args["validators"] if isinstance(v, validators.UUID)
        ]
        assert len(uuid_validators) > 0
        assert len(field_args["filters"]) > 0

    def test_conv_array_field(self):
        """Test ARRAY field converter."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {}

        result = converter.conv_ARRAY(field_args)

        assert result is not None  # Should return Select2TagsField

    def test_conv_hstore_with_custom_form(self):
        """Test HSTORE converter with custom form."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        custom_form = Mock()
        field_args = {"form": custom_form}

        result = converter.conv_HSTORE(field_args)

        assert result is not None
        # Custom form should be popped from field_args
        assert "form" not in field_args

    def test_conv_hstore_default_form(self):
        """Test HSTORE converter with default form."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {}

        result = converter.conv_HSTORE(field_args)

        assert result is not None  # Should use default HstoreForm

    def test_convert_json_field(self):
        """Test JSON field converter."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {}

        result = converter.convert_JSON(field_args)

        assert result is not None  # Should return JSONField

    def test_python_type_converters(self):
        """Test Python native type converters."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        mock_column = Mock()
        field_args = {}

        # Test string converter
        result = converter.conv_python_str(mock_column, field_args)
        assert result is not None

        # Test int converter
        result = converter.conv_python_int(field_args)
        assert result is not None

        # Test float converter
        result = converter.conv_python_float(field_args)
        assert result is not None
        assert field_args["places"] is None

        # Test bool converter
        result = converter.conv_python_bool(field_args)
        assert result is not None

    def test_pydantic_type_converters(self):
        """Test Pydantic type converters."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {"validators": []}

        # Test EmailStr converter
        result = converter.conv_pydantic_email(field_args)
        assert result is not None
        # Check that Email validator was added
        email_validators = [
            v for v in field_args["validators"] if isinstance(v, validators.Email)
        ]
        assert len(email_validators) > 0

        # Test URL converter
        field_args = {"validators": []}
        result = converter.conv_pydantic_url(field_args)
        assert result is not None
        # Check that URL validator was added
        url_validators = [
            v for v in field_args["validators"] if isinstance(v, validators.URL)
        ]
        assert len(url_validators) > 0

        # Test SecretStr converter
        field_args = {}
        result = converter.conv_pydantic_secret(field_args)
        assert result is not None

    def test_datetime_type_converters(self):
        """Test datetime type converters."""
        mock_session = Mock()
        mock_view = Mock()
        converter = AdminModelConverter(mock_session, mock_view)

        field_args = {}

        # Test datetime converter
        result = converter.conv_python_datetime(field_args)
        assert result is not None

        # Test date converter
        result = converter.conv_python_date(field_args)
        assert result is not None
        assert "widget" in field_args

        # Test time converter
        result = converter.conv_python_time(field_args)
        assert result is not None


class TestInlineModelConverters:
    """Test inline model converters - lines 810-1055."""

    def test_inline_model_converter_get_info_with_instance(
        self, engine, sqlmodel_base: type[SQLModel]
    ):
        """Test get_info with InlineFormAdmin instance."""
        from sqlmodel import Session

        session = Session(engine)
        mock_view = Mock()
        converter = InlineModelConverter(session, mock_view, AdminModelConverter)

        # Create a mock InlineFormAdmin instance
        mock_info = Mock(spec=InlineFormAdmin)

        result = converter.get_info(mock_info)

        assert result == mock_info
        # Should process AJAX refs
        assert hasattr(result, "_form_ajax_refs")

    def test_inline_model_converter_get_info_with_tuple(
        self, engine, sqlmodel_base: type[SQLModel]
    ):
        """Test get_info with tuple configuration."""
        from sqlmodel import Session

        session = Session(engine)
        mock_view = Mock()
        converter = InlineModelConverter(session, mock_view, AdminModelConverter)

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        tuple_config = (TestModel, {"form_columns": ["name"]})

        # Let it use the real form_admin_class (InlineFormAdmin)
        result = converter.get_info(tuple_config)

        # Result should be an instance of InlineFormAdmin
        assert isinstance(result, InlineFormAdmin)
        assert result.model == TestModel

    def test_inline_model_converter_get_info_with_model_class(
        self, engine, sqlmodel_base: type[SQLModel]
    ):
        """Test get_info with raw model class."""
        from sqlmodel import Session

        session = Session(engine)
        mock_view = Mock()
        converter = InlineModelConverter(session, mock_view, AdminModelConverter)

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        # Let it use the real form_admin_class (InlineFormAdmin)
        result = converter.get_info(TestModel)

        # Result should be an instance of InlineFormAdmin
        assert isinstance(result, InlineFormAdmin)
        assert result.model == TestModel

    def test_inline_model_converter_get_info_with_custom_object(
        self, engine, sqlmodel_base: type[SQLModel]
    ):
        """Test get_info with custom object having model attribute."""
        from sqlmodel import Session

        session = Session(engine)
        mock_view = Mock()
        converter = InlineModelConverter(session, mock_view, AdminModelConverter)

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        class CustomObject:
            model = TestModel
            form_columns = ["name"]
            custom_attr = "custom_value"

        custom_obj = CustomObject()

        # Let it use the real form_admin_class (InlineFormAdmin)
        result = converter.get_info(custom_obj)

        # Result should be an instance of InlineFormAdmin with custom attributes
        assert isinstance(result, InlineFormAdmin)
        assert result.model == TestModel
        # Check that custom attributes were extracted
        assert hasattr(result, "form_columns")
        assert hasattr(result, "custom_attr")

    def test_inline_model_converter_get_info_invalid_object(
        self, engine, sqlmodel_base
    ):
        """Test get_info with invalid object raises exception."""
        from sqlmodel import Session

        session = Session(engine)
        mock_view = Mock()
        converter = InlineModelConverter(session, mock_view, AdminModelConverter)

        class InvalidObject:
            pass  # No model attribute

        invalid_obj = InvalidObject()

        with pytest.raises(Exception, match="Unknown inline model admin"):
            converter.get_info(invalid_obj)

    def test_process_ajax_refs_with_dict_opts(self, sqlmodel_base: type[SQLModel]):
        """Test process_ajax_refs with dictionary options."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view._form_ajax_refs = {}
        mock_model_converter = Mock()

        converter = InlineModelConverter(mock_session, mock_view, mock_model_converter)

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        mock_info = Mock()
        mock_info.model = TestModel
        mock_info.form_ajax_refs = {"field_name": {"option": "value"}}

        with patch(
            "flask_admin.contrib.sqlmodel.form.create_ajax_loader"
        ) as mock_create_loader:
            mock_loader = Mock()
            mock_loader.name = "testmodel-field_name"
            mock_create_loader.return_value = mock_loader

            result = converter.process_ajax_refs(mock_info)

            assert "field_name" in result
            assert result["field_name"] == mock_loader
            assert mock_view._form_ajax_refs["testmodel-field_name"] == mock_loader

    def test_process_ajax_refs_with_non_dict_opts(self, sqlmodel_base: type[SQLModel]):
        """Test process_ajax_refs with non-dictionary options."""
        mock_session = Mock()
        mock_view = Mock()
        mock_view._form_ajax_refs = {}
        mock_model_converter = Mock()

        converter = InlineModelConverter(mock_session, mock_view, mock_model_converter)

        class TestModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        mock_loader = Mock()
        mock_info = Mock()
        mock_info.model = TestModel
        mock_info.form_ajax_refs = {"field_name": mock_loader}

        result = converter.process_ajax_refs(mock_info)

        assert "field_name" in result
        assert result["field_name"] == mock_loader
        mock_loader.name = "testmodel-field_name"

    def test_calculate_mapping_key_pair_self_referential_skip_manytoone(
        self, engine, sqlmodel_base: type[SQLModel]
    ):
        """Test _calculate_mapping_key_pair
        skips MANYTOONE in self-referential models."""
        from sqlmodel import Session

        session = Session(engine)
        mock_view = Mock()
        converter = InlineModelConverter(session, mock_view, AdminModelConverter)

        # Create a simple self-referential model
        class TreeNode(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str
            parent_id: Optional[int] = Field(default=None, foreign_key="treenode.id")

        # Create the tables
        sqlmodel_base.metadata.create_all(engine)

        # Create info object with the same model (self-referential)
        info = InlineFormAdmin(TreeNode)

        # Test that the method can be called without crashing
        # For a simple self-referential model without explicit relationships,
        # it should raise "No inline relationship found"
        # since no relationships are defined
        with pytest.raises(Exception, match="No inline relationship found"):
            converter._calculate_mapping_key_pair(TreeNode, info)

    def test_calculate_mapping_key_pair_no_relationship_found(
        self, sqlmodel_base: type[SQLModel]
    ):
        """Test _calculate_mapping_key_pair
        raises exception when no relationship found."""
        mock_session = Mock()
        mock_view = Mock()
        mock_model_converter = Mock()

        converter = InlineModelConverter(mock_session, mock_view, mock_model_converter)

        class ParentModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)

        class ChildModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)

        mock_info = Mock()
        mock_info.model = ChildModel

        # Mock empty relationships
        mock_mapper = Mock()
        mock_mapper.relationships = []

        with patch.object(ParentModel, "_sa_class_manager") as mock_manager:
            mock_manager.mapper = mock_mapper

            with pytest.raises(Exception, match="No inline relationship found"):
                converter._calculate_mapping_key_pair(ParentModel, mock_info)

    def test_find_back_populates_with_list_type(self, sqlmodel_base: type[SQLModel]):
        """Test _find_back_populates with list type annotation."""

        from sqlmodel import Relationship

        mock_session = Mock()
        mock_view = Mock()
        mock_model_converter = Mock()

        converter = InlineModelConverter(mock_session, mock_view, mock_model_converter)

        class ParentModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str

        class RelatedModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            # Define a field with list type annotation that should match ParentModel
            parents: list[ParentModel] = Relationship()

        result = converter._find_back_populates(RelatedModel, ParentModel, "related")

        # The method should find the "parents" field
        # because it has list type with ParentModel
        assert result == "parents"

    def test_find_back_populates_fallback(self, sqlmodel_base: type[SQLModel]):
        """Test _find_back_populates fallback to model name."""
        mock_session = Mock()
        mock_view = Mock()
        mock_model_converter = Mock()

        converter = InlineModelConverter(mock_session, mock_view, mock_model_converter)

        class ParentModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)

        class RelatedModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            # No fields that match ParentModel, so should fallback

        result = converter._find_back_populates(RelatedModel, ParentModel, "related")

        assert result == "parentmodel"  # Lowercase model name


class TestInlineOneToOneModelConverter:
    """Test InlineOneToOneModelConverter - lines 1000-1055."""

    def test_calculate_mapping_key_pair_with_back_populates(
        self, sqlmodel_base: type[SQLModel]
    ):
        """Test _calculate_mapping_key_pair with back_populates relationship."""
        mock_session = Mock()
        mock_view = Mock()
        mock_model_converter = Mock()

        converter = InlineOneToOneModelConverter(
            mock_session, mock_view, mock_model_converter
        )

        class ParentModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)

        class ChildModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)

        mock_info = Mock()
        mock_info.model = ChildModel

        # Mock relationship with back_populates
        mock_rel = Mock()
        mock_rel.mapper.class_ = ParentModel
        mock_rel.back_populates = "parent_rel"
        mock_rel.key = "child_rel"

        mock_mapper = Mock()
        mock_mapper.relationships = [mock_rel]

        with patch.object(ChildModel, "_sa_class_manager") as mock_manager:
            mock_manager.mapper = mock_mapper

            result = converter._calculate_mapping_key_pair(ParentModel, mock_info)

            assert result == {"parent_rel": "child_rel"}

    def test_calculate_mapping_key_pair_no_back_populates(
        self, sqlmodel_base: type[SQLModel]
    ):
        """Test _calculate_mapping_key_pair raises exception without back_populates."""
        mock_session = Mock()
        mock_view = Mock()
        mock_model_converter = Mock()

        converter = InlineOneToOneModelConverter(
            mock_session, mock_view, mock_model_converter
        )

        class ParentModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)

        class ChildModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)

        mock_info = Mock()
        mock_info.model = ChildModel

        # Mock relationship without back_populates
        mock_rel = Mock()
        mock_rel.mapper.class_ = ParentModel
        mock_rel.back_populates = None
        mock_rel.key = "child_rel"

        mock_mapper = Mock()
        mock_mapper.relationships = [mock_rel]

        with patch.object(ChildModel, "_sa_class_manager") as mock_manager:
            mock_manager.mapper = mock_mapper

            with pytest.raises(Exception, match="must define 'back_populates'"):
                converter._calculate_mapping_key_pair(ParentModel, mock_info)

    def test_contribute_with_excluded_columns(self, sqlmodel_base: type[SQLModel]):
        """Test contribute method with excluded columns."""
        mock_session = Mock()
        mock_view = Mock()
        mock_model_converter = Mock()

        converter = InlineOneToOneModelConverter(
            mock_session, mock_view, mock_model_converter
        )

        class ParentModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)

        class ChildModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)

        mock_info = Mock()
        mock_info.model = ChildModel
        mock_info.form_excluded_columns = ["excluded_field"]
        mock_info.get_form.return_value = None
        mock_info.form_columns = None
        mock_info.form_base_class = None
        mock_info.form_args = None
        mock_info.form_extra_fields = None
        mock_info.postprocess_form = lambda x: x

        mock_form_class = Mock()

        with patch.object(converter, "_calculate_mapping_key_pair") as mock_calc:
            mock_calc.return_value = {"parent_rel": "child_rel"}

            with patch.object(converter, "model_converter") as mock_conv_class:
                mock_conv_instance = Mock()
                mock_conv_class.return_value = mock_conv_instance

                with patch(
                    "flask_admin.contrib.sqlmodel.form.get_form"
                ) as mock_get_form:
                    mock_child_form = Mock()
                    mock_get_form.return_value = mock_child_form

                    result = converter.contribute(
                        ParentModel, mock_form_class, mock_info
                    )

                    # Check that excluded columns were passed correctly
                    mock_get_form.assert_called_once()
                    call_kwargs = mock_get_form.call_args[1]
                    assert "child_rel" in call_kwargs["exclude"]
                    assert "excluded_field" in call_kwargs["exclude"]

                    assert result == mock_form_class


class TestChoiceTypeCoerceFactory:
    """Test choice_type_coerce_factory function edge cases."""

    def test_choice_coerce_with_enum_choices(self):
        """Test choice coerce with enum choices."""

        class TestEnum(Enum):
            OPTION1 = "option1"
            OPTION2 = "option2"

        mock_type = Mock()
        mock_type.choices = TestEnum
        mock_type.python_type = str

        # Mock the sqlalchemy_utils import inside the function
        with patch("builtins.__import__") as mock_import:
            # Mock successful import of sqlalchemy_utils
            mock_choice_cls = Mock()
            mock_sqlalchemy_utils = Mock()
            mock_sqlalchemy_utils.Choice = mock_choice_cls

            def import_side_effect(name, *args, **kwargs):
                if name == "sqlalchemy_utils":
                    return mock_sqlalchemy_utils
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            coerce_func = choice_type_coerce_factory(mock_type)

            # Test with None
            result = coerce_func(None)
            assert result is None

            # Test with enum value - should return the value since it's an enum
            result = coerce_func(TestEnum.OPTION1)
            assert result == "option1"

    def test_choice_coerce_with_choice_class(self):
        """Test choice coerce with Choice class."""

        mock_type = Mock()
        mock_type.choices = [("value1", "Label 1")]
        mock_type.python_type = str

        # Test the fallback case when sqlalchemy_utils is not available
        with patch("builtins.__import__", side_effect=ImportError):
            coerce_func = choice_type_coerce_factory(mock_type)

            # Test with regular value - should just return the value
            result = coerce_func("test_value")
            assert result == "test_value"

            # Test with None
            result = coerce_func(None)
            assert result is None
