"""
Gene-related type definitions for Genome MCP.

This module contains type definitions for gene-related data structures.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import ConfidenceLevel, DataSource


class GeneQuery(BaseModel):
    """Gene query parameters."""

    gene_symbol: str = Field(..., description="Gene symbol (e.g., TP53)")
    species: str = Field("homo_sapiens", description="Species name")
    include_synonyms: bool = Field(True, description="Include gene synonyms")
    include_function: bool = Field(True, description="Include functional annotations")
    include_pathways: bool = Field(False, description="Include pathway information")
    include_expression: bool = Field(False, description="Include expression data")

    @field_validator("gene_symbol")
    @classmethod
    def validate_gene_symbol(cls, v):
        """Validate gene symbol."""
        if not v or not v.strip():
            raise ValueError("Gene symbol cannot be empty")
        return v.strip().upper()

    @field_validator("species")
    @classmethod
    def validate_species(cls, v):
        """Validate species name."""
        if not v or not v.strip():
            raise ValueError("Species name cannot be empty")
        return v.strip().lower().replace(" ", "_")

    model_config = ConfigDict(use_enum_values=True)


class GeneLocation(BaseModel):
    """Gene location information."""

    chromosome: str = Field(..., description="Chromosome name")
    start: int = Field(..., ge=1, description="Start position")
    end: int = Field(..., ge=1, description="End position")
    strand: str = Field(..., description="Strand (+ or -)")
    assembly: str = Field("GRCh38", description="Genome assembly version")

    @field_validator("strand")
    @classmethod
    def validate_strand(cls, v):
        """Validate strand."""
        if v not in ["+", "-"]:
            raise ValueError("Strand must be '+' or '-'")
        return v

    @field_validator("end")
    @classmethod
    def validate_positions(cls, v, info):
        """Validate start and end positions."""
        data = info.data
        start = data.get("start")
        if start is not None and v < start:
            raise ValueError(
                "End position must be greater than or equal to start position"
            )
        return v

    model_config = ConfigDict(use_enum_values=True)


class GeneInfo(BaseModel):
    """Comprehensive gene information."""

    gene_id: str = Field(..., description="Gene ID")
    gene_symbol: str = Field(..., description="Gene symbol")
    gene_name: str = Field(..., description="Gene full name")
    species: str = Field(..., description="Species name")
    location: GeneLocation = Field(..., description="Gene location")
    gene_type: str = Field(..., description="Gene type (e.g., protein_coding)")
    description: Optional[str] = Field(None, description="Gene description")
    synonyms: List[str] = Field(default_factory=list, description="Gene synonyms")
    external_ids: Dict[str, str] = Field(
        default_factory=dict, description="External database IDs"
    )
    function_summary: Optional[str] = Field(None, description="Functional summary")
    pathways: List[str] = Field(default_factory=list, description="Associated pathways")
    go_terms: List[str] = Field(default_factory=list, description="GO term annotations")
    protein_domains: List[str] = Field(
        default_factory=list, description="Protein domains"
    )
    expression_tissues: List[str] = Field(
        default_factory=list, description="Expression tissues"
    )
    confidence: ConfidenceLevel = Field(
        ConfidenceLevel.UNKNOWN, description="Data confidence"
    )
    sources: List[DataSource] = Field(default_factory=list, description="Data sources")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    model_config = ConfigDict(use_enum_values=True)


class GeneResponse(BaseModel):
    """Gene query response."""

    query: GeneQuery = Field(..., description="Original query")
    gene_info: Optional[GeneInfo] = Field(None, description="Gene information")
    alternate_symbols: List[str] = Field(
        default_factory=list, description="Alternate gene symbols"
    )
    related_genes: List[str] = Field(default_factory=list, description="Related genes")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    execution_time: float = Field(
        0.0, ge=0.0, description="Query execution time in seconds"
    )

    model_config = ConfigDict(use_enum_values=True)


class BatchGeneQuery(BaseModel):
    """Batch gene query parameters."""

    gene_symbols: List[str] = Field(..., description="List of gene symbols")
    species: str = Field("homo_sapiens", description="Species name")
    include_synonyms: bool = Field(True, description="Include gene synonyms")
    include_function: bool = Field(True, description="Include functional annotations")

    @field_validator("gene_symbols")
    @classmethod
    def validate_gene_symbols(cls, v):
        """Validate gene symbols list."""
        if not v:
            raise ValueError("Gene symbols list cannot be empty")
        if len(v) > 100:
            raise ValueError("Maximum 100 gene symbols allowed in batch query")
        return [symbol.strip().upper() for symbol in v if symbol.strip()]

    model_config = ConfigDict(use_enum_values=True)


class BatchGeneResponse(BaseModel):
    """Batch gene query response."""

    query: BatchGeneQuery = Field(..., description="Original query")
    results: Dict[str, GeneInfo] = Field(
        default_factory=dict, description="Results by gene symbol"
    )
    not_found: List[str] = Field(
        default_factory=list, description="Not found gene symbols"
    )
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    execution_time: float = Field(
        0.0, ge=0.0, description="Query execution time in seconds"
    )

    model_config = ConfigDict(use_enum_values=True)
