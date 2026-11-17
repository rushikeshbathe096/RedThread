from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base Pydantic schema with standard configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """Reusable mixin for created_at and updated_at timestamps."""
    created_at: datetime
    updated_at: Optional[datetime] = None


class ResponseEnvelope(BaseSchema, Generic[T]):
    """Standardized API response wrapper used across all endpoints."""
    success: bool = True
    data: T
    message: Optional[str] = None


class PaginatedResponse(BaseSchema, Generic[T]):
    """Standardized pagination wrapper for collections."""
    items: List[T]
    total: int = Field(ge=0, description="Total matching items across all pages")
    page: int = Field(ge=1, default=1, description="Current page number (1-indexed)")
    page_size: int = Field(ge=1, le=100, default=20, description="Number of items per page")
    total_pages: int = Field(ge=0, description="Total number of pages available")
