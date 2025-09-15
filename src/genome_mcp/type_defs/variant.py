"""
Variant-related type definitions for Genome MCP.

This module contains type definitions for variant-related data structures.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import ConfidenceLevel, DataSource


class VariantQuery(BaseModel):
    """Variant query parameters."""

    variant_id: str = Field(..., description="Variant ID (rsID or genomic position)")
    assembly: str = Field("GRCh38", description="Genome assembly version")
    include_clinical: bool = Field(True, description="Include clinical significance")
    include_population: bool = Field(True, description="Include population frequencies")
    include_functional: bool = Field(True, description="Include functional predictions")
    include_related: bool = Field(False, description="Include related variants")

    @field_validator("variant_id")
    @classmethod
    def validate_variant_id(cls, v):
        """Validate variant ID."""
        if not v or not v.strip():
            raise ValueError("Variant ID cannot be empty")
        return v.strip()

    @field_validator("assembly")
    @classmethod
    def validate_assembly(cls, v):
        """Validate genome assembly."""
        valid_assemblies = ["GRCh37", "GRCh38", "hg19", "hg38"]
        if v not in valid_assemblies:
            raise ValueError(f"Assembly must be one of {valid_assemblies}")
        return v

    model_config = ConfigDict(use_enum_values=True)


class GenomicPosition(BaseModel):
    """Genomic position information."""

    chromosome: str = Field(..., description="Chromosome name")
    position: int = Field(..., ge=1, description="Genomic position")
    ref_allele: str = Field(..., description="Reference allele")
    alt_allele: str = Field(..., description="Alternate allele")
    assembly: str = Field("GRCh38", description="Genome assembly version")

    @field_validator("ref_allele")
    @classmethod
    def validate_ref_allele(cls, v):
        """Validate reference allele."""
        if not v or not v.strip():
            raise ValueError("Allele cannot be empty")
        return v.strip().upper()

    @field_validator("alt_allele")
    @classmethod
    def validate_alt_allele(cls, v):
        """Validate alternate allele."""
        if not v or not v.strip():
            raise ValueError("Allele cannot be empty")
        return v.strip().upper()

    model_config = ConfigDict(use_enum_values=True)


class ClinicalSignificance(BaseModel):
    """Clinical significance information."""

    significance: str = Field(
        ..., description="Clinical significance (e.g., Pathogenic)"
    )
    condition: str = Field(..., description="Associated condition")
    evidence_level: str = Field(..., description="Evidence level")
    source: DataSource = Field(..., description="Data source")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    model_config = ConfigDict(use_enum_values=True)


class PopulationFrequency(BaseModel):
    """Population frequency information."""

    population: str = Field(..., description="Population name")
    frequency: float = Field(..., ge=0.0, le=1.0, description="Allele frequency")
    sample_size: int = Field(..., ge=0, description="Sample size")
    source: DataSource = Field(..., description="Data source")

    model_config = ConfigDict(use_enum_values=True)


class FunctionalPrediction(BaseModel):
    """Functional prediction information."""

    algorithm: str = Field(..., description="Prediction algorithm")
    prediction: str = Field(..., description="Predicted effect")
    score: Optional[float] = Field(None, description="Prediction score")
    confidence: ConfidenceLevel = Field(
        ConfidenceLevel.UNKNOWN, description="Prediction confidence"
    )
    source: DataSource = Field(..., description="Data source")

    model_config = ConfigDict(use_enum_values=True)


class VariantInfo(BaseModel):
    """Comprehensive variant information."""

    variant_id: str = Field(..., description="Variant ID")
    rsid: Optional[str] = Field(None, description="dbSNP ID")
    position: GenomicPosition = Field(..., description="Genomic position")
    variant_type: str = Field(..., description="Variant type (e.g., SNV, INDEL)")
    clinical_significance: List[ClinicalSignificance] = Field(
        default_factory=list, description="Clinical significance"
    )
    population_frequencies: List[PopulationFrequency] = Field(
        default_factory=list, description="Population frequencies"
    )
    functional_predictions: List[FunctionalPrediction] = Field(
        default_factory=list, description="Functional predictions"
    )
    genes: List[str] = Field(default_factory=list, description="Affected genes")
    consequences: List[str] = Field(
        default_factory=list, description="Variant consequences"
    )
    related_variants: List[str] = Field(
        default_factory=list, description="Related variants"
    )
    confidence: ConfidenceLevel = Field(
        ConfidenceLevel.UNKNOWN, description="Data confidence"
    )
    sources: List[DataSource] = Field(default_factory=list, description="Data sources")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    model_config = ConfigDict(use_enum_values=True)


class VariantResponse(BaseModel):
    """Variant query response."""

    query: VariantQuery = Field(..., description="Original query")
    variant_info: Optional[VariantInfo] = Field(None, description="Variant information")
    alternate_ids: List[str] = Field(
        default_factory=list, description="Alternate variant IDs"
    )
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    execution_time: float = Field(
        0.0, ge=0.0, description="Query execution time in seconds"
    )

    model_config = ConfigDict(use_enum_values=True)


class RegionVariantQuery(BaseModel):
    """Genomic region variant query parameters."""

    chromosome: str = Field(..., description="Chromosome name")
    start: int = Field(..., ge=1, description="Start position")
    end: int = Field(..., ge=1, description="End position")
    assembly: str = Field("GRCh38", description="Genome assembly version")
    variant_types: List[str] = Field(
        default_factory=list, description="Variant types to include"
    )
    min_frequency: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum allele frequency"
    )
    max_frequency: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Maximum allele frequency"
    )
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")

    @field_validator("end")
    @classmethod
    def validate_positions(cls, v, values):
        """Validate start and end positions."""
        start = values.get("start")
        if start is not None:
            if v < start:
                raise ValueError(
                    "End position must be greater than or equal to start position"
                )
            if v - start > 1000000:  # 1MB limit
                raise ValueError("Region size cannot exceed 1MB")
        return v

    model_config = ConfigDict(use_enum_values=True)


class RegionVariantResponse(BaseModel):
    """Genomic region variant query response."""

    query: RegionVariantQuery = Field(..., description="Original query")
    variants: List[VariantInfo] = Field(
        default_factory=list, description="Found variants"
    )
    total_count: int = Field(0, ge=0, description="Total number of variants")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    execution_time: float = Field(
        0.0, ge=0.0, description="Query execution time in seconds"
    )

    model_config = ConfigDict(use_enum_values=True)
