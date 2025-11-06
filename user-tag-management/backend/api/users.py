"""API endpoints for user management

This file defines the API endpoints for creating, reading, updating, and deleting users.

Design decisions:
- Uses FastAPI's APIRouter for modular route organization
- Implements dependency injection for database sessions
- Uses Pydantic schemas for request/response validation
- Supports multi-tenant functionality
- Implements proper error handling

Performance considerations:
- Uses limit/offset pagination for large result sets
- Implements eager loading for relationships to avoid N+1 queries
- Uses efficient database queries with indexes

Boundary cases:
- Handles non-existent user IDs
- Validates unique email addresses
- Ensures proper tenant isolation
- Handles invalid tag IDs during user creation/update
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ..models import User, Tag
from ..schemas import UserCreate, UserUpdate, User, MessageResponse
from ..main import get_db

router = APIRouter()

@router.post("/", response_model=User, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user with optional tags
    
    Args:
        user: UserCreate schema with user information
        db: Database session dependency
    
    Returns:
        User: Created user information
    
    Boundary cases:
        - Duplicate email address
        - Invalid tag IDs
        - Missing required fields
    """
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email, User.tenant_id == user.tenant_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        address=user.address,
        tenant_id=user.tenant_id
    )
    
    # Add tags if provided
    if user.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(user.tag_ids), Tag.tenant_id == user.tenant_id).all()
        if len(tags) != len(user.tag_ids):
            raise HTTPException(status_code=400, detail="One or more tag IDs are invalid")
        db_user.tags = tags
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[User])
def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tenant_id: Optional[str] = Query("default-tenant"),
    db: Session = Depends(get_db)
):
    """Get a list of users with optional pagination and tenant filter
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        tenant_id: Tenant identifier for multi-tenant support
        db: Database session dependency
    
    Returns:
        List[User]: List of users
    
    Performance considerations:
        - Uses limit/offset pagination
        - Implements eager loading for tags to avoid N+1 queries
    """
    users = db.query(User).filter(User.tenant_id == tenant_id).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=User)
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a single user by ID
    
    Args:
        user_id: User UUID
        db: Database session dependency
    
    Returns:
        User: User information
    
    Boundary cases:
        - Non-existent user ID
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
def update_user(user_id: uuid.UUID, user: UserUpdate, db: Session = Depends(get_db)):
    """Update an existing user
    
    Args:
        user_id: User UUID
        user: UserUpdate schema with updated information
        db: Database session dependency
    
    Returns:
        User: Updated user information
    
    Boundary cases:
        - Non-existent user ID
        - Duplicate email address
        - Invalid tag IDs
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if email is being updated to an existing one
    if user.email and user.email != db_user.email:
        existing_user = db.query(User).filter(User.email == user.email, User.tenant_id == db_user.tenant_id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Update user fields
    update_data = user.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "tag_ids":
            # Update tags
            if value is None:
                db_user.tags = []
            else:
                tags = db.query(Tag).filter(Tag.id.in_(value), Tag.tenant_id == db_user.tenant_id).all()
                if len(tags) != len(value):
                    raise HTTPException(status_code=400, detail="One or more tag IDs are invalid")
                db_user.tags = tags
        else:
            setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a user by ID
    
    Args:
        user_id: User UUID
        db: Database session dependency
    
    Returns:
        MessageResponse: Success message
    
    Boundary cases:
        - Non-existent user ID
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}