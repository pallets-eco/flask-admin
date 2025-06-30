import enum
import uuid

import arrow
from sqlalchemy import cast
from sqlalchemy import sql
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import ArrowType
from sqlalchemy_utils import ChoiceType
from sqlalchemy_utils import ColorType
from sqlalchemy_utils import CurrencyType
from sqlalchemy_utils import EmailType
from sqlalchemy_utils import IPAddressType
from sqlalchemy_utils import TimezoneType
from sqlalchemy_utils import URLType
from sqlalchemy_utils import UUIDType

from admin import db

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
    id = db.Column(UUIDType(binary=False), default=uuid.uuid4, primary_key=True)

    # use a regular string field, for which we can specify a list of available choices
    # later on
    type = db.Column(db.String(100))

    # Fixed choices can be handled in a number of different ways:
    enum_choice_field = db.Column(db.Enum(EnumChoices), nullable=True)
    sqla_utils_choice_field = db.Column(ChoiceType(AVAILABLE_USER_TYPES), nullable=True)
    sqla_utils_enum_choice_field = db.Column(
        ChoiceType(EnumChoices, impl=db.Integer()), nullable=True
    )

    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    # Some sqlalchemy_utils data types (see https://sqlalchemy-utils.readthedocs.io/)
    email = db.Column(EmailType, unique=True, nullable=False)
    website = db.Column(URLType)
    ip_address = db.Column(IPAddressType)
    currency = db.Column(CurrencyType, nullable=True, default=None)
    timezone = db.Column(TimezoneType(backend="pytz"))

    dialling_code = db.Column(db.Integer())
    local_phone_number = db.Column(db.String(10))

    featured_post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    featured_post = db.relationship("Post", foreign_keys=[featured_post_id])

    @hybrid_property
    def phone_number(self):
        if self.dialling_code and self.local_phone_number:
            number = str(self.local_phone_number)
            return (
                f"+{self.dialling_code} ({number[0]}) {number[1:3]} "
                f"{number[3:6]} {number[6::]}"
            )
        return

    @phone_number.expression
    def phone_number(cls):
        return sql.operators.ColumnOperators.concat(
            cast(cls.dialling_code, db.String), cls.local_phone_number
        )

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    def __repr__(self):
        return f"{self.id}: {self.__str__()}"


# Create M2M table
post_tags_table = db.Table(
    "post_tags",
    db.Model.metadata,
    db.Column("post_id", db.Integer, db.ForeignKey("post.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date)

    # some sqlalchemy_utils data types (see https://sqlalchemy-utils.readthedocs.io/)
    background_color = db.Column(ColorType)
    created_at = db.Column(ArrowType, default=arrow.utcnow())
    user_id = db.Column(UUIDType(binary=False), db.ForeignKey(User.id))

    user = db.relationship(User, foreign_keys=[user_id], backref="posts")
    tags = db.relationship("Tag", secondary=post_tags_table)

    def __str__(self):
        return f"{self.title}"


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True)

    def __str__(self):
        return f"{self.name}"


class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    # recursive relationship
    parent_id = db.Column(db.Integer, db.ForeignKey("tree.id"))
    parent = db.relationship("Tree", remote_side=[id], backref="children")

    def __str__(self):
        return f"{self.name}"
