import enum
import uuid
from typing import Optional

import arrow
from admin import db
from sqlalchemy import cast
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import sql
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ArrowType
from sqlalchemy_utils import ChoiceType
from sqlalchemy_utils import ColorType
from sqlalchemy_utils import CurrencyType
from sqlalchemy_utils import EmailType
from sqlalchemy_utils import IPAddressType
from sqlalchemy_utils import TimezoneType
from sqlalchemy_utils import URLType
from sqlalchemy_utils import UUIDType

AVAILABLE_USER_TYPES = [
    ("admin", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]


class EnumChoices(enum.Enum):
    first = 1
    second = 2


class User(db.Model):
    id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False), default=uuid.uuid4, primary_key=True
    )

    # use a regular string field, for which we can specify a list of available choices
    # later on
    type: Mapped[str] = mapped_column(String(100))

    # Fixed choices can be handled in a number of different ways:
    enum_choice_field: Mapped[Enum] = mapped_column(Enum(EnumChoices), nullable=True)  # type: ignore[var-annotated]
    sqla_utils_choice_field: Mapped[ChoiceType] = mapped_column(
        ChoiceType(AVAILABLE_USER_TYPES), nullable=True
    )
    sqla_utils_enum_choice_field: Mapped[ChoiceType] = mapped_column(
        ChoiceType(EnumChoices, impl=Integer()), nullable=True
    )

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))

    # Some sqlalchemy_utils data types (see https://sqlalchemy-utils.readthedocs.io/)
    email: Mapped[EmailType] = mapped_column(EmailType, unique=True, nullable=False)
    website: Mapped[URLType] = mapped_column(URLType)
    ip_address: Mapped[IPAddressType] = mapped_column(IPAddressType)
    currency: Mapped[CurrencyType] = mapped_column(
        CurrencyType, nullable=True, default=None
    )
    timezone: Mapped[TimezoneType] = mapped_column(TimezoneType(backend="pytz"))

    dialling_code: Mapped[int] = mapped_column(Integer())
    local_phone_number: Mapped[str] = mapped_column(String(10))

    featured_post_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "post.id",
            use_alter=True,
            name="fk_user_featured_post",
        ),
        nullable=True,
    )
    featured_post: Mapped["Post | None"] = relationship(
        "Post", foreign_keys=[featured_post_id]
    )

    @hybrid_property
    def phone_number(self):
        if self.dialling_code and self.local_phone_number:
            number = str(self.local_phone_number)
            return (
                f"+{self.dialling_code} ({number[0]}) {number[1:3]} "
                f"{number[3:6]} {number[6::]}"
            )
        return

    @phone_number.expression  # type: ignore[no-redef]
    def phone_number(cls):
        return sql.operators.ColumnOperators.concat(
            cast(cls.dialling_code, String), cls.local_phone_number
        )

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    def __repr__(self):
        return f"{self.id}: {self.__str__()}"


# Create M2M table
post_tags_table = Table(
    "post_tags",
    db.Model.metadata,
    Column("post_id", Integer, ForeignKey("post.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tag.id"), primary_key=True),
)


class Tag(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)

    def __str__(self):
        return f"{self.name}"


class Post(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[Date] = mapped_column(Date)

    # some sqlalchemy_utils data types (see https://sqlalchemy-utils.readthedocs.io/)
    background_color: Mapped[ColorType] = mapped_column(ColorType)
    created_at: Mapped[ArrowType] = mapped_column(ArrowType, default=arrow.utcnow)
    user_id: Mapped[UUIDType] = mapped_column(
        UUIDType(binary=False), ForeignKey(User.id)
    )

    user: Mapped[User] = relationship(User, foreign_keys=[user_id], backref="posts")
    tags: Mapped[list[Tag]] = relationship("Tag", secondary=post_tags_table)

    def __str__(self):
        return f"{self.title}"


class Tree(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))

    # recursive relationship
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tree.id"), nullable=True
    )
    parent: Mapped[Optional["Tree"]] = relationship(
        "Tree", remote_side=[id], backref="children"
    )

    def __str__(self):
        return f"{self.name}"


class Model1(db.Model):  # type: ignore[name-defined, misc]
    def __init__(
        self,
        test1=None,
        test2=None,
        bool_field=False,
        date_field=None,
        time_field=None,
        datetime_field=None,
        email_field=None,
        choice_field=None,
        enum_field=None,
        enum_type_field=None,
    ):
        self.test1 = test1
        self.test2 = test2
        self.bool_field = bool_field
        self.date_field = date_field
        self.time_field = time_field
        self.datetime_field = datetime_field
        self.email_field = email_field
        self.choice_field = choice_field
        self.enum_field = enum_field
        self.enum_type_field = enum_type_field

    class EnumChoices(enum.Enum):
        first = 1
        second = 2

    id = db.Column(db.Integer, primary_key=True)
    test1 = db.Column(db.String(20))
    test2 = db.Column(db.Unicode(20))
    bool_field = db.Column(db.Boolean)
    date_field = db.Column(db.Date)
    time_field = db.Column(db.Time)
    datetime_field = db.Column(db.DateTime)
    email_field = db.Column(EmailType)
    choice_field = db.Column(db.String, nullable=True)
    enum_field = db.Column(db.Enum("model1_v1", "model1_v2"), nullable=True)
    enum_type_field = db.Column(db.Enum(EnumChoices), nullable=True)
    sqla_utils_choice = db.Column(
        ChoiceType([("choice-1", "First choice"), ("choice-2", "Second choice")])
    )
    sqla_utils_enum = db.Column(ChoiceType(EnumChoices, impl=db.Integer()))
    sqla_utils_arrow = db.Column(ArrowType, default=arrow.utcnow())
    sqla_utils_uuid = db.Column(UUIDType(binary=False), default=uuid.uuid4)
    sqla_utils_url = db.Column(URLType)
    sqla_utils_ip_address = db.Column(IPAddressType)
    sqla_utils_currency = db.Column(CurrencyType)
    sqla_utils_color = db.Column(ColorType)

    def __unicode__(self):
        return self.test1

    def __str__(self):
        return self.test1
