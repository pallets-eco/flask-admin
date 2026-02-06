import enum
import json
import uuid
from datetime import date, datetime
from typing import Optional

import arrow
from admin import db
from sqlalchemy import cast
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import event
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
from sqlalchemy.orm.attributes import get_history
from sqlalchemy_utils import ArrowType
from sqlalchemy_utils import ChoiceType
from sqlalchemy_utils import ColorType
from sqlalchemy_utils import CurrencyType
from sqlalchemy_utils import EmailType
from sqlalchemy_utils import IPAddressType
from sqlalchemy_utils import TimezoneType
from sqlalchemy_utils import URLType
from sqlalchemy_utils import UUIDType


# Audit Log Action Types
class AuditActionType(enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

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


# Audit Log Model
class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[AuditActionType] = mapped_column(
        Enum(AuditActionType), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[str] = mapped_column(String(100), nullable=False)
    old_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action.value} {self.model_name} #{self.record_id}>"


def _serialize_value(value):
    """Serialize a value to a JSON-compatible format."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return value.value
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if hasattr(value, '__str__'):
        return str(value)
    return repr(value)


def _get_model_dict(instance, include_relationships=False):
    """Convert a model instance to a dictionary of its column values."""
    result = {}
    mapper = instance.__class__.__mapper__
    for column in mapper.columns:
        key = column.key
        value = getattr(instance, key, None)
        result[key] = _serialize_value(value)
    return result


def _get_primary_key(instance):
    """Get the primary key value of a model instance as a string."""
    mapper = instance.__class__.__mapper__
    pk_cols = mapper.primary_key
    if len(pk_cols) == 1:
        return str(getattr(instance, pk_cols[0].key))
    return str(tuple(getattr(instance, col.key) for col in pk_cols))


def _create_audit_log(session, action, instance, old_values=None, new_values=None):
    """Create an audit log entry."""
    if isinstance(instance, AuditLog):
        return

    audit = AuditLog(
        action=action,
        model_name=instance.__class__.__name__,
        record_id=_get_primary_key(instance),
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
    )
    session.add(audit)


def _after_insert_listener(mapper, connection, target):
    """Event listener for after insert."""
    new_values = _get_model_dict(target)

    @event.listens_for(db.session, "after_flush", once=True)
    def receive_after_flush(session, flush_context):
        _create_audit_log(session, AuditActionType.CREATE, target, new_values=new_values)


def _after_update_listener(mapper, connection, target):
    """Event listener for after update."""
    old_values = {}
    new_values = {}

    for column in mapper.columns:
        key = column.key
        history = get_history(target, key)
        if history.has_changes():
            old_val = history.deleted[0] if history.deleted else None
            new_val = history.added[0] if history.added else None
            old_values[key] = _serialize_value(old_val)
            new_values[key] = _serialize_value(new_val)

    if old_values:
        @event.listens_for(db.session, "after_flush", once=True)
        def receive_after_flush(session, flush_context):
            _create_audit_log(
                session, AuditActionType.UPDATE, target,
                old_values=old_values, new_values=new_values
            )


def _after_delete_listener(mapper, connection, target):
    """Event listener for after delete."""
    old_values = _get_model_dict(target)

    @event.listens_for(db.session, "after_flush", once=True)
    def receive_after_flush(session, flush_context):
        _create_audit_log(session, AuditActionType.DELETE, target, old_values=old_values)


# Register event listeners for all audited models
AUDITED_MODELS = [User, Post, Tag, Tree]

for model in AUDITED_MODELS:
    event.listen(model, "after_insert", _after_insert_listener)
    event.listen(model, "after_update", _after_update_listener)
    event.listen(model, "after_delete", _after_delete_listener)
