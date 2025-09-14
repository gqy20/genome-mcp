"""
Data parsing utilities for Genome MCP.

This module provides utility functions for parsing and validating genomic data
from various sources and formats.
"""

import json
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import structlog

from genome_mcp.exceptions import DataFormatError, ValidationError, create_error_from_exception

logger = structlog.get_logger(__name__)


class GenomicDataParser:
    """Parser for genomic data formats."""

    # Common genomic coordinate patterns
    CHROMOSOME_PATTERN = re.compile(
        r"^(chr)?([1-9]|1[0-9]|2[0-2]|X|Y|MT?)$", re.IGNORECASE
    )
    GENOMIC_POSITION_PATTERN = re.compile(r"^(\d+):(\d+)-(\d+)$")
    RSID_PATTERN = re.compile(r"^rs\d+$")
    ENSEMBL_GENE_PATTERN = re.compile(r"^ENSG\d{11}$")
    ENSEMBL_TRANSCRIPT_PATTERN = re.compile(r"^ENST\d{11}$")
    ENSEMBL_PROTEIN_PATTERN = re.compile(r"^ENSP\d{11}$")

    @classmethod
    def parse_genomic_position(cls, position_str: str) -> Dict[str, Any]:
        """
        Parse genomic position string.

        Args:
            position_str: Genomic position string (e.g., "chr1:1000-2000")

        Returns:
            Parsed genomic position dictionary

        Raises:
            ValidationError: If position format is invalid
        """
        try:
            # Clean the string
            position_str = position_str.strip().upper()

            # Handle different formats
            if ":" in position_str and "-" in position_str:
                # Format: chr1:1000-2000 or 1:1000-2000
                match = cls.GENOMIC_POSITION_PATTERN.search(position_str)
                if not match:
                    raise ValueError(f"Invalid genomic position format: {position_str}")

                chromosome = match.group(1)
                start = int(match.group(2))
                end = int(match.group(3))

            elif ":" in position_str:
                # Format: chr1:1000 (single position)
                parts = position_str.split(":")
                chromosome = parts[0]
                position = int(parts[1])
                start = end = position

            else:
                # Format: chr1 or 1 (just chromosome)
                chromosome = position_str
                start = end = None

            # Validate chromosome
            if not cls.CHROMOSOME_PATTERN.match(chromosome):
                raise ValueError(f"Invalid chromosome format: {chromosome}")

            # Validate positions
            if start is not None and end is not None:
                if start < 1:
                    raise ValueError("Start position must be >= 1")
                if end < start:
                    raise ValueError("End position must be >= start position")

            return {
                "chromosome": chromosome.replace("CHR", "").replace("chr", ""),
                "start": start,
                "end": end,
                "original_string": position_str,
            }

        except ValueError as e:
            raise ValidationError(
                message=f"Failed to parse genomic position '{position_str}': {str(e)}",
                field_name="genomic_position",
                field_value=position_str,
            ) from e

    @classmethod
    def parse_variant_id(cls, variant_id: str) -> Dict[str, Any]:
        """
        Parse variant identifier.

        Args:
            variant_id: Variant identifier (e.g., "rs123456", "chr1:1000:A:T")

        Returns:
            Parsed variant information dictionary

        Raises:
            ValidationError: If variant ID format is invalid
        """
        try:
            variant_id = variant_id.strip()

            # Check for rsID
            if cls.RSID_PATTERN.match(variant_id):
                return {"type": "rsid", "rsid": variant_id, "original_id": variant_id}

            # Check for genomic position format
            if ":" in variant_id and variant_id.count(":") >= 1:
                parts = variant_id.split(":")
                chromosome = parts[0]

                if not cls.CHROMOSOME_PATTERN.match(chromosome):
                    raise ValueError(f"Invalid chromosome in variant ID: {chromosome}")

                # Parse position and alleles
                if len(parts) >= 2:
                    position_part = parts[1]
                    if "-" in position_part:
                        # Range format: chr1:1000-2000
                        raise ValueError("Range format not supported for variant IDs")

                    position = int(position_part)

                    # Extract alleles
                    ref_allele = None
                    alt_allele = None

                    if len(parts) >= 3:
                        alleles = parts[2].split(">")
                        if len(alleles) == 2:
                            ref_allele = alleles[0].upper()
                            alt_allele = alleles[1].upper()
                        elif len(alleles) == 1:
                            ref_allele = alleles[0].upper()

                    return {
                        "type": "genomic_position",
                        "chromosome": chromosome.replace("CHR", "").replace("chr", ""),
                        "position": position,
                        "ref_allele": ref_allele,
                        "alt_allele": alt_allele,
                        "original_id": variant_id,
                    }

            # Check for Ensembl variant format
            if variant_id.startswith("ENSV"):
                return {
                    "type": "ensembl_variant",
                    "ensembl_id": variant_id,
                    "original_id": variant_id,
                }

            # Unknown format
            raise ValueError(f"Unrecognized variant ID format: {variant_id}")

        except ValueError as e:
            raise ValidationError(
                message=f"Failed to parse variant ID '{variant_id}': {str(e)}",
                field_name="variant_id",
                field_value=variant_id,
            ) from e

    @classmethod
    def parse_gene_symbol(cls, gene_symbol: str) -> Dict[str, Any]:
        """
        Parse and normalize gene symbol.

        Args:
            gene_symbol: Gene symbol to parse

        Returns:
            Normalized gene symbol information

        Raises:
            ValidationError: If gene symbol is invalid
        """
        try:
            gene_symbol = gene_symbol.strip().upper()

            # Basic validation
            if not gene_symbol:
                raise ValueError("Gene symbol cannot be empty")

            # Remove common prefixes/suffixes
            gene_symbol = re.sub(r"^(GENE|PROTEIN)_", "", gene_symbol)
            gene_symbol = re.sub(r"_(GENE|PROTEIN)$", "", gene_symbol)

            # Check for valid gene symbol format
            # Most gene symbols are letters, numbers, and some special characters
            if not re.match(r"^[A-Z0-9\-_.]+$", gene_symbol):
                raise ValueError(f"Invalid gene symbol format: {gene_symbol}")

            # Check length (typical gene symbols are 1-20 characters)
            if len(gene_symbol) > 50:
                raise ValueError("Gene symbol too long")

            return {
                "symbol": gene_symbol,
                "original_symbol": gene_symbol,
                "is_valid": True,
            }

        except ValueError as e:
            raise ValidationError(
                message=f"Failed to parse gene symbol '{gene_symbol}': {str(e)}",
                field_name="gene_symbol",
                field_value=gene_symbol,
            ) from e


