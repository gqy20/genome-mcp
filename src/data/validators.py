"""
Validation utilities for Genome MCP.

This module provides validation functions for various genomic data types
and query parameters.
"""

import re
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import structlog

from exceptions import ValidationError, create_error_from_exception

logger = structlog.get_logger(__name__)


class GenomicValidator:
    """Validator for genomic data types."""
    
    # Genomic coordinate patterns
    CHROMOSOME_PATTERN = re.compile(r'^(chr)?([1-9]|1[0-9]|2[0-2]|X|Y|MT?)$', re.IGNORECASE)
    GENOMIC_POSITION_PATTERN = re.compile(r'^(\d+):(\d+)(?:-(\d+))?$')
    RSID_PATTERN = re.compile(r'^rs\d+$')
    HGVS_PATTERN = re.compile(r'^[A-Z]+:[gcmnprp]\.[\dACGTN_>+-]+$')
    
    @classmethod
    def validate_chromosome(cls, chromosome: str) -> str:
        """
        Validate chromosome name.
        
        Args:
            chromosome: Chromosome name
            
        Returns:
            Normalized chromosome name
            
        Raises:
            ValidationError: If chromosome is invalid
        """
        if not chromosome:
            raise ValidationError(
                message="Chromosome cannot be empty",
                field_name="chromosome",
                field_value=chromosome
            )
        
        chromosome = chromosome.strip().upper()
        
        if not cls.CHROMOSOME_PATTERN.match(chromosome):
            raise ValidationError(
                message=f"Invalid chromosome format: {chromosome}",
                field_name="chromosome",
                field_value=chromosome
            )
        
        # Normalize chromosome name
        chromosome = chromosome.replace('CHR', '').replace('chr', '')
        
        # Handle special cases
        if chromosome == 'M':
            chromosome = 'MT'
        
        return chromosome
    
    @classmethod
    def validate_genomic_position(cls, position: int, chromosome: Optional[str] = None) -> int:
        """
        Validate genomic position.
        
        Args:
            position: Genomic position
            chromosome: Optional chromosome name for context
            
        Returns:
            Validated position
            
        Raises:
            ValidationError: If position is invalid
        """
        if not isinstance(position, int):
            raise ValidationError(
                message="Genomic position must be an integer",
                field_name="position",
                field_value=position
            )
        
        if position < 1:
            raise ValidationError(
                message=f"Genomic position must be >= 1: {position}",
                field_name="position",
                field_value=position
            )
        
        # Chromosome-specific validation
        if chromosome:
            normalized_chr = cls.validate_chromosome(chromosome)
            max_positions = {
                '1': 248956422,
                '2': 242193529,
                '3': 198295559,
                '4': 190214555,
                '5': 181538259,
                '6': 170805979,
                '7': 159345973,
                '8': 145138636,
                '9': 138394717,
                '10': 133797422,
                '11': 135086622,
                '12': 133275309,
                '13': 114364328,
                '14': 107043718,
                '15': 101991189,
                '16': 90338345,
                '17': 83257441,
                '18': 80373285,
                '19': 58617616,
                '20': 64444167,
                '21': 46709983,
                '22': 50818468,
                'X': 156040895,
                'Y': 57227415,
                'MT': 16569,
            }
            
            if normalized_chr in max_positions and position > max_positions[normalized_chr]:
                raise ValidationError(
                    message=f"Position {position} exceeds chromosome {normalized_chr} length",
                    field_name="position",
                    field_value=position
                )
        
        return position
    
    @classmethod
    def validate_genomic_range(cls, start: int, end: int) -> Tuple[int, int]:
        """
        Validate genomic range.
        
        Args:
            start: Start position
            end: End position
            
        Returns:
            Validated (start, end) tuple
            
        Raises:
            ValidationError: If range is invalid
        """
        start = cls.validate_genomic_position(start)
        end = cls.validate_genomic_position(end)
        
        if end < start:
            raise ValidationError(
                message=f"End position {end} must be >= start position {start}",
                field_name="genomic_range",
                field_value={"start": start, "end": end}
            )
        
        # Validate range size (max 10MB for typical queries)
        max_range_size = 10_000_000
        range_size = end - start + 1
        
        if range_size > max_range_size:
            raise ValidationError(
                message=f"Range size {range_size} exceeds maximum allowed {max_range_size}",
                field_name="genomic_range",
                field_value={"start": start, "end": end}
            )
        
        return start, end
    
    @classmethod
    def validate_ref_allele(cls, allele: str) -> str:
        """
        Validate reference allele.
        
        Args:
            allele: Reference allele sequence
            
        Returns:
            Validated reference allele
            
        Raises:
            ValidationError: If allele is invalid
        """
        if not allele:
            raise ValidationError(
                message="Reference allele cannot be empty",
                field_name="ref_allele",
                field_value=allele
            )
        
        allele = allele.upper().strip()
        
        # Check for valid nucleotides
        valid_nucleotides = set('ACGTN')
        if not all(c in valid_nucleotides for c in allele):
            invalid_chars = set(allele) - valid_nucleotides
            raise ValidationError(
                message=f"Invalid nucleotides in reference allele: {', '.join(invalid_chars)}",
                field_name="ref_allele",
                field_value=allele
            )
        
        # Validate length (max 100bp for typical variants)
        if len(allele) > 100:
            raise ValidationError(
                message=f"Reference allele too long: {len(allele)} bp (max 100)",
                field_name="ref_allele",
                field_value=allele
            )
        
        return allele
    
    @classmethod
    def validate_alt_allele(cls, allele: str, ref_allele: str) -> str:
        """
        Validate alternate allele.
        
        Args:
            allele: Alternate allele sequence
            ref_allele: Reference allele for comparison
            
        Returns:
            Validated alternate allele
            
        Raises:
            ValidationError: If allele is invalid
        """
        if not allele:
            raise ValidationError(
                message="Alternate allele cannot be empty",
                field_name="alt_allele",
                field_value=allele
            )
        
        allele = allele.upper().strip()
        
        # Check for valid nucleotides
        valid_nucleotides = set('ACGTN')
        if not all(c in valid_nucleotides for c in allele):
            invalid_chars = set(allele) - valid_nucleotides
            raise ValidationError(
                message=f"Invalid nucleotides in alternate allele: {', '.join(invalid_chars)}",
                field_name="alt_allele",
                field_value=allele
            )
        
        # Check that alternate is different from reference
        if allele == ref_allele:
            raise ValidationError(
                message="Alternate allele must be different from reference allele",
                field_name="alt_allele",
                field_value=allele
            )
        
        # Validate length (max 100bp for typical variants)
        if len(allele) > 100:
            raise ValidationError(
                message=f"Alternate allele too long: {len(allele)} bp (max 100)",
                field_name="alt_allele",
                field_value=allele
            )
        
        return allele
    
    @classmethod
    def validate_rsid(cls, rsid: str) -> str:
        """
        Validate RSID format.
        
        Args:
            rsid: RSID string
            
        Returns:
            Validated RSID
            
        Raises:
            ValidationError: If RSID is invalid
        """
        if not rsid:
            raise ValidationError(
                message="RSID cannot be empty",
                field_name="rsid",
                field_value=rsid
            )
        
        rsid = rsid.strip()
        
        if not cls.RSID_PATTERN.match(rsid):
            raise ValidationError(
                message=f"Invalid RSID format: {rsid} (expected format: rs123456)",
                field_name="rsid",
                field_value=rsid
            )
        
        return rsid
    
    @classmethod
    def validate_gene_symbol(cls, symbol: str) -> str:
        """
        Validate gene symbol.
        
        Args:
            symbol: Gene symbol
            
        Returns:
            Validated gene symbol
            
        Raises:
            ValidationError: If gene symbol is invalid
        """
        if not symbol:
            raise ValidationError(
                message="Gene symbol cannot be empty",
                field_name="gene_symbol",
                field_value=symbol
            )
        
        symbol = symbol.strip().upper()
        
        # Basic format validation
        if not re.match(r'^[A-Z0-9\-_.]+$', symbol):
            raise ValidationError(
                message=f"Invalid gene symbol format: {symbol}",
                field_name="gene_symbol",
                field_value=symbol
            )
        
        # Length validation
        if len(symbol) > 50:
            raise ValidationError(
                message=f"Gene symbol too long: {len(symbol)} characters (max 50)",
                field_name="gene_symbol",
                field_value=symbol
            )
        
        # Remove common prefixes/suffixes
        symbol = re.sub(r'^(GENE|PROTEIN)_', '', symbol)
        symbol = re.sub(r'_(GENE|PROTEIN)$', '', symbol)
        
        return symbol


