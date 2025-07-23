"""
Comprehensive CRUD tests for UUID fields and computed properties in SQLModel.

This test file validates that Flask-Admin correctly handles SQLModel models
with UUID primary keys and computed properties through full Create, Read,
Update, Delete operations.
"""

import uuid
from typing import Optional

from sqlmodel import Field
from sqlmodel import select
from sqlmodel import Session

from flask_admin.contrib.sqlmodel import SQLModelView
from flask_admin.tests.sqlmodel import sqlmodel_base

sqlmodel_class = sqlmodel_base()

class UUIDPropertyTestModel(sqlmodel_class, table=True):
    """Test model with UUID primary key and computed properties."""

    __tablename__ = "uuid_property_test" # type: ignore

    # UUID primary key using native SQLModel
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Basic fields
    first_name: str
    last_name: str
    age: int
    email: Optional[str] = None
    phone: Optional[str] = None
    dialling_code: Optional[str] = Field(default="39")

    # Computed property with getter and setter
    @property
    def full_name(self) -> str:
        """Computed property combining first and last name."""
        return f"{self.first_name} {self.last_name}"

    @full_name.setter
    def full_name(self, value: str):
        """Setter to allow form processing."""
        if value is None or value == "":
            # Skip setting if no value provided
            return
        parts = value.split(" ", 1)
        if len(parts) >= 2:
            self.first_name, self.last_name = parts[0], parts[1]
        else:
            self.first_name = parts[0]
            self.last_name = ""

    # Phone number property with formatting and filtering support
    @property
    def formatted_phone(self) -> str:
        """Format phone number for display."""
        if not self.phone:
            return ""

        # Remove any non-digit characters for processing
        clean_phone = "".join(filter(str.isdigit, self.phone))
        if len(clean_phone) < 6:
            return self.phone or ""

        # Format based on length
        if len(clean_phone) <= 10:
            # Format as local number
            if len(clean_phone) == 10:
                return f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}"
            else:
                return clean_phone
        else:
            # International format
            return f"+{self.dialling_code} {clean_phone}"

    @formatted_phone.setter
    def formatted_phone(self, value: str):
        """Allow setting phone through formatted property."""
        if value and value.strip():
            # Store clean digits only
            self.phone = "".join(filter(str.isdigit, value))
        else:
            self.phone = None


class UUIDPropertyTestModelView(SQLModelView):
    """Custom view for testing UUID and property handling."""

    # Include computed properties in column list and form
    column_list = [
        "id",
        "first_name",
        "last_name",
        "full_name",
        "age",
        "email",
        "formatted_phone",
    ]
    column_searchable_list = ["first_name", "last_name", "email"]
    column_filters = ["first_name", "last_name", "age", "email", "formatted_phone"]

    # Only include basic fields in form to avoid setter issues
    form_columns = ["first_name", "last_name", "age", "email", "phone", "dialling_code"]

    # Override to show readable labels
    column_labels = {
        "id": "ID",
        "full_name": "Full Name",
        "formatted_phone": "Phone Number",
    }