class JSONDataParser:
    """Parser for JSON data from genomic APIs."""

    @staticmethod
    def safe_parse_json(json_str: str) -> Dict[str, Any]:
        """
        Safely parse JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            Parsed JSON data

        Raises:
            DataFormatError: If JSON parsing fails
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise DataFormatError(
                message=f"Failed to parse JSON: {str(e)}",
                expected_format="JSON",
                actual_format="invalid_json",
            ) from e

    @staticmethod
    def extract_nested_value(
        data: Dict[str, Any], key_path: str, default: Any = None
    ) -> Any:
        """
        Extract nested value from dictionary using dot notation.

        Args:
            data: Dictionary to extract value from
            key_path: Dot-separated key path (e.g., "result.gene.symbol")
            default: Default value if key not found

        Returns:
            Extracted value or default
        """
        try:
            keys = key_path.split(".")
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default

            return current

        except (KeyError, TypeError, AttributeError):
            return default

    @staticmethod
    def flatten_dict(
        data: Dict[str, Any], parent_key: str = "", separator: str = "."
    ) -> Dict[str, Any]:
        """
        Flatten nested dictionary.

        Args:
            data: Dictionary to flatten
            parent_key: Parent key for nested items
            separator: Separator for nested keys

        Returns:
            Flattened dictionary
        """
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(
                    JSONDataParser.flatten_dict(value, new_key, separator).items()
                )
            elif isinstance(value, list):
                # Handle lists by creating indexed keys
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.extend(
                            JSONDataParser.flatten_dict(
                                item, f"{new_key}[{i}]", separator
                            ).items()
                        )
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, value))

        return dict(items)

    @staticmethod
    def clean_response_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean API response data by removing null values and normalizing.

        Args:
            data: Raw response data

        Returns:
            Cleaned response data
        """
        if not isinstance(data, dict):
            return data

        cleaned = {}
        for key, value in data.items():
            if value is None:
                continue
            elif isinstance(value, dict):
                cleaned_dict = JSONDataParser.clean_response_data(value)
                if cleaned_dict:  # Only add if not empty
                    cleaned[key] = cleaned_dict
            elif isinstance(value, list):
                cleaned_list = [
                    (
                        JSONDataParser.clean_response_data(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                    if item is not None
                ]
                if cleaned_list:  # Only add if not empty
                    cleaned[key] = cleaned_list
            else:
                cleaned[key] = value

        return cleaned


class BatchProcessor:
    """Utility for processing batch operations."""

    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
        """
        Split list into chunks of specified size.

        Args:
            items: List to chunk
            chunk_size: Size of each chunk

        Returns:
            List of chunks
        """
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")

        return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod
    def validate_batch_size(batch_size: int, max_size: int = 1000) -> int:
        """
        Validate and adjust batch size.

        Args:
            batch_size: Requested batch size
            max_size: Maximum allowed batch size

        Returns:
            Validated batch size
        """
        if batch_size <= 0:
            return 1
        elif batch_size > max_size:
            logger.warning(
                "Batch size %d exceeds maximum %d, using maximum", batch_size, max_size
            )
            return max_size
        else:
            return batch_size

    @staticmethod
    def merge_batch_results(
        results: List[Dict[str, Any]], key_field: str = "id"
    ) -> Dict[str, Any]:
        """
        Merge batch results into a single dictionary.

        Args:
            results: List of batch results
            key_field: Field to use as key in merged dictionary

        Returns:
            Merged results dictionary
        """
        merged = {}

        for result in results:
            if isinstance(result, dict) and key_field in result:
                key = result[key_field]
                merged[key] = result
            else:
                logger.warning(
                    "Skipping result without key field '%s': %s", key_field, result
                )

        return merged


class DataValidator:
    """Utility for data validation."""

    @staticmethod
    def validate_genomic_assembly(assembly: str) -> str:
        """
        Validate and normalize genome assembly name.

        Args:
            assembly: Genome assembly name

        Returns:
            Normalized assembly name

        Raises:
            ValidationError: If assembly is invalid
        """
        valid_assemblies = {
            "GRCH37",
            "HG19",  # Same assembly, different names
            "GRCH38",
            "HG38",  # Same assembly, different names
            "T2T-CHM13",
            "CHM13",
            "GRCM38",
            "MM10",  # Mouse
            "GRCM39",  # Mouse
        }

        assembly = assembly.upper().strip()

        if assembly not in valid_assemblies:
            raise ValidationError(
                message=f"Invalid genome assembly: {assembly}",
                field_name="assembly",
                field_value=assembly,
            )

        # Normalize to preferred names
        normalization_map = {
            "HG19": "GRCH37",
            "HG38": "GRCH38",
            "MM10": "GRCM38",
            "CHM13": "T2T-CHM13",
        }

        return normalization_map.get(assembly, assembly)

    @staticmethod
    def validate_species_name(species: str) -> str:
        """
        Validate and normalize species name.

        Args:
            species: Species name

        Returns:
            Normalized species name

        Raises:
            ValidationError: If species is invalid
        """
        # Common species mappings
        species_mappings = {
            "HUMAN": "HOMO_SAPIENS",
            "MOUSE": "MUS_MUSCULUS",
            "RAT": "RATTUS_NORVEGICUS",
            "DROSOPHILA": "DROSOPHILA_MELANOGASTER",
            "CELEGANS": "CAENORHABDITIS_ELEGANS",
            "YEAST": "SACCHAROMYCES_CEREVISIAE",
        }

        species = species.upper().strip().replace(" ", "_")

        # Apply normalization
        normalized = species_mappings.get(species, species)

        # Basic validation (should be more comprehensive in practice)
        if not re.match(r"^[A-Z_]+$", normalized):
            raise ValidationError(
                message=f"Invalid species name: {species}",
                field_name="species",
                field_value=species,
            )

        return normalized

    @staticmethod
    def validate_confidence_score(score: float) -> float:
        """
        Validate confidence score.

        Args:
            score: Confidence score

        Returns:
            Validated confidence score

        Raises:
            ValidationError: If score is invalid
        """
        if not (0.0 <= score <= 1.0):
            raise ValidationError(
                message=f"Confidence score must be between 0.0 and 1.0: {score}",
                field_name="confidence_score",
                field_value=score,
            )

        return round(score, 3)  # Round to 3 decimal places
