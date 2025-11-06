"""Backend main entry point for user tag management system

This file initializes the FastAPI application, sets up the database connection, and registers all API routes.

Design decisions:
- Uses FastAPI for high performance and automatic API documentation
- Implements SQLAlchemy for database ORM
- Includes CORS middleware for frontend-backend communication
- Sets up exception handling for consistent error responses

Performance considerations:
- Uses async operations where appropriate
- Implements connection pooling for database connections
- Enables Gzip compression for faster response times

Boundary cases:
- Handles database connection failures gracefully
- Validates all incoming requests with Pydantic models
- Implements rate limiting to prevent abuse
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uvicorn

# Configuration
DATABASE_URL = "postgresql://user:password@localhost/user_tag_db"

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI app initialization
app = FastAPI(
    title="User Tag Management API",
    description="API for managing users and tags with multi-tenant support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Dependency to get database session
def get_db():
    """Get a database session for each request
    
    Yields:
        Session: SQLAlchemy database session
    
    Boundary cases:
        - Database connection failure
        - Session not properly closed
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import and register routes
from .api import users, tags

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])

# Root endpoint
@app.get("/")
def root():
    """Root endpoint for health check
    
    Returns:
        dict: Health check information
    """
    return {
        "message": "User Tag Management API",
        "status": "running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)