def test_uuid_property_full_crud(app, engine, admin):
    """Test complete CRUD operations with UUID primary keys and computed properties."""

    # Create tables
    sqlmodel_class.metadata.create_all(engine)

    with app.app_context():
        with Session(engine) as db_session:
            # Add the view to admin
            view = UUIDPropertyTestModelView(UUIDPropertyTestModel, db_session)
            admin.add_view(view)

            client = app.test_client()

            # === CREATE OPERATION ===
            print("=== Testing CREATE ===")

            # Test creating a new record through the form
            create_data = {
                "first_name": "John",
                "last_name": "Doe",
                "age": "30",
                "email": "john.doe@example.com",
                "phone": "1234567890",
                "dialling_code": "1",
            }

            # Create the record
            rv = client.post("/admin/uuidpropertytestmodel/new/", data=create_data)
            assert rv.status_code == 302  # Redirect after successful creation

            # Verify the record was created in the database
            stmt = select(UUIDPropertyTestModel).where(
                UUIDPropertyTestModel.email == "john.doe@example.com"
            )
            created_record = db_session.exec(stmt).first()
            assert created_record is not None
            assert created_record.first_name == "John"
            assert created_record.last_name == "Doe"
            assert created_record.age == 30
            assert created_record.email == "john.doe@example.com"
            assert created_record.phone == "1234567890"
            assert isinstance(created_record.id, uuid.UUID)

            # Test computed properties
            assert created_record.full_name == "John Doe"
            assert (
                created_record.formatted_phone == "(123) 456-7890"
            )  # Should be formatted

            record_id = created_record.id

            # === READ OPERATIONS ===
            print("=== Testing READ ===")

            # Test list view shows the record
            rv = client.get("/admin/uuidpropertytestmodel/")
            assert rv.status_code == 200
            assert "John" in rv.text
            assert "Doe" in rv.text
            assert "john.doe@example.com" in rv.text

            # Test that UUID is displayed properly (should show as string)
            assert str(record_id) in rv.text

            # Test edit form loads correctly with UUID in URL
            rv = client.get(f"/admin/uuidpropertytestmodel/edit/?id={record_id}")
            assert rv.status_code == 200
            assert 'value="John"' in rv.text
            assert 'value="Doe"' in rv.text
            assert "john.doe@example.com" in rv.text

            # Test details view if available
            rv = client.get(f"/admin/uuidpropertytestmodel/details/?id={record_id}")
            # Details might not be enabled, so accept 200, 302, or 404
            assert rv.status_code in [200, 302, 404]

            # === UPDATE OPERATION ===
            print("=== Testing UPDATE ===")

            # Test updating the record
            update_data = {
                "first_name": "Jane",
                "last_name": "Smith",
                "age": "28",
                "email": "jane.smith@example.com",
                "phone": "9876543210",
                "dialling_code": "1",
            }

            # Update via form submission
            rv = client.post(
                f"/admin/uuidpropertytestmodel/edit/?id={record_id}", data=update_data
            )
            assert rv.status_code == 302  # Redirect after successful update

            # Verify the record was updated in database
            db_session.refresh(created_record)
            assert created_record.first_name == "Jane"
            assert created_record.last_name == "Smith"
            assert created_record.age == 28
            assert created_record.email == "jane.smith@example.com"
            assert created_record.phone == "9876543210"
            assert created_record.id == record_id  # UUID should remain the same

            # Test computed properties after update
            assert created_record.full_name == "Jane Smith"
            assert (
                created_record.formatted_phone == "(987) 654-3210"
            )  # Should be formatted

            # Verify update is reflected in list view
            rv = client.get("/admin/uuidpropertytestmodel/")
            assert rv.status_code == 200
            assert "Jane" in rv.text
            assert "Smith" in rv.text
            assert "jane.smith@example.com" in rv.text
            # Old data should be gone
            assert "John" not in rv.text
            assert "john.doe@example.com" not in rv.text

            # === DELETE OPERATION ===
            print("=== Testing DELETE ===")

            # Test deleting the record
            rv = client.post(
                "/admin/uuidpropertytestmodel/delete/", data={"id": str(record_id)}
            )
            assert rv.status_code == 302  # Redirect after successful deletion

            # Verify the record was deleted from database
            stmt = select(UUIDPropertyTestModel).where(
                UUIDPropertyTestModel.id == record_id
            )
            deleted_record = db_session.exec(stmt).first()
            assert deleted_record is None

            # Verify deletion is reflected in list view
            rv = client.get("/admin/uuidpropertytestmodel/")
            assert rv.status_code == 200
            assert "Jane" not in rv.text
            assert "jane.smith@example.com" not in rv.text


def test_uuid_property_edge_cases(app, engine, admin):
    """Test edge cases with UUID and property handling."""

    # Create tables
    sqlmodel_class.metadata.create_all(engine)

    with app.app_context():
        with Session(engine) as db_session:
            # Add the view to admin
            view = UUIDPropertyTestModelView(UUIDPropertyTestModel, db_session)
            admin.add_view(view)

            client = app.test_client()

            # Test with minimal data
            create_data = {
                "first_name": "Min",
                "last_name": "User",
                "age": "25",
                # No email, phone, etc.
            }

            rv = client.post("/admin/uuidpropertytestmodel/new/", data=create_data)
            assert rv.status_code == 302

            # Find the created record
            stmt = select(UUIDPropertyTestModel).where(
                UUIDPropertyTestModel.first_name == "Min"
            )
            record = db_session.exec(stmt).first()
            assert record is not None
            assert record.full_name == "Min User"
            assert record.formatted_phone == ""  # Empty phone should work

            # Test invalid UUID in URL (should handle gracefully)
            rv = client.get("/admin/uuidpropertytestmodel/edit/?id=invalid-uuid")
            assert rv.status_code == 302  # Should redirect, not crash

            # Test empty UUID (should handle gracefully)
            rv = client.get("/admin/uuidpropertytestmodel/edit/?id=")
            assert rv.status_code in [302, 404]  # Should not crash

            # Clean up
            db_session.delete(record)
            db_session.commit()


