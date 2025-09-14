"""
Genome MCP - Intelligent Genomics Data Analysis Tool

A Model Context Protocol (MCP) based intelligent genomics data analysis tool
that integrates multiple biological databases and provides unified access to
genomic information through natural language interactions.

Author: Genomics MCP Team
Version: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "Genomics MCP Team"
__email__ = "team@genomics-mcp.org"

from .core.models import GeneInfo, VariantInfo, DataSource
from .core.exceptions import GenomicsMCPError, APIError, DataValidationError
from .types.gene import GeneQuery, GeneResponse
from .types.variant import VariantQuery, VariantResponse

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "GeneInfo",
    "VariantInfo", 
    "DataSource",
    "GenomicsMCPError",
    "APIError",
    "DataValidationError",
    "GeneQuery",
    "GeneResponse",
    "VariantQuery",
    "VariantResponse",
]