class QueryValidator:
    """Validator for query parameters."""
    
    @classmethod
    def validate_page_number(cls, page: int) -> int:
        """
        Validate page number.
        
        Args:
            page: Page number
            
        Returns:
            Validated page number
            
        Raises:
            ValidationError: If page number is invalid
        """
        if not isinstance(page, int):
            raise ValidationError(
                message="Page number must be an integer",
                field_name="page",
                field_value=page
            )
        
        if page < 1:
            raise ValidationError(
                message=f"Page number must be >= 1: {page}",
                field_name="page",
                field_value=page
            )
        
        return page
    
    @classmethod
    def validate_page_size(cls, page_size: int, max_size: int = 100) -> int:
        """
        Validate page size.
        
        Args:
            page_size: Page size
            max_size: Maximum allowed page size
            
        Returns:
            Validated page size
            
        Raises:
            ValidationError: If page size is invalid
        """
        if not isinstance(page_size, int):
            raise ValidationError(
                message="Page size must be an integer",
                field_name="page_size",
                field_value=page_size
            )
        
        if page_size < 1:
            raise ValidationError(
                message=f"Page size must be >= 1: {page_size}",
                field_name="page_size",
                field_value=page_size
            )
        
        if page_size > max_size:
            raise ValidationError(
                message=f"Page size {page_size} exceeds maximum {max_size}",
                field_name="page_size",
                field_value=page_size
            )
        
        return page_size
    
    @classmethod
    def validate_timeout(cls, timeout: float, min_timeout: float = 1.0, max_timeout: float = 300.0) -> float:
        """
        Validate timeout value.
        
        Args:
            timeout: Timeout value in seconds
            min_timeout: Minimum allowed timeout
            max_timeout: Maximum allowed timeout
            
        Returns:
            Validated timeout
            
        Raises:
            ValidationError: If timeout is invalid
        """
        if not isinstance(timeout, (int, float)):
            raise ValidationError(
                message="Timeout must be a number",
                field_name="timeout",
                field_value=timeout
            )
        
        if timeout < min_timeout:
            raise ValidationError(
                message=f"Timeout {timeout} is less than minimum {min_timeout}",
                field_name="timeout",
                field_value=timeout
            )
        
        if timeout > max_timeout:
            raise ValidationError(
                message=f"Timeout {timeout} exceeds maximum {max_timeout}",
                field_name="timeout",
                field_value=timeout
            )
        
        return float(timeout)
    
    @classmethod
    def validate_batch_size(cls, batch_size: int, max_size: int = 1000) -> int:
        """
        Validate batch size.
        
        Args:
            batch_size: Batch size
            max_size: Maximum allowed batch size
            
        Returns:
            Validated batch size
            
        Raises:
            ValidationError: If batch size is invalid
        """
        if not isinstance(batch_size, int):
            raise ValidationError(
                message="Batch size must be an integer",
                field_name="batch_size",
                field_value=batch_size
            )
        
        if batch_size < 1:
            raise ValidationError(
                message=f"Batch size must be >= 1: {batch_size}",
                field_name="batch_size",
                field_value=batch_size
            )
        
        if batch_size > max_size:
            raise ValidationError(
                message=f"Batch size {batch_size} exceeds maximum {max_size}",
                field_name="batch_size",
                field_value=batch_size
            )
        
        return batch_size
    
    @classmethod
    def validate_confidence_threshold(cls, threshold: float) -> float:
        """
        Validate confidence threshold.
        
        Args:
            threshold: Confidence threshold (0.0 to 1.0)
            
        Returns:
            Validated threshold
            
        Raises:
            ValidationError: If threshold is invalid
        """
        if not isinstance(threshold, (int, float)):
            raise ValidationError(
                message="Confidence threshold must be a number",
                field_name="confidence_threshold",
                field_value=threshold
            )
        
        threshold = float(threshold)
        
        if not (0.0 <= threshold <= 1.0):
            raise ValidationError(
                message=f"Confidence threshold must be between 0.0 and 1.0: {threshold}",
                field_name="confidence_threshold",
                field_value=threshold
            )
        
        return round(threshold, 3)


