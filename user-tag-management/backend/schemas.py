"""Pydantic schemas for data validation in user tag management system

This file defines the Pydantic models for request and response validation.

Design decisions:
- Uses separate schemas for creation, update, and read operations
- Implements strict data validation with appropriate field types
- Includes all necessary fields for each operation
- Uses UUID type for IDs
- Supports multi-tenant functionality

Performance considerations:
- Uses lightweight schemas for API requests/responses
- Avoids unnecessary fields in response models
- Implements validation at the API layer to reduce database load

Boundary cases:
- Validates email format
- Ensures required fields are present
- Validates string lengths
- Handles optional fields appropriately
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import uuid

class TagBase(BaseModel):
    """Base tag schema with common fields"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tenant_id: Optional[str] = Field("default-tenant", max_length=100)

class TagCreate(TagBase):
    """Schema for creating a new tag"""
    pass

class TagUpdate(BaseModel):
    """Schema for updating an existing tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class Tag(TagBase):
    """Schema for reading tag information"""
    id: uuid.UUID
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True

class UserBase(BaseModel):
    """Base user schema with common fields"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    tenant_id: Optional[str] = Field("default-tenant", max_length=100)

class UserCreate(UserBase):
    """Schema for creating a new user"""
    tag_ids: Optional[List[uuid.UUID]] = []

class UserUpdate(BaseModel):
    """Schema for updating an existing user"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    tag_ids: Optional[List[uuid.UUID]] = None

class User(UserBase):
    """Schema for reading user information"""
    id: uuid.UUID
    tags: List[Tag] = []
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True

class UserTagAssociation(BaseModel):
    """Schema for user-tag association"""
    user_id: uuid.UUID
    tag_id: uuid.UUID

class MessageResponse(BaseModel):
    """Schema for generic message responses"""
    message: str

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "User not found"
            }
        }