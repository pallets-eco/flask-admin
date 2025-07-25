import enum
import uuid
from typing import ClassVar
from typing import Optional
from typing import TYPE_CHECKING

import arrow
from sqlalchemy import cast
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import operators
from sqlalchemy_utils import ChoiceType
from sqlalchemy_utils import ColorType
from sqlalchemy_utils import CurrencyType
from sqlalchemy_utils import EmailType
from sqlalchemy_utils import IPAddressType
from sqlalchemy_utils import TimezoneType
from sqlalchemy_utils import URLType
from sqlalchemy_utils import UUIDType
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

# Optional: install sqlalchemy-utils replacements or handle via custom types
# Example: pip install sqlalchemy-utils-compatible if you still want those

# Simulating SQLAlchemy-Utils with regular types
AVAILABLE_USER_TYPES = [
    ("admin", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]

_phone_number_placeholder = cast("hybrid_property", None)  # type: ignore


class EnumChoices(enum.Enum):
    first = 1
    second = 2


class PostTag(SQLModel, table=True):
    post_id: int = Field(foreign_key="post.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)


class Post(SQLModel, table=True):
    model_config = {"arbitrary_types_allowed": True}  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    title: Optional[str] = Field(default=None, max_length=120)
    text: Optional[str] = Field(nullable=False)
    date: Optional[Date] = Field(default=None, sa_column=Column(Date))

    background_color: Optional[str] = Field(default=None, sa_column=Column(ColorType))
    created_at: Optional[str] = Field(
        default_factory=lambda: arrow.utcnow().isoformat()
    )  # Simulate ArrowType

    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

    user: Optional["User"] = Relationship(
        back_populates="posts", sa_relationship_kwargs={"foreign_keys": "Post.user_id"}
    )

    tags: list["Tag"] = Relationship(
        back_populates="posts",
        link_model=PostTag,
        sa_relationship_kwargs={
            "primaryjoin": "Post.id==PostTag.post_id",
            "secondaryjoin": "Tag.id==PostTag.tag_id",
        },
    )

    def __str__(self):
        return self.title or ""


class Tag(SQLModel, table=True):
    model_config = {"arbitrary_types_allowed": True}  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(
        sa_column=Column(Unicode(64), unique=True, nullable=False)
    )

    posts: list["Post"] = Relationship(
        back_populates="tags",
        link_model=PostTag,
        sa_relationship_kwargs={
            "primaryjoin": "Tag.id==PostTag.tag_id",
            "secondaryjoin": "Post.id==PostTag.post_id",
        },
    )

    def __str__(self):
        return self.name


class User(SQLModel, table=True):
    model_config = {"arbitrary_types_allowed": True}  # type: ignore
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUIDType(binary=False), primary_key=True),
    )  # type: ignore

    type: Optional[str] = Field(default=None, max_length=100)

    enum_choice_field: Optional[EnumChoices] = Field(
        default=None, sa_column=Column(Enum(EnumChoices))
    )
    sqla_utils_choice_field: Optional[str] = Field(
        default=None, sa_column=Column(ChoiceType(AVAILABLE_USER_TYPES), nullable=True)
    )
    sqla_utils_enum_choice_field: Optional[int] = Field(
        default=None,
        sa_column=Column(ChoiceType(EnumChoices, impl=Integer()), nullable=True),
    )  # Replace ChoiceType(EnumChoices, impl=Integer)

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)

    email: Optional[str] = Field(
        sa_column=Column(EmailType, unique=True, nullable=False)
    )  # Replace EmailType
    website: Optional[str] = Field(default=None, sa_column=Column(URLType))
    ip_address: Optional[str] = Field(default=None, sa_column=Column(IPAddressType))
    currency: Optional[str] = Field(
        default=None, sa_column=Column(CurrencyType, nullable=True)
    )
    timezone: Optional[str] = Field(
        default=None, sa_column=Column(TimezoneType(backend="pytz"))
    )

    dialling_code: Optional[int] = None
    local_phone_number: Optional[str] = Field(default=None, max_length=10)

    featured_post_id: Optional[int] = Field(default=None, foreign_key="post.id")
    featured_post: Optional[Post] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[User.featured_post_id]"}
    )

    posts: list["Post"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"foreign_keys": "Post.user_id"}
    )

    # Correct hybrid property setup
    @hybrid_property
    def phone_number(self) -> Optional[str]:  # type: ignore
        if self.dialling_code and self.local_phone_number:
            number = self.local_phone_number
            return (
                f"+{self.dialling_code} ({number[0]}) {number[1:3]} "
                f"{number[3:6]} {number[6:]}"
            )
        return None

    @phone_number.expression  # type: ignore
    def phone_number(cls):
        return operators.ColumnOperators.concat(
            cast(cls.dialling_code, String),
            cast(cls.local_phone_number, String),
        )

    # Tell Pydantic to ignore `phone_number`
    phone_number: ClassVar  # type: ignore

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    def __repr__(self):
        return f"{self.id}: {self.__str__()}"


class Tree(SQLModel, table=True):
    model_config = {"arbitrary_types_allowed": True}  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(max_length=64, nullable=False)

    parent_id: Optional[int] = Field(default=None, foreign_key="tree.id")
    parent: Optional["Tree"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "[Tree.id]"}
    )
    children: list["Tree"] = Relationship(back_populates="parent")

    def __str__(self):
        return self.name


# Required for forward references
if TYPE_CHECKING:
    Post.model_rebuild()
    Tag.model_rebuild()
    User.model_rebuild()
    Tree.model_rebuild()