class APIValidator:
    """Validator for API-related parameters."""
    
    @classmethod
    def validate_url(cls, url: str) -> str:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            Validated URL
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not url:
            raise ValidationError(
                message="URL cannot be empty",
                field_name="url",
                field_value=url
            )
        
        url = url.strip()
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP address
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(url):
            raise ValidationError(
                message=f"Invalid URL format: {url}",
                field_name="url",
                field_value=url
            )
        
        return url
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> str:
        """
        Validate API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            Validated API key
            
        Raises:
            ValidationError: If API key is invalid
        """
        if not api_key:
            raise ValidationError(
                message="API key cannot be empty",
                field_name="api_key",
                field_value=api_key
            )
        
        api_key = api_key.strip()
        
        # Basic validation - API keys are typically alphanumeric with some special chars
        if len(api_key) < 8:
            raise ValidationError(
                message=f"API key too short: {len(api_key)} characters (min 8)",
                field_name="api_key",
                field_value=api_key
            )
        
        if len(api_key) > 500:
            raise ValidationError(
                message=f"API key too long: {len(api_key)} characters (max 500)",
                field_name="api_key",
                field_value=api_key
            )
        
        # Check for reasonable characters
        if not re.match(r'^[A-Za-z0-9\-_.+/+=]+$', api_key):
            raise ValidationError(
                message=f"Invalid API key format: {api_key}",
                field_name="api_key",
                field_value=api_key
            )
        
        return api_key


