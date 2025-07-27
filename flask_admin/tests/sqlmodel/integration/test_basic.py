import enum
import logging
import uuid
from datetime import date
from datetime import datetime
from datetime import time
from typing import Any
from typing import Optional

import arrow
import pytest
from pydantic import computed_field
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import registry
from sqlalchemy.types import Enum as SQLAEnum
from sqlalchemy_utils import ArrowType
from sqlalchemy_utils import ChoiceType
from sqlalchemy_utils import ColorType
from sqlalchemy_utils import CurrencyType
from sqlalchemy_utils import EmailType
from sqlalchemy_utils import IPAddressType
from sqlalchemy_utils import URLType
from sqlalchemy_utils import UUIDType
from sqlmodel import Boolean
from sqlmodel import Column
from sqlmodel import create_engine
from sqlmodel import Date
from sqlmodel import DateTime
from sqlmodel import Field
from sqlmodel import Float
from sqlmodel import Integer
from sqlmodel import Relationship
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import String
from sqlmodel import Text
from sqlmodel import Time
from sqlmodel import UnicodeText

# from flask_admin.contrib.sqla.fields import QuerySelectField
from wtforms import fields
from wtforms import validators

from flask_admin import form
from flask_admin._compat import as_unicode

# from wtforms.fields import DateTimeField
from flask_admin.contrib.sqlmodel import filters
from flask_admin.contrib.sqlmodel import SQLModelView
from flask_admin.contrib.sqlmodel import tools

# from flask_admin.contrib.sqlmodel import SQLModelView
from flask_admin.form import Select2Field
from flask_admin.form.fields import DateTimeField as AdminDateTimeField
from flask_admin.tests import flask_babel_test_decorator

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EnumChoices(enum.Enum):
    first = 1
    second = 2


