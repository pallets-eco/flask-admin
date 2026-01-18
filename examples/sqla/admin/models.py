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