class DataValidator:
    """General data validation utilities."""
    
    @staticmethod
    def validate_non_empty_string(value: str, field_name: str) -> str:
        """
        Validate that a string is not empty.
        
        Args:
            value: String to validate
            field_name: Name of the field for error messages
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If string is empty
        """
        if not isinstance(value, str):
            raise ValidationError(
                message=f"{field_name} must be a string",
                field_name=field_name,
                field_value=value
            )
        
        value = value.strip()
        
        if not value:
            raise ValidationError(
                message=f"{field_name} cannot be empty",
                field_name=field_name,
                field_value=value
            )
        
        return value
    
    @staticmethod
    def validate_string_length(value: str, min_length: int, max_length: int, field_name: str) -> str:
        """
        Validate string length.
        
        Args:
            value: String to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            field_name: Name of the field for error messages
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If string length is invalid
        """
        if not isinstance(value, str):
            raise ValidationError(
                message=f"{field_name} must be a string",
                field_name=field_name,
                field_value=value
            )
        
        if len(value) < min_length:
            raise ValidationError(
                message=f"{field_name} too short: {len(value)} characters (min {min_length})",
                field_name=field_name,
                field_value=value
            )
        
        if len(value) > max_length:
            raise ValidationError(
                message=f"{field_name} too long: {len(value)} characters (max {max_length})",
                field_name=field_name,
                field_value=value
            )
        
        return value
    
    @staticmethod
    def validate_enum_value(value: str, allowed_values: List[str], field_name: str) -> str:
        """
        Validate enum value.
        
        Args:
            value: Value to validate
            allowed_values: List of allowed values
            field_name: Name of the field for error messages
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If value is not allowed
        """
        if value not in allowed_values:
            raise ValidationError(
                message=f"Invalid {field_name}: {value}. Allowed values: {', '.join(allowed_values)}",
                field_name=field_name,
                field_value=value
            )
        
        return value
    
    @staticmethod
    def validate_numeric_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float], field_name: str) -> Union[int, float]:
        """
        Validate numeric range.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Name of the field for error messages
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If value is out of range
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(
                message=f"{field_name} must be a number",
                field_name=field_name,
                field_value=value
            )
        
        if value < min_val:
            raise ValidationError(
                message=f"{field_name} {value} is less than minimum {min_val}",
                field_name=field_name,
                field_value=value
            )
        
        if value > max_val:
            raise ValidationError(
                message=f"{field_name} {value} exceeds maximum {max_val}",
                field_name=field_name,
                field_value=value
            )
        
        return value