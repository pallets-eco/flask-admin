"""
Shared test utilities for SQLModel tests.

This module provides common test utilities that are used across
multiple test modules in the SQLModel test suite.
"""

import enum
import uuid
from datetime import date
from datetime import datetime
from datetime import time
from typing import Optional

import arrow
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
from sqlmodel import Date
from sqlmodel import DateTime
from sqlmodel import Field
from sqlmodel import Float
from sqlmodel import Integer
from sqlmodel import Relationship
from sqlmodel import SQLModel
from sqlmodel import String
from sqlmodel import Text
from sqlmodel import Time

from flask_admin.contrib.sqlmodel import SQLModelView


class EnumChoices(enum.Enum):
    """Internal test enum for choice fields."""

    first = 1
    second = 2


class CustomModelView(SQLModelView):
    """Custom SQLModel view for testing with additional configuration."""

    def __init__(
        self,
        model,
        session,
        name=None,
        category=None,
        endpoint=None,
        url=None,
        **kwargs,
    ):
        for k, v in kwargs.items():
            setattr(self, k, v)

        super().__init__(model, session, name, category, endpoint, url)

    form_choices = {"choice_field": [("choice-1", "One"), ("choice-2", "Two")]}


def sqlmodel_base() -> type[SQLModel]:
    """Create a fresh SQLModel base class for each test
    to avoid class name conflicts."""
    # Create a fresh registry and metadata for complete isolation
    test_registry = registry()

    # Create a new SQLModel base class with its own registry
    class SQLModelCleanRegistry(SQLModel, registry=test_registry):
        pass

    return SQLModelCleanRegistry


def create_models(
    engine, sqlmodel_class: Optional[type[SQLModel]] = None
) -> tuple[type[SQLModel], type[SQLModel]]:
    """Create SQLModel models for testing with proper metadata handling."""
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

        def __unicode__(self):
            return self.test1

        def __str__(self):
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


def fill_db(session, Model1, Model2):
    """Fill database with test data."""
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


# Export only the utilities that are actually imported by test files
__all__ = [
    "CustomModelView",
    "create_models",
    "fill_db",
    "sqlmodel_base",
]
