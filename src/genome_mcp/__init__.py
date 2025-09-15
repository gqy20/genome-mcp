"""
Genome MCP - Intelligent Genomics Data Analysis Tool

A Model Context Protocol (MCP) based intelligent genomics data analysis tool
that integrates multiple biological databases and provides unified access to
genomic information through natural language interactions.

Author: Genomics MCP Team
Version: 0.1.0
"""

__version__ = "0.1.5"
__author__ = "Genomics MCP Team"
__email__ = "team@genomics-mcp.org"

from .exceptions import (
    APIError,
    AuthenticationError,
    BatchProcessingError,
    CacheError,
    ConfigurationError,
    DatabaseError,
    DataFormatError,
    DataNotFoundError,
    GenomeMCPError,
    NetworkError,
    QuerySyntaxError,
    RateLimitError,
    ResourceError,
    ServerError,
    TimeoutError,
    ValidationError,
    create_error_from_exception,
)
from .type_defs.common import ConfidenceLevel, DataSource
from .type_defs.gene import GeneQuery, GeneResponse
from .type_defs.variant import VariantQuery, VariantResponse

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "DataSource",
    "ConfidenceLevel",
    "GeneQuery",
    "GeneResponse",
    "VariantQuery",
    "VariantResponse",
    "GenomeMCPError",
    "ConfigurationError",
    "ValidationError",
    "DataNotFoundError",
    "DataFormatError",
    "APIError",
    "RateLimitError",
    "AuthenticationError",
    "NetworkError",
    "CacheError",
    "TimeoutError",
    "ResourceError",
    "BatchProcessingError",
    "QuerySyntaxError",
    "ServerError",
    "DatabaseError",
    "create_error_from_exception",
]
