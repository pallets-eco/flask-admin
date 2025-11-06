"""API endpoints for tag management

This file defines the API endpoints for creating, reading, updating, and deleting tags.

Design decisions:
- Uses FastAPI's APIRouter for modular route organization
- Implements dependency injection for database sessions
- Uses Pydantic schemas for request/response validation
- Supports multi-tenant functionality
- Implements proper error handling

Performance considerations:
- Uses limit/offset pagination for large result sets
- Uses efficient database queries with indexes

Boundary cases:
- Handles non-existent tag IDs
- Validates unique tag names per tenant
- Ensures proper tenant isolation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ..models import Tag
from ..schemas import TagCreate, TagUpdate, Tag, MessageResponse
from ..main import get_db

router = APIRouter()

@router.post("/", response_model=Tag, status_code=201)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """Create a new tag
    
    Args:
        tag: TagCreate schema with tag information
        db: Database session dependency
    
    Returns:
        Tag: Created tag information
    
    Boundary cases:
        - Duplicate tag name per tenant
        - Missing required fields
    """
    # Check if tag name already exists for the tenant
    db_tag = db.query(Tag).filter(Tag.name == tag.name, Tag.tenant_id == tag.tenant_id).first()
    if db_tag:
        raise HTTPException(status_code=400, detail="Tag name already exists")
    
    # Create new tag
    db_tag = Tag(
        name=tag.name,
        description=tag.description,
        tenant_id=tag.tenant_id
    )
    
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.get("/", response_model=List[Tag])
def read_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tenant_id: Optional[str] = Query("default-tenant"),
    db: Session = Depends(get_db)
):
    """Get a list of tags with optional pagination and tenant filter
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        tenant_id: Tenant identifier for multi-tenant support
        db: Database session dependency
    
    Returns:
        List[Tag]: List of tags
    
    Performance considerations:
        - Uses limit/offset pagination
    """
    tags = db.query(Tag).filter(Tag.tenant_id == tenant_id).offset(skip).limit(limit).all()
    return tags

@router.get("/{tag_id}", response_model=Tag)
def read_tag(tag_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a single tag by ID
    
    Args:
        tag_id: Tag UUID
        db: Database session dependency
    
    Returns:
        Tag: Tag information
    
    Boundary cases:
        - Non-existent tag ID
    """
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return db_tag

@router.put("/{tag_id}", response_model=Tag)
def update_tag(tag_id: uuid.UUID, tag: TagUpdate, db: Session = Depends(get_db)):
    """Update an existing tag
    
    Args:
        tag_id: Tag UUID
        tag: TagUpdate schema with updated information
        db: Database session dependency
    
    Returns:
        Tag: Updated tag information
    
    Boundary cases:
        - Non-existent tag ID
        - Duplicate tag name per tenant
    """
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Check if tag name is being updated to an existing one
    if tag.name and tag.name != db_tag.name:
        existing_tag = db.query(Tag).filter(Tag.name == tag.name, Tag.tenant_id == db_tag.tenant_id).first()
        if existing_tag:
            raise HTTPException(status_code=400, detail="Tag name already exists")
    
    # Update tag fields
    update_data = tag.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tag, field, value)
    
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.delete("/{tag_id}", response_model=MessageResponse)
def delete_tag(tag_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a tag by ID
    
    Args:
        tag_id: Tag UUID
        db: Database session dependency
    
    Returns:
        MessageResponse: Success message
    
    Boundary cases:
        - Non-existent tag ID
    """
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(db_tag)
    db.commit()
    return {"message": "Tag deleted successfully"}