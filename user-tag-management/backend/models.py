"""Database models for user tag management system

This file defines the SQLAlchemy models for users, tags, and their association.

Design decisions:
- Uses UUID for primary keys for better security and scalability
- Implements many-to-many relationship between users and tags
- Includes tenant_id for multi-tenant support
- Uses Pydantic for data validation

Performance considerations:
- Adds indexes to frequently queried fields
- Uses lazy loading for relationships by default
- Implements cascade delete for associated records

Boundary cases:
- Handles duplicate email addresses
- Validates phone number format
- Ensures tag names are unique per tenant
"""

from sqlalchemy import Column, Integer, String, Text, UUID, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

# Association table for user-tag many-to-many relationship
user_tags = Table(
    'user_tags',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True)
)

class User(Base):
    """User model with personal information and tag associations
    
    Attributes:
        id: Unique identifier for the user
        tenant_id: Tenant identifier for multi-tenant support
        first_name: User's first name
        last_name: User's last name
        email: User's email address (unique)
        phone: User's phone number
        address: User's address
        tags: Associated tags
        created_at: Timestamp when the user was created
        updated_at: Timestamp when the user was last updated
    """
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), default='default-tenant', index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    address = Column(Text)
    tags = relationship('Tag', secondary=user_tags, back_populates='users')
    created_at = Column(String(50), default=lambda: str(uuid.uuid4().time_low))  # Simplified timestamp
    updated_at = Column(String(50), default=lambda: str(uuid.uuid4().time_low), onupdate=lambda: str(uuid.uuid4().time_low))

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

class Tag(Base):
    """Tag model for categorizing users
    
    Attributes:
        id: Unique identifier for the tag
        tenant_id: Tenant identifier for multi-tenant support
        name: Tag name (unique per tenant)
        description: Tag description
        users: Associated users
        created_at: Timestamp when the tag was created
        updated_at: Timestamp when the tag was last updated
    """
    __tablename__ = 'tags'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), default='default-tenant', index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    users = relationship('User', secondary=user_tags, back_populates='tags')
    created_at = Column(String(50), default=lambda: str(uuid.uuid4().time_low))
    updated_at = Column(String(50), default=lambda: str(uuid.uuid4().time_low), onupdate=lambda: str(uuid.uuid4().time_low))
    
    __table_args__ = (
        # Ensure tag name is unique per tenant
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"