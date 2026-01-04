import enum
import uuid

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
from sqlalchemy import Unicode
from sqlalchemy.ext.hybrid import hybrid_property
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
    id = mapped_column(UUIDType(binary=False), default=uuid.uuid4, primary_key=True)

    # use a regular string field, for which we can specify a list of available choices
    # later on
    type = mapped_column(String(100))

    # Fixed choices can be handled in a number of different ways:
    enum_choice_field = mapped_column(Enum(EnumChoices), nullable=True)  # type: ignore[var-annotated]
    sqla_utils_choice_field = mapped_column(
        ChoiceType(AVAILABLE_USER_TYPES), nullable=True
    )
    sqla_utils_enum_choice_field = mapped_column(
        ChoiceType(EnumChoices, impl=Integer()), nullable=True
    )

    first_name = mapped_column(String(100))
    last_name = mapped_column(String(100))

    # Some sqlalchemy_utils data types (see https://sqlalchemy-utils.readthedocs.io/)
    email = mapped_column(EmailType, unique=True, nullable=False)
    website = mapped_column(URLType)
    ip_address = mapped_column(IPAddressType)
    currency = mapped_column(CurrencyType, nullable=True, default=None)
    timezone = mapped_column(TimezoneType(backend="pytz"))

    dialling_code = mapped_column(Integer())
    local_phone_number = mapped_column(String(10))

    featured_post_id = mapped_column(Integer, ForeignKey("post.id"))
    featured_post = relationship("Post", foreign_keys=[featured_post_id])

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
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tag.id")),
)


class Post(db.Model):
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(120))
    text = mapped_column(Text, nullable=False)
    date = mapped_column(Date)

    # some sqlalchemy_utils data types (see https://sqlalchemy-utils.readthedocs.io/)
    background_color = mapped_column(ColorType)
    created_at = mapped_column(ArrowType, default=arrow.utcnow())
    user_id = mapped_column(UUIDType(binary=False), ForeignKey(User.id))

    user = relationship(User, foreign_keys=[user_id], backref="posts")
    tags = relationship("Tag", secondary=post_tags_table)

    def __str__(self):
        return f"{self.title}"


class Tag(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(Unicode(64), unique=True)

    def __str__(self):
        return f"{self.name}"


class Tree(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(64))

    # recursive relationship
    parent_id = mapped_column(Integer, ForeignKey("tree.id"))
    parent = relationship("Tree", remote_side=[id], backref="children")

    def __str__(self):
        return f"{self.name}"
