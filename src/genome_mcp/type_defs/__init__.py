"""
Type definitions for Genome MCP.

This module contains type definitions for various genomic data structures.
"""

from .common import (
    APIResponse,
    CacheEntry,
    ConfidenceLevel,
    DataSource,
    ErrorInfo,
    PaginationParams,
    PaginationResponse,
    QueryResult,
)
from .gene import (
    BatchGeneQuery,
    BatchGeneResponse,
    GeneInfo,
    GeneLocation,
    GeneQuery,
    GeneResponse,
)
from .variant import (
    ClinicalSignificance,
    FunctionalPrediction,
    GenomicPosition,
    PopulationFrequency,
    RegionVariantQuery,
    RegionVariantResponse,
    VariantInfo,
    VariantQuery,
    VariantResponse,
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
