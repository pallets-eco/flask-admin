import datetime
import enum
import uuid
from typing import Optional
from typing import TYPE_CHECKING

import arrow
from pydantic import EmailStr  # Pydantic-native types
from pydantic import field_validator
from pydantic import HttpUrl  # Pydantic-native types
from pydantic import IPvAnyAddress  # Pydantic-native types
from sqlalchemy import Column
from sqlalchemy_utils import ColorType
from sqlalchemy_utils import CurrencyType
from sqlalchemy_utils import TimezoneType
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel


class EnumChoices(enum.Enum):
    first = 1
    second = 2


class AvailableUserTypes(str, enum.Enum):
    admin = "admin"
    content_writer = "content-writer"
    editor = "editor"
    regular_user = "regular-user"


def enum_to_form_choices(enum_cls):
    return [
        (member.value, member.name.replace("_", " ").title()) for member in enum_cls
    ]


AVAILABLE_USER_TYPES = enum_to_form_choices(AvailableUserTypes)


class PostTag(SQLModel, table=True):
    post_id: int = Field(foreign_key="post.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)


class Post(SQLModel, table=True):
    model_config = {"arbitrary_types_allowed": True}  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    title: Optional[str] = Field(default=None, max_length=120)
    text: Optional[str] = Field(nullable=False)
    date: Optional[datetime.date] = Field(default=None)

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
        default=None, max_length=64, unique=True, nullable=False
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
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)  # type: ignore

    type: Optional[AvailableUserTypes] = Field(default=AvailableUserTypes.regular_user)

    # Native enum field
    enum_choice_field: Optional[EnumChoices] = Field(default=None)

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)

    # Pure SQLModel with built-in Pydantic validators
    # Works well with SQLite. but sa_column format is better for Postgres or MYSQL
    # No DB constraints but validates format at runtime
    email: EmailStr = Field(nullable=False, unique=True)
    website_str: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)

    # These two fields work better using sqlachemy style
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

    @property
    def full_name(self) -> Optional[str]:
        if self.last_name is not None and self.first_name is not None:
            return f"{self.last_name} {self.first_name}"
        return None

    @full_name.setter
    def full_name(self, value: Optional[str]):
        # This setter is needed for Flask-Admin to detect it as a field
        pass  # Read-only computed field

    @property
    def phone_number(self) -> Optional[str]:
        if self.dialling_code is not None and self.local_phone_number is not None:
            number = self.local_phone_number
            return (
                f"+{self.dialling_code} ({number[0]}) {number[1:3]} "
                f"{number[3:6]} {number[6:]}"
            )
        return None

    @phone_number.setter
    def phone_number(self, value: Optional[str]):
        # This setter is needed for Flask-Admin to detect it as a field
        pass  # Read-only computed field

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    def __repr__(self):
        return f"{self.id}: {self.__str__()}"

    @property
    def website(self) -> Optional[HttpUrl]:
        if self.website_str is None:
            return None
        return HttpUrl(self.website_str)

    @website.setter
    def website(self, value: Optional[HttpUrl]):
        self.website_str = str(value) if value is not None else None

    @field_validator("ip_address", mode="before")
    def validate_ip_address(cls, v):
        if v is None:
            return v
        return str(IPvAnyAddress(v))


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
