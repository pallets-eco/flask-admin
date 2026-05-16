import datetime
import enum
import uuid
from typing import Optional

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

AVAILABLE_USER_TYPES = [
    ("admin", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]


class EnumChoices(enum.Enum):
    first = 1
    second = 2


class PostTagLink(SQLModel, table=True):
    post_id: Optional[int] = Field(
        default=None, foreign_key="post.id", primary_key=True
    )
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    type: str = Field(default="regular-user", max_length=100)
    enum_choice_field: Optional[EnumChoices] = Field(default=None)

    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: str = Field(index=True, max_length=255)
    website: str = Field(default="", max_length=255)
    ip_address: str = Field(default="", max_length=64)
    currency: Optional[str] = Field(default=None, max_length=16)
    timezone: str = Field(default="UTC", max_length=64)

    dialling_code: int = Field(default=1)
    local_phone_number: str = Field(default="", max_length=10)

    featured_post_id: Optional[int] = Field(default=None, foreign_key="post.id")

    featured_post: Optional["Post"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[User.featured_post_id]"}
    )
    posts: list["Post"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Post.user_id]"},
    )

    @property
    def phone_number(self) -> Optional[str]:
        if self.dialling_code and self.local_phone_number:
            number = self.local_phone_number
            return (
                f"+{self.dialling_code} ({number[0]}) {number[1:3]} "
                f"{number[3:6]} {number[6:]}"
            )
        return None

    def __str__(self) -> str:
        return f"{self.last_name}, {self.first_name}"


class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=64)

    posts: list["Post"] = Relationship(back_populates="tags", link_model=PostTagLink)

    def __str__(self) -> str:
        return self.name


class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=120)
    text: str
    date: datetime.date = Field(default_factory=datetime.date.today)
    background_color: str = Field(default="#cccccc", max_length=32)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    user_id: uuid.UUID = Field(foreign_key="user.id")

    user: User = Relationship(
        back_populates="posts",
        sa_relationship_kwargs={"foreign_keys": "[Post.user_id]"},
    )
    tags: list[Tag] = Relationship(back_populates="posts", link_model=PostTagLink)

    def __str__(self) -> str:
        return self.title


class Tree(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=64)
    parent_id: Optional[int] = Field(default=None, foreign_key="tree.id")

    parent: Optional["Tree"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Tree.id"},
    )
    children: list["Tree"] = Relationship(back_populates="parent")

    def __str__(self) -> str:
        return self.name
