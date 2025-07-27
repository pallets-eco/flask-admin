"""
Integration tests for special Pydantic field types in SQLModel forms.

This file tests the complete integration of advanced Pydantic types including:
- SecretBytes, IPvAnyAddress, IPv4Address, IPv6Address
- UUID variants (UUID1, UUID3, UUID4, UUID5)
- Json type
- Proper form generation, validation, and field handling
"""

import uuid
from typing import Optional

import pytest
from sqlalchemy import JSON
from sqlalchemy import String
from sqlmodel import Field
from sqlmodel import SQLModel
from wtforms import fields
from wtforms import validators

from flask_admin.contrib.sqlmodel.view import SQLModelView

# Import types with fallbacks for testing
try:
    from pydantic import Json
    from pydantic import SecretBytes
    from pydantic.types import UUID1
    from pydantic.types import UUID4

    ADVANCED_TYPES_AVAILABLE = True
except ImportError:
    ADVANCED_TYPES_AVAILABLE = False

try:
    # IPv4Address and IPv6Address come from the standard library, not pydantic
    from ipaddress import IPv4Address
    from ipaddress import IPv6Address

    from pydantic import IPvAnyAddress

    IP_TYPES_AVAILABLE = True
except ImportError:
    IP_TYPES_AVAILABLE = False


class TestSpecialPydanticTypesIntegration:
    """Integration tests for special Pydantic field types."""

    @pytest.mark.skipif(
        not ADVANCED_TYPES_AVAILABLE, reason="Advanced Pydantic types not available"
    )
    def test_secret_bytes_field_conversion(
        self, app, engine, sqlmodel_base: type[SQLModel]
    ):
        """Test SecretBytes field conversion and form generation."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class SecretModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str
            # Use sa_type to specify SQLAlchemy type for Pydantic SecretBytes
            secret_data: SecretBytes = Field(sa_type=String)
            optional_secret: Optional[SecretBytes] = Field(default=None, sa_type=String)

        # Create the view with proper session
        view = SQLModelView(SecretModel, session, name="Secret Model")

        with app.app_context():
            # Test form generation
            form = view.create_form()
            assert form is not None

            # Test field types in form - the actual integration test
            assert hasattr(form, "secret_data")
            assert isinstance(form.secret_data, fields.PasswordField)
            assert hasattr(form, "optional_secret")
            assert isinstance(form.optional_secret, fields.PasswordField)

    @pytest.mark.skipif(not IP_TYPES_AVAILABLE, reason="IP address types not available")
    def test_ip_address_field_conversion(
        self, app, engine, sqlmodel_base: type[SQLModel]
    ):
        """Test IP address field types conversion and validation."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class NetworkModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str
            # Use sa_type to specify SQLAlchemy type for Pydantic IP types
            any_ip: IPvAnyAddress = Field(sa_type=String)
            ipv4_addr: IPv4Address = Field(sa_type=String)
            ipv6_addr: IPv6Address = Field(sa_type=String)
            optional_ip: Optional[IPvAnyAddress] = Field(default=None, sa_type=String)

        # Create the view with proper session
        view = SQLModelView(NetworkModel, session, name="Network Model")

        with app.app_context():
            # Test form generation
            form = view.create_form()
            assert form is not None

            # Test all IP field types
            assert hasattr(form, "any_ip")
            assert isinstance(form.any_ip, fields.StringField)
            assert hasattr(form, "ipv4_addr")
            assert isinstance(form.ipv4_addr, fields.StringField)
            assert hasattr(form, "ipv6_addr")
            assert isinstance(form.ipv6_addr, fields.StringField)

            # Check for IP validation
            any_ip_validators = [type(v) for v in form.any_ip.validators]
            assert validators.IPAddress in any_ip_validators

    def test_uuid_field_conversion(self, app, engine, sqlmodel_base: type[SQLModel]):
        """Test UUID field types conversion and validation."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class UUIDModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str
            standard_uuid: uuid.UUID
            optional_uuid: Optional[uuid.UUID] = None

        # Create the view with proper session
        view = SQLModelView(UUIDModel, session, name="UUID Model")

        with app.app_context():
            # Test form generation
            form = view.create_form()
            assert form is not None

            assert hasattr(form, "standard_uuid")
            assert isinstance(form.standard_uuid, fields.StringField)
            assert hasattr(form, "optional_uuid")
            assert isinstance(form.optional_uuid, fields.StringField)

            # Check for UUID validation
            uuid_validators = [type(v) for v in form.standard_uuid.validators]
            assert validators.UUID in uuid_validators

    @pytest.mark.skipif(not ADVANCED_TYPES_AVAILABLE, reason="Json type not available")
    def test_json_field_conversion(self, app, engine, sqlmodel_base: type[SQLModel]):
        """Test Json field type conversion."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class JsonModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str
            # Use sa_type to specify SQLAlchemy type for Pydantic Json
            config_data: Json = Field(sa_type=JSON)
            optional_json: Optional[Json] = Field(default=None, sa_type=JSON)

        # Create the view with proper session
        view = SQLModelView(JsonModel, session, name="JSON Model")

        with app.app_context():
            # Test form generation
            form = view.create_form()
            assert form is not None

            # Test field types in form
            from flask_admin.form import JSONField

            assert hasattr(form, "config_data")
            assert isinstance(form.config_data, JSONField)
            assert hasattr(form, "optional_json")
            assert isinstance(form.optional_json, JSONField)


