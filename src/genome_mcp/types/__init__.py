"""
Type definitions for Genome MCP.

This module contains type definitions for various genomic data structures.
"""

from .gene import GeneQuery, GeneResponse, GeneInfo
from .variant import VariantQuery, VariantResponse, VariantInfo
from .common import DataSource, ConfidenceLevel, APIResponse

__all__ = [
    "GeneQuery",
    "GeneResponse", 
    "GeneInfo",
    "VariantQuery",
    "VariantResponse",
    "VariantInfo",
    "DataSource",
    "ConfidenceLevel",
    "APIResponse",
]