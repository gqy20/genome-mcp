"""
Type definitions for Genome MCP.

This module contains type definitions for various genomic data structures.
"""

from .gene import (
    GeneQuery, 
    GeneResponse, 
    GeneInfo, 
    GeneLocation,
    BatchGeneQuery,
    BatchGeneResponse
)
from .variant import (
    VariantQuery, 
    VariantResponse, 
    VariantInfo,
    GenomicPosition,
    ClinicalSignificance,
    PopulationFrequency,
    FunctionalPrediction,
    RegionVariantQuery,
    RegionVariantResponse
)
from .common import (
    DataSource, 
    ConfidenceLevel, 
    APIResponse,
    PaginationParams,
    PaginationResponse,
    QueryResult,
    CacheEntry,
    ErrorInfo
)

__all__ = [
    # Gene types
    "GeneQuery",
    "GeneResponse", 
    "GeneInfo",
    "GeneLocation",
    "BatchGeneQuery",
    "BatchGeneResponse",
    # Variant types
    "VariantQuery",
    "VariantResponse",
    "VariantInfo",
    "GenomicPosition",
    "ClinicalSignificance",
    "PopulationFrequency",
    "FunctionalPrediction",
    "RegionVariantQuery",
    "RegionVariantResponse",
    # Common types
    "DataSource",
    "ConfidenceLevel",
    "APIResponse",
    "PaginationParams",
    "PaginationResponse",
    "QueryResult",
    "CacheEntry",
    "ErrorInfo",
]