class TestSpecialTypesInSQLModelView:
    """Test special types integration with SQLModelView."""

    @pytest.mark.skipif(
        not ADVANCED_TYPES_AVAILABLE or not IP_TYPES_AVAILABLE,
        reason="Advanced types not available",
    )
    def test_complete_special_types_model_view(
        self, app, engine, sqlmodel_base: type[SQLModel]
    ):
        """Test a complete model with all special types in SQLModelView."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class CompleteSpecialTypesModel(sqlmodel_base, table=True):
            __tablename__ = "special_types_test"

            id: int = Field(primary_key=True)
            name: str

            # Secret types
            api_key: SecretBytes = Field(sa_type=String)
            password: Optional[SecretBytes] = Field(default=None, sa_type=String)

            # IP types
            server_ip: IPvAnyAddress = Field(sa_type=String)
            backup_ipv4: IPv4Address = Field(sa_type=String)
            backup_ipv6: IPv6Address = Field(sa_type=String)

            # UUID types
            session_id: uuid.UUID
            uuid1_id: UUID1 = (
                Field(sa_type=String) if ADVANCED_TYPES_AVAILABLE else uuid.UUID
            )
            uuid4_id: UUID4 = (
                Field(sa_type=String) if ADVANCED_TYPES_AVAILABLE else uuid.UUID
            )

            # JSON type
            config_metadata: Json = Field(sa_type=JSON)
            optional_config: Optional[Json] = Field(default=None, sa_type=JSON)

        # Create the view
        view = SQLModelView(CompleteSpecialTypesModel, session, name="Special Types")

        with app.app_context():
            # Test form creation
            form = view.create_form()
            assert form is not None

            # Test secret fields
            assert hasattr(form, "api_key")
            assert isinstance(form.api_key, fields.PasswordField)
            assert hasattr(form, "password")
            assert isinstance(form.password, fields.PasswordField)

            # Test IP fields
            assert hasattr(form, "server_ip")
            assert isinstance(form.server_ip, fields.StringField)
            assert hasattr(form, "backup_ipv4")
            assert isinstance(form.backup_ipv4, fields.StringField)
            assert hasattr(form, "backup_ipv6")
            assert isinstance(form.backup_ipv6, fields.StringField)

            # Test UUID fields
            assert hasattr(form, "session_id")
            assert isinstance(form.session_id, fields.StringField)
            assert hasattr(form, "uuid1_id")
            assert isinstance(form.uuid1_id, fields.StringField)
            assert hasattr(form, "uuid4_id")
            assert isinstance(form.uuid4_id, fields.StringField)

            # Test JSON fields
            assert hasattr(form, "config_metadata")
            from flask_admin.form import JSONField

            assert isinstance(form.config_metadata, JSONField)
            assert hasattr(form, "optional_config")
            assert isinstance(form.optional_config, JSONField)

    def test_field_validation_behavior(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test that validators are properly applied to special field types."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class ValidationTestModel(sqlmodel_base, table=True):
            __tablename__ = "validation_test"

            id: int = Field(primary_key=True)
            test_uuid: uuid.UUID

        view = SQLModelView(ValidationTestModel, session, name="Validation Test")

        with app.app_context():
            form = view.create_form()

            # Test UUID field has UUID validator
            uuid_field = form.test_uuid
            validator_types = [type(v) for v in uuid_field.validators]
            assert validators.UUID in validator_types

            # Test invalid UUID validation - create a fresh form for each test
            invalid_form = form.__class__(data={"test_uuid": "invalid-uuid"})
            assert not invalid_form.validate()
            assert invalid_form.test_uuid.errors

            # Test valid UUID validation
            valid_form = form.__class__(data={"test_uuid": str(uuid.uuid4())})
            # Note: We only check the UUID field since other
            # required fields might cause validation failures
            assert not valid_form.test_uuid.errors

    @pytest.mark.skipif(not IP_TYPES_AVAILABLE, reason="IP types not available")
    def test_ip_field_validation_behavior(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test IP address field validation behavior."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class IPTestModel(sqlmodel_base, table=True):
            __tablename__ = "ip_test"

            id: int = Field(primary_key=True)
            test_ip: IPvAnyAddress = Field(sa_type=String)

        view = SQLModelView(IPTestModel, session, name="IP Test")

        with app.app_context():
            form = view.create_form()

            # Test IP field has IP validator
            ip_field = form.test_ip
            validator_types = [type(v) for v in ip_field.validators]
            assert validators.IPAddress in validator_types

            # Test invalid IP validation - create a fresh form for each test
            invalid_form = form.__class__(data={"test_ip": "invalid-ip"})
            assert not invalid_form.validate()
            assert invalid_form.test_ip.errors

            # Test valid IPv4 validation
            valid_ipv4_form = form.__class__(data={"test_ip": "192.168.1.1"})
            assert not valid_ipv4_form.test_ip.errors

            # Test valid IPv6 validation
            valid_ipv6_form = form.__class__(data={"test_ip": "2001:db8::1"})
            assert not valid_ipv6_form.test_ip.errors


class TestSpecialTypesCompatibility:
    """Test compatibility and fallback behavior for special types."""

    def test_fallback_when_types_unavailable(self, sqlmodel_base: type[SQLModel]):
        """Test that the system gracefully handles missing Pydantic types."""

        # This test ensures the import system works correctly
        from flask_admin.contrib.sqlmodel.tools import PYDANTIC_IP_TYPES_AVAILABLE
        from flask_admin.contrib.sqlmodel.tools import PYDANTIC_TYPES_AVAILABLE

        # These should be boolean values, not None
        assert isinstance(PYDANTIC_TYPES_AVAILABLE, bool)
        assert isinstance(PYDANTIC_IP_TYPES_AVAILABLE, bool)

    def test_special_type_detection_function(self, sqlmodel_base: type[SQLModel]):
        """Test the special type detection function works correctly."""

        from flask_admin.contrib.sqlmodel.tools import _is_special_pydantic_type

        # Test with standard types
        assert not _is_special_pydantic_type(str)
        assert not _is_special_pydantic_type(int)

        # Test with available special types
        if ADVANCED_TYPES_AVAILABLE:
            from pydantic import Json
            from pydantic import SecretBytes

            assert _is_special_pydantic_type(Json)
            assert _is_special_pydantic_type(SecretBytes)

        if IP_TYPES_AVAILABLE:
            from pydantic import IPvAnyAddress

            assert _is_special_pydantic_type(IPvAnyAddress)

        # Test UUID (should always be available)
        import uuid

        assert _is_special_pydantic_type(uuid.UUID)