class CustomModelView(SQLModelView):
    def __init__(
        self,
        model: Any,
        session: Any,
        name: Optional[str] = None,
        category: Optional[str] = None,
        endpoint: Optional[str] = None,
        url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

        super().__init__(model, session, name, category, endpoint, url)

    form_choices: dict[str, list[tuple[str, str]]] = {
        "choice_field": [("choice-1", "One"), ("choice-2", "Two")]
    }


# class CustomModelView(ModelView):
#     """
#         Flask-Admin ModelView with comprehensive SQLModel support
#         Handles Pydantic v2.11+ deprecation warnings and SQLModel-specific behaviors
#     """
#     def __init__(self, model, session, name=None,
#         category=None,
#         endpoint=None,
#         url=None,
#         **kwargs):
#         # Set configuration attributes first
#         for k, v in kwargs.items():
#             setattr(self, k, v)

#         # Then call parent initialization
#         super().__init__(model, session, name, category, endpoint, url)
#     def is_accessible(self):
#         return True

#     def _get_model_fields(self, model) -> set:
#         """
#         Get model fields from SQLModel, handling both instance and class access
#         Compatible with Pydantic v2.11+ deprecation warnings
#         """
#         try:
#             # If it's a class, access directly
#             if hasattr(model.__class__, 'model_fields'):
#                 return set(model.__class__.model_fields.keys())
#             else:
#                 # Fallback for older versions
#                 return set(getattr(model, '__fields__', {}).keys())
#         except Exception as e:
#             logger.warning(f"Could not get model fields: {e}")
#             return set()

#     def _is_sqlmodel(self, model_or_class) -> bool:
#         """Check if the model is a SQLModel instance or class"""
#         try:
#             if hasattr(model_or_class, '__class__'):
#                 return issubclass(model_or_class.__class__, SQLModel)
#             else:
#                 return issubclass(model_or_class, SQLModel)
#         except (TypeError, AttributeError):
#             return False

#     def _safe_setattr(self, model, field_name: str, value: Any) -> bool:
#         """
#         Safely set attribute on SQLModel, handling validation errors
#         """
#         try:
#             setattr(model, field_name, value)
#             return True
#         except ValidationError as e:
#             logger.warning(f"Validation error setting {field_name}={value}: {e}")
#             return False
#         except Exception as e:
#             logger.warning(f"Error setting {field_name}={value}: {e}")
#             return False

#     def update_model(self, form, model):
#         """Override update_model to handle SQLModel with Pydantic v2.11+"""
#         if not self._is_sqlmodel(model):
#             # Fall back to parent implementation for non-SQLModel
#             return super().update_model(form, model)

#         try:
#             # Get model fields from the model class
#             model_fields = self._get_model_fields(model)

#             # Track if any updates were made
#             updated = False
#             validation_errors = []

#             # Update only valid fields from the form
#             for field_name, field_obj in form._fields.items():
#                 if (field_name in model_fields and
#                     hasattr(field_obj, 'data') and
#                     field_name not in ['csrf_token', 'list_form_pk']):

#                     if self._safe_setattr(model, field_name, field_obj.data):
#                         updated = True
#                     else:
#                         validation_errors.append(f"Invalid value for {field_name}")

#             if validation_errors:
#                 flash(f"Validation errors: {'; '.join(validation_errors)}", 'error')
#                 return False

#             if updated:
#                 self.session.commit()
#                 return True
#             else:
#                 # No updates made, but not an error
#                 return True

#         except Exception as ex:
#             if not self.handle_view_exception(ex):
#                 flash(f'Failed to update record. {str(ex)}', 'error')
#             self.session.rollback()
#             return False

#     def edit_model(self, form, model):
#         """Override edit_model to handle SQLModel with Pydantic v2.11+"""
#         if not self._is_sqlmodel(model):
#             # Fall back to parent implementation for non-SQLModel
#             return super().edit_model(form, model)

#         try:
#             # Get model fields from the model class
#             model_fields = self._get_model_fields(model)

#             # Track if any updates were made
#             updated = False
#             validation_errors = []

#             # Update only valid fields from the form
#             for field_name, field_obj in form._fields.items():
#                 if (field_name in model_fields and
#                     hasattr(field_obj, 'data') and
#                     field_name not in ['csrf_token', 'list_form_pk']):

#                     if self._safe_setattr(model, field_name, field_obj.data):
#                         updated = True
#                     else:
#                         validation_errors.append(f"Invalid value for {field_name}")

#             if validation_errors:
#                 flash(f"Validation errors: {'; '.join(validation_errors)}", 'error')
#                 return False

#             if updated:
#                 self.session.commit()
#                 return True
#             else:
#                 # No updates made, but not an error
#                 return True

#         except Exception as ex:
#             if not self.handle_view_exception(ex):
#                 flash(f'Failed to update record. {str(ex)}', 'error')
#             self.session.rollback()
#             return False

#     def create_model(self, form):
#         """Override create_model to handle SQLModel with Pydantic v2.11+"""
#         if not self._is_sqlmodel(self.model):
#             # Fall back to parent implementation for non-SQLModel
#             return super().create_model(form)

#         try:
#             # Get model fields from the model class
#             model_fields = self._get_model_fields(self.model)

#             # Create model instance with form data
#             model_data = {}
#             validation_errors = []

#             for field_name, field_obj in form._fields.items():
#                 if (field_name in model_fields and
#                     hasattr(field_obj, 'data') and
#                     field_name not in ['csrf_token', 'list_form_pk']):
#                     model_data[field_name] = field_obj.data

#             # Create the model instance
#             try:
#                 model = self.model(**model_data)
#                 self.session.add(model)
#                 self.session.commit()
#                 return model
#             except ValidationError as e:
#                 validation_errors.append(f"Validation error: {str(e)}")
#                 flash(f"Validation errors: {'; '.join(validation_errors)}", 'error')
#                 return False

#         except Exception as ex:
#             if not self.handle_view_exception(ex):
#                 flash(f'Failed to create record. {str(ex)}', 'error')
#             self.session.rollback()
#             return False

#     def delete_model(self, model):
#         """Override delete_model to handle SQLModel specifics"""
#         if not self._is_sqlmodel(model):
#             # Fall back to parent implementation for non-SQLModel
#             return super().delete_model(model)

#         try:
#             self.session.delete(model)
#             self.session.commit()
#             return True
#         except Exception as ex:
#             if not self.handle_view_exception(ex):
#                 flash(f'Failed to delete record. {str(ex)}', 'error')
#             self.session.rollback()
#             return False


def sqlmodel_base() -> type[SQLModel]:
    """Create a fresh SQLModel base class for each test to avoid class name conflicts"""
    # Create a fresh registry and metadata for complete isolation
    test_registry = registry()

    # Create a new SQLModel base class with its own registry
    class SQLModelCleanRegistry(SQLModel, registry=test_registry):
        pass

    return SQLModelCleanRegistry


def create_models(
    engine: Any, sqlmodel_class: Optional[type[SQLModel]] = None
) -> tuple[type[SQLModel], type[SQLModel]]:
    """Create SQLModel models for testing with proper metadata handling"""
    if sqlmodel_class is None:
        sqlmodel_class = sqlmodel_base()

    class Model1(sqlmodel_class, table=True):
        __tablename__ = "model1"
        __table_args__ = {"extend_existing": True}  # Allow table recreation

        id: Optional[int] = Field(default=None, primary_key=True)
        test1: Optional[str] = Field(default=None, sa_column=Column(String(20)))
        test2: Optional[str] = Field(default=None, sa_column=Column(String(20)))
        test3: Optional[str] = Field(default=None, sa_column=Column(Text))
        test4: Optional[str] = Field(default=None, sa_column=Column(Text))
        bool_field: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
        date_field: Optional[date] = Field(default=None, sa_column=Column(Date))
        time_field: Optional[time] = Field(default=None, sa_column=Column(Time))
        datetime_field: Optional[datetime] = Field(
            default=None, sa_column=Column(DateTime)
        )
        email_field: Optional[str] = Field(default=None, sa_column=Column(EmailType))
        enum_field: Optional[str] = Field(
            default=None,
            sa_column=Column(SQLAEnum("model1_v1", "model1_v2"), nullable=True),
        )
        enum_type_field: Optional[EnumChoices] = Field(
            default=None, sa_column=Column(SQLAEnum(EnumChoices), nullable=True)
        )
        # choice_field: Optional[str] = Field(
        #     default=None,
        #     sa_column=Column(
        #         ChoiceType([
        #             ("choice-1", "First choice"),
        #             ("choice-2", "Second choice"),
        #         ])
        #     )
        # )
        choice_field: Optional[str] = Field(default=None, sa_column=Column(String))
        sqla_utils_choice: Optional[str] = Field(
            default=None,
            sa_column=Column(
                ChoiceType(
                    [("choice-1", "First choice"), ("choice-2", "Second choice")]
                )
            ),
        )
        sqla_utils_enum: Optional[EnumChoices] = Field(
            default=None, sa_column=Column(ChoiceType(EnumChoices, impl=Integer()))
        )
        sqla_utils_arrow: Optional[arrow.Arrow] = Field(
            default_factory=arrow.utcnow, sa_column=Column(ArrowType)
        )
        sqla_utils_uuid: Optional[uuid.UUID] = Field(
            default_factory=uuid.uuid4, sa_column=Column(UUIDType(binary=False))
        )
        sqla_utils_url: Optional[str] = Field(default=None, sa_column=Column(URLType))
        sqla_utils_ip_address: Optional[str] = Field(
            default=None, sa_column=Column(IPAddressType)
        )
        sqla_utils_currency: Optional[str] = Field(
            default=None, sa_column=Column(CurrencyType)
        )
        sqla_utils_color: Optional[str] = Field(
            default=None, sa_column=Column(ColorType)
        )

        # Relationships
        model2: list["Model2"] = Relationship(back_populates="model1")

        model_config = {"arbitrary_types_allowed": True}

        def __unicode__(self) -> str:
            return self.test1

        def __str__(self) -> str:
            return self.test1 or ""

    class Model2(sqlmodel_class, table=True):
        __tablename__ = "model2"
        __table_args__ = {"extend_existing": True}  # Allow table recreation
        model_config = {"arbitrary_types_allowed": True}

        id: Optional[int] = Field(default=None, primary_key=True)
        string_field: Optional[str] = Field(default=None, sa_column=Column(String))
        string_field_default: Optional[str] = Field(
            default="", sa_column=Column(Text, nullable=False)
        )
        string_field_empty_default: Optional[str] = Field(
            default="", sa_column=Column(Text, nullable=False)
        )
        int_field: Optional[int] = Field(default=None, sa_column=Column(Integer))
        bool_field: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
        enum_field: Optional[str] = Field(
            default=None,
            sa_column=Column(SQLAEnum("model2_v1", "model2_v2"), nullable=True),
        )
        float_field: Optional[float] = Field(default=None, sa_column=Column(Float))

        # Foreign key and relationship
        model1_id: Optional[int] = Field(default=None, foreign_key="model1.id")
        model1: Optional[Model1] = Relationship(back_populates="model2")

        model_config = {"arbitrary_types_allowed": True}

    # Create tables with the test metadata
    sqlmodel_class.metadata.create_all(engine)

    return Model1, Model2


def fill_db(session: Any, Model1: type[SQLModel], Model2: type[SQLModel]) -> None:
    """Fill database with test data"""
    model1_obj1 = Model1(test1="test1_val_1", test2="test2_val_1", bool_field=True)
    model1_obj2 = Model1(test1="test1_val_2", test2="test2_val_2", bool_field=False)
    model1_obj3 = Model1(test1="test1_val_3", test2="test2_val_3")
    model1_obj4 = Model1(
        test1="test1_val_4",
        test2="test2_val_4",
        email_field="test@test.com",
        choice_field="choice-1",
    )

    model2_obj1 = Model2(
        string_field="test2_val_1", model1=model1_obj1, float_field=None
    )
    model2_obj2 = Model2(
        string_field="test2_val_2", model1=model1_obj2, float_field=None
    )
    model2_obj3 = Model2(string_field="test2_val_3", int_field=5000, float_field=25.9)
    model2_obj4 = Model2(string_field="test2_val_4", int_field=9000, float_field=75.5)
    model2_obj5 = Model2(string_field="test2_val_5", int_field=6169453081680413441)

    date_obj1 = Model1(test1="date_obj1", date_field=date(2014, 11, 17))
    date_obj2 = Model1(test1="date_obj2", date_field=date(2013, 10, 16))
    timeonly_obj1 = Model1(test1="timeonly_obj1", time_field=time(11, 10, 9))
    timeonly_obj2 = Model1(test1="timeonly_obj2", time_field=time(10, 9, 8))
    datetime_obj1 = Model1(
        test1="datetime_obj1", datetime_field=datetime(2014, 4, 3, 1, 9, 0)
    )
    datetime_obj2 = Model1(
        test1="datetime_obj2", datetime_field=datetime(2013, 3, 2, 0, 8, 0)
    )

    enum_obj1 = Model1(test1="enum_obj1", enum_field="model1_v1")
    enum_obj2 = Model1(test1="enum_obj2", enum_field="model1_v2")

    enum_type_obj1 = Model1(test1="enum_type_obj1", enum_type_field=EnumChoices.first)
    enum_type_obj2 = Model1(test1="enum_type_obj2", enum_type_field=EnumChoices.second)

    empty_obj = Model1(test2="empty_obj")

    session.add_all(
        [
            model1_obj1,
            model1_obj2,
            model1_obj3,
            model1_obj4,
            model2_obj1,
            model2_obj2,
            model2_obj3,
            model2_obj4,
            model2_obj5,
            date_obj1,
            timeonly_obj1,
            datetime_obj1,
            date_obj2,
            timeonly_obj2,
            datetime_obj2,
            enum_obj1,
            enum_obj2,
            enum_type_obj1,
            enum_type_obj2,
            empty_obj,
        ]
    )
    session.commit()


@pytest.mark.filterwarnings(
    "ignore:'iter_groups' is expected to return 4 items tuple "
    "since wtforms 3.1create_models, this "
    "will be mandatory in wtforms 3.2:DeprecationWarning",
)
def test_model(
    app: Any, engine: Any, admin: Any, sqlmodel_base: type[SQLModel]
) -> None:
    with app.app_context():
        Model1, _ = create_models(engine, sqlmodel_base)

        with Session(engine) as db_sesion:
            view = CustomModelView(Model1, db_sesion)
            admin.add_view(view)

        assert view.model == Model1
        assert view.name == "Model1"
        assert view.endpoint == "model1"

        assert view._primary_key == "id"

        assert "test1" in view._sortable_columns
        assert "test2" in view._sortable_columns
        assert "test3" in view._sortable_columns
        assert "test4" in view._sortable_columns

        assert view._create_form_class is not None
        assert view._edit_form_class is not None
        assert not view._search_supported
        assert view._filters is None

        # Verify form fields
        assert view._create_form_class.test1.field_class == fields.StringField
        assert view._create_form_class.test2.field_class == fields.StringField
        assert view._create_form_class.test3.field_class == fields.TextAreaField
        assert view._create_form_class.test4.field_class == fields.TextAreaField
        assert view._create_form_class.email_field.field_class == fields.StringField
        assert view._create_form_class.choice_field.field_class == Select2Field
        assert view._create_form_class.enum_field.field_class == Select2Field
        assert view._create_form_class.sqla_utils_choice.field_class == Select2Field
        assert view._create_form_class.sqla_utils_enum.field_class == Select2Field
        assert (
            view._create_form_class.sqla_utils_arrow.field_class == AdminDateTimeField
        )
        assert view._create_form_class.sqla_utils_uuid.field_class == fields.StringField
        assert view._create_form_class.sqla_utils_url.field_class == fields.StringField
        assert (
            view._create_form_class.sqla_utils_ip_address.field_class
            == fields.StringField
        )
        assert (
            view._create_form_class.sqla_utils_currency.field_class
            == fields.StringField
        )
        assert (
            view._create_form_class.sqla_utils_color.field_class == fields.StringField
        )

        # Make test client
        client: Any = app.test_client()
        # Check that we can retrieve a list view
        rv = client.get("/admin/model1/")
        assert rv.status_code == 200

        # Check that we can retrieve a 'create' view
        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        # Create a new record
        uuid_obj: uuid.UUID = uuid.uuid4()
        rv = client.post(
            "/admin/model1/new/",
            data=dict(
                test1="test1large",
                test2="test2",
                time_field=time(0, 0, 0),
                email_field="Test@TEST.com",
                choice_field="choice-1",
                enum_field="model1_v1",
                sqla_utils_choice="choice-1",
                sqla_utils_enum=1,
                sqla_utils_arrow="2018-10-27 14:17:00",
                sqla_utils_uuid=str(uuid_obj),
                sqla_utils_url="http://www.example.com",
                sqla_utils_ip_address="127.0.0.1",
                sqla_utils_currency="USD",
                sqla_utils_color="#f0f0f0",
            ),
        )
        assert rv.status_code == 302, rv.data.decode()

        # Check that the new record was persisted
        with Session(engine) as db_session:
            model = db_session.exec(select(Model1)).scalars().first()
            assert model.test1 == "test1large"
            assert model.test2 == "test2"
            assert model.test3 is None
            assert model.test4 is None
            assert model.email_field == "test@test.com"
            assert model.choice_field == "choice-1"
            assert model.enum_field == "model1_v1"
            assert model.sqla_utils_choice == "choice-1"
            assert model.sqla_utils_enum.value == 1
            assert model.sqla_utils_arrow == arrow.get("2018-10-27 14:17:00")
            assert model.sqla_utils_uuid == uuid_obj
            assert model.sqla_utils_url == "http://www.example.com"
            assert str(model.sqla_utils_ip_address) == "127.0.0.1"
            assert str(model.sqla_utils_currency) == "USD"
            assert model.sqla_utils_color.hex == "#f0f0f0"

            # Check that the new record shows up on the list view
            rv = client.get("/admin/model1/")
            assert rv.status_code == 200
            assert "test1large" in rv.data.decode("utf-8")

            # Check that we can retrieve an edit view
            url = f"/admin/model1/edit/?id={model.id}"
            rv = client.get(url)
            assert rv.status_code == 200

            # Verify that midnight does not show as blank
            assert "00:00:00" in rv.data.decode("utf-8")

            # Edit the record
            new_uuid_obj: uuid.UUID = uuid.uuid4()
            rv = client.post(
                url,
                data=dict(
                    test1="test1small",
                    test2="test2large",
                    email_field="Test2@TEST.com",
                    choice_field="__None",
                    enum_field="__None",
                    sqla_utils_choice="__None",
                    sqla_utils_enum="__None",
                    sqla_utils_arrow="",
                    sqla_utils_uuid=str(new_uuid_obj),
                    sqla_utils_url="",
                    sqla_utils_ip_address="",
                    sqla_utils_currency="",
                    sqla_utils_color="",
                ),
            )
            assert rv.status_code == 302

            # Refresh the model
            db_session.refresh(model)

            # Check that the changes were persisted
            assert model.test1 == "test1small"
            assert model.test2 == "test2large"
            assert model.test3 is None
            assert model.test4 is None
            assert model.email_field == "test2@test.com"
            assert model.choice_field is None
            assert model.enum_field is None
            assert model.sqla_utils_choice is None
            assert model.sqla_utils_enum is None
            assert model.sqla_utils_arrow is None
            assert model.sqla_utils_uuid == new_uuid_obj
            assert model.sqla_utils_url is None
            assert model.sqla_utils_ip_address is None
            assert model.sqla_utils_currency is None
            assert model.sqla_utils_color is None

            # Check that the model can be deleted
            url = f"/admin/model1/delete/?id={model.id}"
            rv = client.post(url)
            assert rv.status_code == 302
            count = db_session.exec(select(func.count()).select_from(Model1)).scalar()
            assert count == 0


@pytest.mark.xfail(raises=Exception)
def test_no_pk(app: Any, engine: Any, admin: Any) -> None:
    """Test that models without primary keys raise an exception"""
    sqlmodel_class = sqlmodel_base()  # init to clear registry

    class Model(sqlmodel_class, table=True):
        test: Optional[int] = Field(default=None)

    with app.app_context():
        with Session(engine) as db_session:
            view = CustomModelView(Model, db_session)
            admin.add_view(view)


def test_editable_list_special_pks(app: Any, engine: Any, admin: Any) -> None:
    """Tests editable list view + a primary key with special characters"""
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class Model1(sqlmodel_class, table=True):
            model_config = {"extra": "allow"}  # Allow extra fields
            id: Optional[str] = Field(
                default=None, sa_column=(Column(String(20), primary_key=True))
            )
            val1: Optional[str] = Field(default=None, sa_column=(Column(String(20))))

        sqlmodel_class.metadata.create_all(bind=engine)
        with Session(engine) as db_session:
            view = CustomModelView(Model1, db_session, column_editable_list=["val1"])
            admin.add_view(view)

            db_session.add(Model1(id="1-1", val1="test1"))
            db_session.add(Model1(id="1-5", val1="test2"))
            db_session.commit()

        client: Any = app.test_client()

        # Form - Test basic in-line edit functionality
        rv = client.post(
            "/admin/model1/ajax/update/",
            data={
                "list_form_pk": "1-1",
                "val1": "change-success-1",
            },
        )
        data = rv.data.decode("utf-8")
        assert "Record was successfully saved." == data

        # ensure the value has changed
        rv = client.get("/admin/model1/")
        data = rv.data.decode("utf-8")
        assert "change-success-1" in data


def test_hybrid_property(app: Any, engine: Any, admin: Any) -> None:
    pass


def test_computed_property(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class Model1(sqlmodel_class, table=True):
            model_config = {"extra": "allow"}  # Allow extra fields

            id: Optional[int] = Field(
                default=None, sa_column=(Column(Integer(), primary_key=True))
            )
            name: Optional[str] = Field(default=None, sa_column=(Column(String)))
            width: Optional[int] = Field(default=None, sa_column=(Column(Integer)))
            height: Optional[int] = Field(default=None, sa_column=(Column(Integer)))

            @computed_field
            @property
            def number_of_pixels(self) -> int:
                return (self.width or 0) * (self.height or 0)

            @computed_field
            @property
            def number_of_pixels_str(self) -> str:
                return str(self.number_of_pixels)

        # Function to check if a field is a computed property
        def is_computed_property(model_class: type[SQLModel], field_name: str) -> bool:
            attr = getattr(model_class, field_name, None)
            return isinstance(attr, property)

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            assert is_computed_property(Model1, "number_of_pixels")
            assert is_computed_property(Model1, "number_of_pixels_str")
            assert not is_computed_property(Model1, "height")
            assert not is_computed_property(Model1, "width")

            db_session.add(Model1(id=1, name="test_row_1", width=25, height=25))
            db_session.add(Model1(id=2, name="test_row_2", width=10, height=10))
            db_session.commit()

            client: Any = app.test_client()

            view = CustomModelView(
                Model1,
                db_session,
                column_default_sort="number_of_pixels",
                column_filters=[
                    filters.IntGreaterFilter(
                        Model1.number_of_pixels, "Number of Pixels"
                    )
                ],
                column_searchable_list=[
                    "number_of_pixels_str",
                ],
            )
            admin.add_view(view)

        # filters - hybrid_property integer - greater
        rv = client.get("/admin/model1/?flt0_0=600")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test_row_1" in data
        assert "test_row_2" not in data

        # sorting
        rv = client.get("/admin/model1/?sort=0")
        assert rv.status_code == 200

        _, data = view.get_list(0, None, None, None, None)

        assert len(data) == 2
        assert data[0].name == "test_row_2"
        assert data[1].name == "test_row_1"

        # searching
        rv = client.get("/admin/model1/?search=100")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test_row_2" in data
        assert "test_row_1" not in data


# def test_hybrid_property_nested(app, db, admin):
#     with app.app_context():

#         class Model1(db.Model):
#             id = db.Column(db.Integer, primary_key=True)
#             firstname = db.Column(db.String)
#             lastname = db.Column(db.String)

#             @hybrid_property
#             def fullname(self):
#                 return f"{self.firstname} {self.lastname}"

#         class Model2(db.Model):
#             id = db.Column(db.Integer, primary_key=True)
#             name = db.Column(db.String)
#             owner_id = db.Column(
#                 db.Integer, db.ForeignKey("model1.id", ondelete="CASCADE")
#             )
#             owner = db.relationship(
#                 "Model1", backref=db.backref("tiles"), uselist=False
#             )

#         db.create_all()

#         assert tools.is_hybrid_property(Model2, "owner.fullname")
#         assert not tools.is_hybrid_property(Model2, "owner.firstname")

#         db.session.add(Model1(id=1, firstname="John", lastname="Dow"))
#         db.session.add(Model1(id=2, firstname="Jim", lastname="Smith"))
#         db.session.add(Model2(id=1, name="pencil", owner_id=1))
#         db.session.add(Model2(id=2, name="key", owner_id=1))
#         db.session.add(Model2(id=3, name="map", owner_id=2))
#         db.session.commit()

#         client: Any = app.test_client()

#         view = CustomModelView(
#             Model2,
#             db.session,
#             column_list=("id", "name", "owner.fullname"),
#             column_default_sort="id",
#         )
#         admin.add_view(view)

#         rv = client.get("/admin/model2/")
#         assert rv.status_code == 200
#         data = rv.data.decode("utf-8")
#         assert "John Dow" in data
#         assert "Jim Smith" in data


def test_non_int_pk(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class Model(sqlmodel_class, table=True):
            id: Optional[str] = Field(sa_column=(Column(String, primary_key=True)))
            test: Optional[str] = Field(sa_column=(Column(String)))

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            view = CustomModelView(Model, db_session, form_columns=["id", "test"])
            admin.add_view(view)

        client: Any = app.test_client()

        rv = client.get("/admin/model/")
        assert rv.status_code == 200

        rv = client.post("/admin/model/new/", data=dict(id="test1", test="test2"))
        assert rv.status_code == 302

        rv = client.get("/admin/model/")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test1" in data

        rv = client.get("/admin/model/edit/?id=test1")
        assert rv.status_code == 200
        data = rv.data.decode("utf-8")
        assert "test2" in data


def test_form_columns(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class Model(sqlmodel_class, table=True):
            id: Optional[str] = Field(sa_column=Column(String, primary_key=True))
            int_field: Optional[int] = Field(sa_column=Column(Integer))
            datetime_field: Optional[datetime] = Field(sa_column=Column(DateTime))
            text_field: Optional[str] = Field(sa_column=Column(UnicodeText))
            excluded_column: Optional[str] = Field(sa_column=Column(String))

            # relationship to ChildModel
            children: list["ChildModel"] = Relationship(back_populates="model")

        class ChildModel(sqlmodel_class, table=True):
            class EnumChoices(enum.Enum):
                first = 1
                second = 2

            id: Optional[str] = Field(sa_column=(Column(String, primary_key=True)))
            model_id: Optional[int] = Field(default=None, foreign_key="model.id")
            model: Optional[Model] = Relationship(back_populates="children")
            enum_field: Optional[str] = Field(
                sa_column=Column(
                    SQLAEnum("model1_v1", "model1_v2", name="enum_field_enum"),
                    nullable=True,
                )
            )
            choice_field: Optional[str] = Field(default=None)
            sqla_utils_choice: Optional[str] = Field(
                sa_column=(
                    Column(
                        ChoiceType(
                            [
                                ("choice-1", "First choice"),
                                ("choice-2", "Second choice"),
                            ]
                        )
                    )
                )
            )
            sqla_utils_enum: Optional[EnumChoices] = Field(
                sa_column=Column(ChoiceType(EnumChoices, impl=Integer()))
            )

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            view1 = CustomModelView(
                Model,
                db_session,
                endpoint="view1",
                form_columns=("int_field", "text_field"),
            )
            view2 = CustomModelView(
                Model,
                db_session,
                endpoint="view2",
                form_excluded_columns=("excluded_column",),
            )
            view3 = CustomModelView(ChildModel, db_session, endpoint="view3")

            form1: Any = view1.create_form()
            form2: Any = view2.create_form()
            form3: Any = view3.create_form()

            assert "int_field" in form1._fields
            assert "text_field" in form1._fields
            assert "datetime_field" not in form1._fields
            assert "excluded_column" not in form2._fields

            # check that relation shows up as a query select
            assert type(form3.model).__name__ == "QuerySelectField"

            # check that select field is rendered if form_choices were specified
            assert type(form3.choice_field).__name__ == "Select2Field"

            # check that select field is rendered for enum fields
            assert type(form3.enum_field).__name__ == "Select2Field"

            # check that sqlalchemy_utils field types are handled appropriately
            assert type(form3.sqla_utils_choice).__name__ == "Select2Field"
            assert type(form3.sqla_utils_enum).__name__ == "Select2Field"

            # test form_columns with model objects
            view4: CustomModelView = CustomModelView(
                Model, db_session, endpoint="view1", form_columns=[Model.int_field]
            )
            form4: Any = view4.create_form()
            assert "int_field" in form4._fields


def test_form_args(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class Model(sqlmodel_class, table=True):
            id: Optional[int] = Field(
                default=None, sa_column=(Column(String, primary_key=True))
            )
            test: str = Field(sa_column=(Column(String, nullable=False)))

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            shared_form_args: dict[str, dict[str, list[Any]]] = {
                "test": {"validators": [validators.Regexp("test")]}
            }

            view = CustomModelView(Model, db_session, form_args=shared_form_args)
            admin.add_view(view)

            create_form: Any = view.create_form()
            assert len(create_form.test.validators) == 2

            # ensure shared field_args don't create duplicate validators
            edit_form: Any = view.edit_form()
            assert len(edit_form.test.validators) == 2


def test_form_override(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class Model(sqlmodel_class, table=True):
            id: Optional[str] = Field(sa_column=(Column(String, primary_key=True)))
            test: Optional[str] = Field(sa_column=(Column(String)))

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            view1 = CustomModelView(Model, db_session, endpoint="view1")
            view2 = CustomModelView(
                Model,
                db_session,
                endpoint="view2",
                form_overrides=dict(test=fields.FileField),
            )
            admin.add_view(view1)
            admin.add_view(view2)

            assert view1._create_form_class.test.field_class == fields.StringField
            assert view2._create_form_class.test.field_class == fields.FileField


def test_form_onetoone(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()

        class Model1(sqlmodel_class, table=True):
            id: Optional[int] = Field(
                default=None, sa_column=(Column(Integer, primary_key=True))
            )
            test: Optional[str] = Field(sa_column=(Column(String)))
            # Use a string forward reference
            model2: Optional["Model2"] = Relationship(back_populates="model1")

        class Model2(sqlmodel_class, table=True):
            id: Optional[int] = Field(
                default=None, sa_column=(Column(Integer, primary_key=True))
            )

            model1_id: Optional[int] = Field(default=None, foreign_key="model1.id")
            model1: Optional[Model1] = Relationship(back_populates="model2")

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            view1 = CustomModelView(Model1, db_session, endpoint="view1")
            view2 = CustomModelView(Model2, db_session, endpoint="view2")
            admin.add_view(view1)
            admin.add_view(view2)

            model1 = Model1(test="test")
            model2 = Model2(model1=model1)
            db_session.add(model1)
            db_session.add(model2)
            db_session.commit()

            assert model1.model2 == model2
            assert model2.model1 == model1

            assert not view1._create_form_class.model2.field_class.widget.multiple
            assert not view2._create_form_class.model1.field_class.widget.multiple


def test_relations() -> None:
    # TODO: test relations
    pass


def test_extra_field_order(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        Model1, _ = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model1,
                db_session,
                form_columns=("extra_field", "test1"),
                form_extra_fields={"extra_field": fields.StringField("Extra Field")},
            )
            admin.add_view(view)

        client: Any = app.test_client()

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200

        # Check presence and order
        data = rv.data.decode("utf-8")
        pos1 = data.find("Extra Field")
        pos2 = data.find("Test1")
        assert pos2 > pos1


@pytest.mark.parametrize(
    "locale, expect_text",
    (
        ("en", "Home"),
        ("cs", "Domů"),
        ("de", "Start"),
        ("es", "Inicio"),
        ("fa", "خانه"),
        ("fr", "Accueil"),
        ("pt", "Início"),
        ("ru", "Главная"),
        ("pa", "ਹੋਮ"),
        ("zh_CN", "首页"),
        ("zh_TW", "首頁"),
    ),
)
@pytest.mark.filterwarnings(
    "ignore:'iter_groups' is expected to return 4 items tuple since wtforms 3.1, this "
    "will be mandatory in wtforms 3.2:DeprecationWarning",
)
@flask_babel_test_decorator
def test_modelview_localization(
    request: Any, app: Any, locale: str, expect_text: str
) -> None:
    # We need to configure the default Babel locale _before_ the `babel` fixture is
    # initialised, so we have to use `request.getfixturevalue` to pull the fixture
    # within the test function rather than the test signature. The `admin` fixture
    # pulls in the `babel` fixture, which will then use the configuration here.
    app.config["BABEL_DEFAULT_LOCALE"] = locale
    engine = request.getfixturevalue("engine")
    admin = request.getfixturevalue("admin")
    _sqlmodel_class = sqlmodel_base()  # init to clear registry

    with app.app_context():
        Model1, _ = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model1,
                db_session,
                column_filters=[
                    "test1",
                    "bool_field",
                    "date_field",
                    "datetime_field",
                    "time_field",
                ],
            )

            admin.add_view(view)

        client: Any = app.test_client()

        rv = client.get("/admin/model1/")
        assert expect_text in rv.text
        assert rv.status_code == 200

        rv = client.get("/admin/model1/new/")
        assert rv.status_code == 200


# @flask_babel_test_decorator
# def test_modelview_named_filter_localization(request, app):
#     # We need to configure the default Babel locale _before_ the `babel` fixture is
#     # initialised, so we have to use `request.getfixturevalue` to pull the fixture
#     # within the test function rather than the test signature. The `admin` fixture
#     # pulls in the `babel` fixture, which will then use the configuration here.
#     app.config["BABEL_DEFAULT_LOCALE"] = "de"
#     db = request.getfixturevalue("db")
#     _ = request.getfixturevalue("admin")

#     with app.app_context():
#         Model1, _ = create_models(db)

#         view = CustomModelView(
#             Model1,
#             db.session,
#             named_filter_urls=True,
#             column_filters=["test1"],
#         )

#         filters = view.get_filters()
#         flt = filters[2]
#         with app.test_request_context():
#             flt_name = view.get_filter_arg(2, flt)
#         assert "test1_equals" == flt_name


def test_custom_form_base(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():

        class TestForm(form.BaseForm):
            pass

        Model1, _ = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(Model1, db_session, form_base_class=TestForm)
            admin.add_view(view)

        assert hasattr(view._create_form_class, "test1")

        create_form: Any = view.create_form()
        assert isinstance(create_form, TestForm)


def test_ajax_fk(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        Model1, Model2 = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model2,
                db_session,
                url="view",
                form_ajax_refs={"model1": {"fields": ("test1", "test2")}},
            )
            admin.add_view(view)

            assert "model1" in view._form_ajax_refs
            model = Model1(test1="first")
            model2 = Model1(test1="foo", test2="bar")
            db_session.add_all([model, model2])
            db_session.commit()

            # Check loader
            loader = view._form_ajax_refs["model1"]
            mdl = loader.get_one(model.id)
            assert mdl.test1 == model.test1

            items = loader.get_list("fir")
            assert len(items) == 1
            assert items[0].id == model.id

            items = loader.get_list("bar")
            assert len(items) == 1
            assert items[0].test1 == "foo"

            # Check form generation
            form: Any = view.create_form()
            assert form.model1.__class__.__name__ == "AjaxSelectField"

            with app.test_request_context("/admin/view/"):
                assert 'value=""' not in form.model1()

                form.model1.data = model
                assert (
                    f'data-json="[{model.id}, &quot;first&quot;]"' in form.model1()
                    or f'data-json="[{model.id}, &#34;first&#34;]"' in form.model1()
                )
                assert 'value="1"' in form.model1()

            # Check querying
            client: Any = app.test_client()

            req = client.get("/admin/view/ajax/lookup/?name=model1&query=foo")
            assert req.data.decode("utf-8") == f'[[{model2.id}, "foo"]]'

            # Check submitting
            req = client.post("/admin/view/new/", data={"model1": as_unicode(model.id)})
            # Get the created Model2 instance - it should have id=1 since it's the first
            mdl = db_session.get(Model2, 1)

            assert mdl is not None
            assert mdl.model1_id == model.id
            # Get the related model1 through a separate query since relationships
            # may not be auto-loaded
            related_model1 = db_session.get(Model1, mdl.model1_id)
            assert related_model1 is not None
            assert related_model1.id == model.id
            assert related_model1.test1 == "first"


def test_ajax_fk_multi(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class M2M(sqlmodel_class, table=True):
            model1_id: Optional[int] = Field(
                default=None, foreign_key="model1.id", primary_key=True
            )
            model2_id: Optional[int] = Field(
                default=None, foreign_key="model2.id", primary_key=True
            )

        class Model1(sqlmodel_class, table=True):
            __tablename__ = "model1"

            id: Optional[int] = Field(default=None, primary_key=True)
            name: Optional[str] = Field(default=None)

            model2: list["Model2"] = Relationship(
                back_populates="model1", link_model=M2M
            )

            def __str__(self) -> str:
                return self.name or ""

        class Model2(sqlmodel_class, table=True):
            __tablename__ = "model2"

            id: Optional[int] = Field(default=None, primary_key=True)
            name: Optional[str] = Field(default=None, max_length=20)

            model1: list[Model1] = Relationship(back_populates="model2", link_model=M2M)

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            view = CustomModelView(
                Model2,
                db_session,
                url="view",
                form_ajax_refs={"model1": {"fields": ["name"]}},
            )
            admin.add_view(view)

            assert "model1" in view._form_ajax_refs

            model = Model1(name="first")
            db_session.add_all([model, Model1(name="foo")])
            db_session.commit()

            # Check form generation
            form: Any = view.create_form()
            assert form.model1.__class__.__name__ == "AjaxSelectMultipleField"

            with app.test_request_context("/admin/view/"):
                assert 'data-json="[]"' in form.model1()

                form.model1.data = [model]
                assert (
                    'data-json="[[1, &quot;first&quot;]]"' in form.model1()
                    or 'data-json="[[1, &#34;first&#34;]]"' in form.model1()
                )

            # Check submitting
            client: Any = app.test_client()
            client.post("/admin/view/new/", data={"model1": as_unicode(model.id)})
            # Get the created Model2 instance - it should have id=1 since it's the first
            mdl = db_session.get(Model2, 1)

            assert mdl is not None
            # For many-to-many relationships, the model1 list should have been populated
            assert mdl.model1 is not None
            assert len(mdl.model1) == 1


def test_safe_redirect(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        Model1, _ = create_models(engine)
        with Session(engine) as db_session:
            view = CustomModelView(Model1, db_session)
            admin.add_view(view)

        client: Any = app.test_client()

        rv = client.post(
            "/admin/model1/new/?url=http://localhost/admin/model2view/",
            data=dict(
                test1="test1large",
                test2="test2",
                _continue_editing="Save and Continue Editing",
            ),
        )

        assert rv.status_code == 302

        # werkzeug 2.1.0+ now returns *relative* redirect/location by default.
        expected = "/admin/model1/edit/"

        # handle old werkzeug (or if relative location is disabled via
        # `autocorrect_location_header=True`)
        if (
            not hasattr(rv, "autocorrect_location_header")
            or rv.autocorrect_location_header
        ):
            expected = "http://localhost" + expected

        assert rv.location.startswith(expected)
        assert "url=http://localhost/admin/model2view/" in rv.location
        assert "id=1" in rv.location

        rv = client.post(
            "/admin/model1/new/?url=http://google.com/evil/",
            data=dict(
                test1="test1large",
                test2="test2",
                _continue_editing="Save and Continue Editing",
            ),
        )

        assert rv.status_code == 302
        assert rv.location.startswith(expected)
        assert "url=/admin/model1/" in rv.location
        assert "id=2" in rv.location


def test_simple_list_pager(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        Model1, _ = create_models(engine)
        with Session(engine) as db_session:

            class TestModelView(CustomModelView):
                simple_list_pager = True

                def get_count_query(self) -> None:
                    raise AssertionError()

            view = TestModelView(Model1, db_session)
            admin.add_view(view)

            count, data = view.get_list(0, None, None, None, None)
            assert count is None


def test_customising_page_size(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        M1, _ = create_models(engine)
        with Session(engine) as db_session:
            db_session.add_all(
                [M1(test1=str(f"instance-{x + 1:03d}")) for x in range(101)]
            )
            db_session.commit()

            view1 = CustomModelView(
                M1, db_session, endpoint="view1", page_size=20, can_set_page_size=False
            )
            admin.add_view(view1)

            view2 = CustomModelView(
                M1, db_session, endpoint="view2", page_size=5, can_set_page_size=False
            )
            admin.add_view(view2)

            view3 = CustomModelView(
                M1, db_session, endpoint="view3", page_size=20, can_set_page_size=True
            )
            admin.add_view(view3)

            view4 = CustomModelView(
                M1,
                db_session,
                endpoint="view4",
                page_size=5,
                page_size_options=(5, 10, 15),
                can_set_page_size=True,
            )
            admin.add_view(view4)

        client: Any = app.test_client()

        rv = client.get("/admin/view1/")
        assert "instance-020" in rv.text
        assert "instance-021" not in rv.text

        # `can_set_page_size=False`, so only the default of 20 is available.
        rv = client.get("/admin/view1/?page_size=50")
        assert "instance-020" in rv.text
        assert "instance-021" not in rv.text

        # Check view2, which has `page_size=5` to change the default page size
        rv = client.get("/admin/view2/")
        assert "instance-005" in rv.text
        assert "instance-006" not in rv.text

        # Check view3, which has `can_set_page_size=True`
        rv = client.get("/admin/view3/")
        assert "instance-020" in rv.text
        assert "instance-021" not in rv.text

        rv = client.get("/admin/view3/?page_size=50")
        assert "instance-050" in rv.text
        assert "instance-051" not in rv.text

        rv = client.get("/admin/view3/?page_size=100")
        assert "instance-100" in rv.text
        assert "instance-101" not in rv.text

        # Invalid page sizes are reset to the default
        rv = client.get("/admin/view3/?page_size=1")
        assert "instance-020" in rv.text
        assert "instance-021" not in rv.text

        # Check view4, which has custom `page_size_options`
        rv = client.get("/admin/view4/")
        assert "instance-005" in rv.text
        assert "instance-006" not in rv.text

        # Invalid page sizes are reset to the default
        rv = client.get("/admin/view4/?page_size=1")
        assert "instance-005" in rv.text
        assert "instance-006" not in rv.text

        rv = client.get("/admin/view4/?page_size=10")
        assert "instance-010" in rv.text
        assert "instance-011" not in rv.text

        rv = client.get("/admin/view4/?page_size=15")
        assert "instance-015" in rv.text
        assert "instance-016" not in rv.text


def test_unlimited_page_size(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        M1, _ = create_models(engine)
        with Session(engine) as db_session:
            db_session.add_all(
                [
                    M1(test1="1"),
                    M1(test1="2"),
                    M1(test1="3"),
                    M1(test1="4"),
                    M1(test1="5"),
                    M1(test1="6"),
                    M1(test1="7"),
                    M1(test1="8"),
                    M1(test1="9"),
                    M1(test1="10"),
                    M1(test1="11"),
                    M1(test1="12"),
                    M1(test1="13"),
                    M1(test1="14"),
                    M1(test1="15"),
                    M1(test1="16"),
                    M1(test1="17"),
                    M1(test1="18"),
                    M1(test1="19"),
                    M1(test1="20"),
                    M1(test1="21"),
                ]
            )
            db_session.commit()

            view = CustomModelView(M1, db_session)

        # test 0 as page_size
        _, data = view.get_list(0, None, None, None, None, execute=True, page_size=0)
        assert len(data) == 21

        # test False as page_size
        _, data = view.get_list(
            0, None, None, None, None, execute=True, page_size=False
        )
        assert len(data) == 21


def test_advanced_joins(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class Model1(sqlmodel_class, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            val1: Optional[str] = Field(default=None, max_length=20)
            test: Optional[str] = Field(default=None, max_length=20)

            model2: list["Model2"] = Relationship(back_populates="model1")

        class Model2(sqlmodel_class, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            val2: Optional[str] = Field(default=None, max_length=20)
            model1_id: Optional[int] = Field(default=None, foreign_key="model1.id")

            model1: Optional[Model1] = Relationship(back_populates="model2")
            model3: list["Model3"] = Relationship(back_populates="model2")

        class Model3(sqlmodel_class, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            val2: Optional[str] = Field(default=None, max_length=20)
            model2_id: Optional[int] = Field(default=None, foreign_key="model2.id")

            model2: Optional[Model2] = Relationship(back_populates="model3")

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            view1 = CustomModelView(Model1, db_session)
            admin.add_view(view1)

            view2 = CustomModelView(Model2, db_session)
            admin.add_view(view2)

            view3 = CustomModelView(Model3, db_session)
            admin.add_view(view3)

        # Test joins
        attr, path = tools.get_field_with_path(Model2, "model1.val1")
        assert attr == Model1.val1
        assert path == [Model2.model1]

        attr, path = tools.get_field_with_path(Model1, "model2.val2")
        assert attr == Model2.val2
        assert id(path[0]) == id(Model1.model2)

        attr, path = tools.get_field_with_path(Model3, "model2.model1.val1")
        assert attr == Model1.val1
        assert path == [Model3.model2, Model2.model1]

        # Test how joins are applied
        query = view3.get_query()

        joins = {}
        q1, joins, alias = view3._apply_path_joins(query, joins, path)
        assert (True, Model3.model2) in joins
        assert (True, Model2.model1) in joins
        assert alias is not None

        # Check if another join would use same path
        attr, path = tools.get_field_with_path(Model2, "model1.test")
        q2, joins, alias = view2._apply_path_joins(query, joins, path)

        assert len(joins) == 2

        if hasattr(q2, "_join_entities"):
            for p in q2._join_entities:
                assert p in q1._join_entities

        assert alias is not None

        # Check if normal properties are supported by tools.get_field_with_path
        attr, path = tools.get_field_with_path(Model2, Model1.test)
        assert attr == Model1.test
        assert path == [Model1.__table__]

        q3, joins, alias = view2._apply_path_joins(view2.get_query(), joins, path)
        assert len(joins) == 3
        assert alias is None


def test_multipath_joins(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class Model1(sqlmodel_class, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            val1: Optional[str] = Field(default=None, max_length=20)
            test: Optional[str] = Field(default=None, max_length=20)

            first_refs: list["Model2"] = Relationship(
                back_populates="first",
                sa_relationship_kwargs={"foreign_keys": "[Model2.first_id]"},
            )
            second_refs: list["Model2"] = Relationship(
                back_populates="second",
                sa_relationship_kwargs={"foreign_keys": "[Model2.second_id]"},
            )

        class Model2(sqlmodel_class, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            val2: Optional[str] = Field(default=None, max_length=20)

            first_id: Optional[int] = Field(default=None, foreign_key="model1.id")
            second_id: Optional[int] = Field(default=None, foreign_key="model1.id")

            first: Optional[Model1] = Relationship(
                back_populates="first_refs",
                sa_relationship_kwargs={"foreign_keys": "[Model2.first_id]"},
            )
            second: Optional[Model1] = Relationship(
                back_populates="second_refs",
                sa_relationship_kwargs={"foreign_keys": "[Model2.second_id]"},
            )

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            view = CustomModelView(Model2, db_session, filters=["first.test"])
            admin.add_view(view)

        client: Any = app.test_client()

        rv = client.get("/admin/model2/")
        assert rv.status_code == 200


# SQLModel does not support bindings
# This is a wrkaoround that creates both Models
# in the other engine
def test_different_bind_joins(request: Any, app: Any, engine: Any) -> None:
    app.config["SQLALCHEMY_BINDS"] = {"other": "sqlite:///"}

    admin = request.getfixturevalue("admin")
    sqlmodel_class = sqlmodel_base()  # init to clear registry
    with app.app_context():
        other_db_uri = app.config["SQLALCHEMY_BINDS"]["other"]
        other_engine = create_engine(other_db_uri)

        class Model1(sqlmodel_class, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            val1: Optional[str] = Field(default=None, max_length=20)

        class Model2(sqlmodel_class, table=True):
            __tablename__ = "model2"

            id: Optional[int] = Field(default=None, primary_key=True)
            val1: Optional[str] = Field(default=None, max_length=20)

            first_id: Optional[int] = Field(default=None, foreign_key="model1.id")
            first: Optional[Model1] = Relationship()

        sqlmodel_class.metadata.create_all(engine, tables=[Model1.__table__])
        other_metadata = sqlmodel_class.metadata
        other_metadata.create_all(
            other_engine,
            tables=[Model1.__table__, Model2.__table__],
        )
        with Session(other_engine) as db_session:
            view = CustomModelView(Model2, db_session)
            admin.add_view(view)

        client: Any = app.test_client()

        rv = client.get("/admin/model2/")
        assert rv.status_code == 200


def test_model_default(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        _, Model2 = create_models(engine)

        class ModelView(CustomModelView):
            pass

        with Session(engine) as db_session:
            view = ModelView(Model2, db_session)
            admin.add_view(view)

        client: Any = app.test_client()
        rv = client.post("/admin/model2/new/", data=dict())
        assert b"This field is required" not in rv.data


def test_export_csv(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        with Session(engine) as db_session:
            Model1, Model2 = create_models(engine)

            for _x in range(5):
                fill_db(db_session, Model1, Model2)

        with Session(engine) as db_session:
            view1 = CustomModelView(
                Model1,
                db_session,
                can_export=True,
                column_list=["test1", "test2"],
                export_max_rows=2,
                endpoint="row_limit_2",
            )
            admin.add_view(view1)
            view2 = CustomModelView(
                Model1,
                db_session,
                can_export=True,
                column_list=["test1", "test2"],
                endpoint="no_row_limit",
            )
            admin.add_view(view2)

        client: Any = app.test_client()

        # test export_max_rows
        rv = client.get("/admin/row_limit_2/export/csv/")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert (
            "Test1,Test2\r\n"
            + "test1_val_1,test2_val_1\r\n"
            + "test1_val_2,test2_val_2\r\n"
            == data
        )

        # test row limit without export_max_rows
        rv = client.get("/admin/no_row_limit/export/csv/")
        data = rv.data.decode("utf-8")
        assert rv.status_code == 200
        assert len(data.splitlines()) > 21


STRING_CONSTANT = "Anyway, here's Wonderwall"


def test_string_null_behavior(app: Any, engine: Any, admin: Any) -> None:
    with app.app_context():
        sqlmodel_class = sqlmodel_base()  # init to clear registry

        class StringTestModel(sqlmodel_class, table=True):
            id: Optional[int] = Field(
                default=None, sa_column=(Column(Integer, primary_key=True))
            )
            test_no: int = Field(sa_column=(Column(Integer, nullable=False)))
            string_field: Optional[int] = Field(sa_column=(Column(String)))
            string_field_nonull: str = Field(sa_column=(Column(String, nullable=False)))
            string_field_nonull_default: str = Field(
                sa_column=(Column(String, nullable=False, default=""))
            )
            text_field: Optional[str] = Field(sa_column=(Column(Text)))
            text_field_nonull: str = Field(sa_column=(Column(Text, nullable=False)))
            text_field_nonull_default: str = Field(
                sa_column=(Column(Text, nullable=False, default=""))
            )

        sqlmodel_class.metadata.create_all(engine)
        with Session(engine) as db_session:
            view = CustomModelView(StringTestModel, db_session)
            admin.add_view(view)

            client: Any = app.test_client()

            valid_params = {
                "test_no": 1,
                "string_field_nonull": STRING_CONSTANT,
                "text_field_nonull": STRING_CONSTANT,
            }
            rv = client.post("/admin/stringtestmodel/new/", data=valid_params)
            assert rv.status_code == 302

            # Assert on defaults
            valid_inst = (
                db_session.exec(
                    select(StringTestModel).filter(StringTestModel.test_no == 1)
                )
                .scalars()
                .one()
            )
            assert valid_inst.string_field is None
            assert valid_inst.string_field_nonull == STRING_CONSTANT
            assert valid_inst.string_field_nonull_default == ""
            assert valid_inst.text_field is None
            assert valid_inst.text_field_nonull == STRING_CONSTANT
            assert valid_inst.text_field_nonull_default == ""

            # Assert that nulls are caught on the non-null fields
            invalid_string_field = {
                "test_no": 2,
                "string_field_nonull": None,
                "text_field_nonull": STRING_CONSTANT,
            }
            rv = client.post("/admin/stringtestmodel/new/", data=invalid_string_field)
            assert rv.status_code == 200
            assert b"This field is required." in rv.data
            result = db_session.exec(
                select(StringTestModel).where(StringTestModel.test_no == 2)
            ).all()

            assert result == []

            invalid_text_field = {
                "test_no": 3,
                "string_field_nonull": STRING_CONSTANT,
                "text_field_nonull": None,
            }
            rv = client.post("/admin/stringtestmodel/new/", data=invalid_text_field)
            assert rv.status_code == 200
            assert b"This field is required." in rv.data
            result = db_session.exec(
                select(StringTestModel).filter(StringTestModel.test_no == 3)
            ).all()

            assert result == []

            # Assert that empty strings are converted to None on nullable fields.
            empty_strings = {
                "test_no": 4,
                "string_field": "",
                "text_field": "",
                "string_field_nonull": STRING_CONSTANT,
                "text_field_nonull": STRING_CONSTANT,
            }
            rv = client.post("/admin/stringtestmodel/new/", data=empty_strings)
            assert rv.status_code == 302
            empty_string_inst = (
                db_session.exec(
                    select(StringTestModel).filter(StringTestModel.test_no == 4)
                )
                .scalars()
                .one()
            )

            assert empty_string_inst.string_field is None
            assert empty_string_inst.text_field is None


def test_primary_key_detection(app: Any, engine: Any, admin: Any) -> None:
    """Test that primary key detection works with sa_column fields"""
    with app.app_context():
        Model1, _ = create_models(engine)

        from flask_admin.contrib.sqlmodel import tools

        # Test get_model_fields detects primary key correctly
        fields = tools.get_model_fields(Model1)
        pk_fields = [f for f in fields if f.primary_key]
        assert len(pk_fields) == 1
        assert pk_fields[0].name == "id"

        # Test get_primary_key function
        pk = tools.get_primary_key(Model1)
        assert pk == "id"

        # Test has_multiple_pks
        assert not tools.has_multiple_pks(Model1)


def test_union_type_detection(app: Any, engine: Any, admin: Any) -> None:
    """Test that modern Python union types (str | None) are detected properly"""
    with app.app_context():
        Model1, _ = create_models(engine)

        with Session(engine) as db_session:
            view = CustomModelView(Model1, db_session)
            admin.add_view(view)

            # Test scaffold_sortable_columns detects union types
            sortable = view.scaffold_sortable_columns()

            # These should be detected as sortable (scalar | None types)
            assert "test1" in sortable  # str | None
            assert "test2" in sortable  # str | None
            assert "bool_field" in sortable  # str | bool
            assert "id" in sortable  # int | None

            # These should NOT be detected (non-scalar types)
            assert "model_extra" not in sortable  # dict type
            assert "model_fields_set" not in sortable  # set type


def test_field_type_info(app: Any, engine: Any, admin: Any) -> None:
    """Test field type information extraction"""
    with app.app_context():
        Model1, _ = create_models(engine)

        from flask_admin.contrib.sqlmodel import tools

        fields = tools.get_model_fields(Model1)
        field_dict = {f.name: f for f in fields}

        # Test basic field detection
        assert "id" in field_dict
        assert "test1" in field_dict
        assert "email_field" in field_dict

        # Test type information
        test1_field = field_dict["test1"]
        assert "str" in str(test1_field.type_)
        assert not test1_field.primary_key

        id_field = field_dict["id"]
        assert "int" in str(id_field.type_)
        assert id_field.primary_key
