"""
Common type definitions for Genome MCP.

This module contains common type definitions used across the system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DataSource(str, Enum):
    """Data source enumeration."""

    NCBI = "ncbi"
    ENSEMBL = "ensembl"
    DBSNP = "dbsnp"
    CLINVAR = "clinvar"
    GO = "go"
    KEGG = "kegg"
    UNIPROT = "uniprot"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Confidence level enumeration."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class APIResponse(BaseModel):
    """Base API response model."""

    success: bool = Field(True, description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )
    source: DataSource = Field(DataSource.UNKNOWN, description="Data source")

    class Config:
        use_enum_values = True


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    class Config:
        use_enum_values = True


class PaginationResponse(BaseModel):
    """Pagination response model."""

    items: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of items"
    )
    total: int = Field(0, ge=0, description="Total number of items")
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    total_pages: int = Field(0, ge=0, description="Total number of pages")

    class Config:
        use_enum_values = True


class QueryResult(BaseModel):
    """Query result model."""

    query: str = Field(..., description="Original query")
    results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Query results"
    )
    sources: List[DataSource] = Field(
        default_factory=list, description="Data sources used"
    )
    confidence: ConfidenceLevel = Field(
        ConfidenceLevel.UNKNOWN, description="Result confidence"
    )
    execution_time: float = Field(
        0.0, ge=0.0, description="Query execution time in seconds"
    )
    warnings: List[str] = Field(default_factory=list, description="Warning messages")

    class Config:
        use_enum_values = True


class CacheEntry(BaseModel):
    """Cache entry model."""

    key: str = Field(..., description="Cache key")
    value: Dict[str, Any] = Field(..., description="Cached value")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    expires_at: datetime = Field(..., description="Expiration timestamp")
    hit_count: int = Field(0, ge=0, description="Number of cache hits")

    class Config:
        use_enum_values = True


class ErrorInfo(BaseModel):
    """Error information model."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Error timestamp"
    )

    class Config:
        use_enum_values = True