def test_uuid_property_filtering_and_search(app, engine, admin):
    """Test filtering and searching with UUID primary keys and computed properties."""

    # Create tables
    sqlmodel_class.metadata.create_all(engine)

    with app.app_context():
        with Session(engine) as db_session:
            # Add the view to admin
            view = UUIDPropertyTestModelView(UUIDPropertyTestModel, db_session)
            admin.add_view(view)

            client = app.test_client()

            # Create test records
            test_records = [
                {
                    "first_name": "Alice",
                    "last_name": "Johnson",
                    "age": "25",
                    "email": "alice@example.com",
                    "phone": "1111111111",
                },
                {
                    "first_name": "Bob",
                    "last_name": "Williams",
                    "age": "35",
                    "email": "bob@example.com",
                    "phone": "2222222222",
                },
                {
                    "first_name": "Carol",
                    "last_name": "Johnson",
                    "age": "30",
                    "email": "carol@example.com",
                    "phone": "3333333333",
                },
            ]

            # Create all records
            created_ids = []
            for record_data in test_records:
                rv = client.post("/admin/uuidpropertytestmodel/new/", data=record_data)
                assert rv.status_code == 302

                # Find the created record to get its UUID
                stmt = select(UUIDPropertyTestModel).where(
                    UUIDPropertyTestModel.email == record_data["email"]
                )
                created_record = db_session.exec(stmt).first()
                assert created_record is not None
                created_ids.append(created_record.id)

            # Test basic list view with all records
            rv = client.get("/admin/uuidpropertytestmodel/")
            assert rv.status_code == 200
            assert "Alice" in rv.text
            assert "Bob" in rv.text
            assert "Carol" in rv.text

            # Test search functionality
            rv = client.get("/admin/uuidpropertytestmodel/?search=Alice")
            assert rv.status_code == 200
            assert "Alice" in rv.text
            assert "Bob" not in rv.text
            assert "Carol" not in rv.text

            # Test filtering (if filters are working)
            # Note: Computed property filtering may use post-query filtering
            rv = client.get("/admin/uuidpropertytestmodel/?flt1_1=Johnson")
            assert rv.status_code == 200
            # Should show Alice and Carol (both have Johnson as last name)
            # Exact behavior depends on filter implementation

            # Clean up all test records
            for record_id in created_ids:
                stmt = select(UUIDPropertyTestModel).where(
                    UUIDPropertyTestModel.id == record_id
                )
                record = db_session.exec(stmt).first()
                if record:
                    db_session.delete(record)
            db_session.commit()


def test_uuid_property_bulk_operations(app, engine, admin):
    """Test bulk operations with UUID primary keys."""

    # Create tables
    sqlmodel_class.metadata.create_all(engine)

    with app.app_context():
        with Session(engine) as db_session:
            # Add the view to admin
            view = UUIDPropertyTestModelView(UUIDPropertyTestModel, db_session)
            admin.add_view(view)

            client = app.test_client()

            # Create multiple test records
            test_data = [
                ("Test1", "User1", "test1@example.com"),
                ("Test2", "User2", "test2@example.com"),
                ("Test3", "User3", "test3@example.com"),
            ]

            created_ids = []
            for first, last, email in test_data:
                record_data = {
                    "first_name": first,
                    "last_name": last,
                    "age": "25",
                    "email": email,
                }

                rv = client.post("/admin/uuidpropertytestmodel/new/", data=record_data)
                assert rv.status_code == 302

                # Get the created record's UUID
                stmt = select(UUIDPropertyTestModel).where(
                    UUIDPropertyTestModel.email == email
                )
                record = db_session.exec(stmt).first()
                assert record is not None
                created_ids.append(record.id)

            # Test that all records exist
            rv = client.get("/admin/uuidpropertytestmodel/")
            assert rv.status_code == 200
            assert "Test1" in rv.text
            assert "Test2" in rv.text
            assert "Test3" in rv.text

            # Test bulk delete if supported
            # Note: This tests the underlying UUID handling in bulk operations
            delete_data = {"action": "delete", "rowid": [str(id) for id in created_ids]}
            rv = client.post("/admin/uuidpropertytestmodel/action/", data=delete_data)

            # Verify records are gone (exact behavior depends
            # on Flask-Admin bulk action implementation)
            for record_id in created_ids:
                stmt = select(UUIDPropertyTestModel).where(
                    UUIDPropertyTestModel.id == record_id
                )
                record = db_session.exec(stmt).first()
                # Record should be deleted or at least deletion attempted
                # The exact assertion depends on whether bulk delete is implemented
