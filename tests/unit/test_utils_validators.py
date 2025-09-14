"""
Tests for validator utility functions.

This module contains tests for genomic, query, and API validators.
"""

import pytest
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data.validators import (
    GenomicValidator,
    QueryValidator,
    APIValidator,
)
from exceptions import ValidationError


class TestGenomicValidator:
    """Test genomic data validation functionality."""
    
    def test_validate_chromosome_valid(self):
        """Test validating valid chromosome names."""
        valid_chromosomes = [
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
            "13", "14", "15", "16", "17", "18", "19", "20", "21", "22",
            "X", "Y", "MT",
            "chr1", "chr2", "chrX", "chrY", "chrMT",
            "CHR1", "CHR2", "CHRX", "CHRY", "CHRMT"
        ]
        
        for chrom in valid_chromosomes:
            result = GenomicValidator.validate_chromosome(chrom)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_validate_chromosome_normalization(self):
        """Test chromosome name normalization."""
        assert GenomicValidator.validate_chromosome("chr1") == "1"
        assert GenomicValidator.validate_chromosome("CHR1") == "1"
        assert GenomicValidator.validate_chromosome("chrX") == "X"
        assert GenomicValidator.validate_chromosome("CHRMT") == "MT"
    
    def test_validate_chromosome_invalid(self):
        """Test validating invalid chromosome names."""
        invalid_chromosomes = [
            "0", "23", "24",  # Invalid numbers
            "chr0", "chr23",  # Invalid with prefix
            "chr",           # Just prefix
            "XY", "XX",       # Invalid combinations
            "M",             # Should be MT
            "",              # Empty
            "abc",           # Invalid format
        ]
        
        for chrom in invalid_chromosomes:
            with pytest.raises(ValidationError):
                GenomicValidator.validate_chromosome(chrom)
    
    def test_validate_genomic_position_valid(self):
        """Test validating valid genomic positions."""
        valid_positions = [
            (1, 1),      # Minimum position
            (1, 1000),   # Normal position
            (22, 50000000),  # Large position
        ]
        
        for chrom, pos in valid_positions:
            result = GenomicValidator.validate_genomic_position(chrom, pos)
            assert result["chromosome"] == str(chrom)
            assert result["position"] == pos
    
    def test_validate_genomic_position_with_ref_alt(self):
        """Test validating genomic position with ref/alt alleles."""
        result = GenomicValidator.validate_genomic_position(
            "1", 1000, ref="A", alt="T"
        )
        
        assert result["chromosome"] == "1"
        assert result["position"] == 1000
        assert result["ref_allele"] == "A"
        assert result["alt_allele"] == "T"
    
    def test_validate_genomic_position_invalid_chromosome(self):
        """Test genomic position with invalid chromosome."""
        with pytest.raises(ValidationError):
            GenomicValidator.validate_genomic_position("0", 1000)
    
    def test_validate_genomic_position_invalid_position(self):
        """Test genomic position with invalid position."""
        with pytest.raises(ValidationError):
            GenomicValidator.validate_genomic_position("1", 0)
        
        with pytest.raises(ValidationError):
            GenomicValidator.validate_genomic_position("1", -1)
    
    def test_validate_genomic_range_valid(self):
        """Test validating valid genomic ranges."""
        valid_ranges = [
            ("1", 1000, 2000),
            ("X", 1, 100),
            ("MT", 100, 200),
        ]
        
        for chrom, start, end in valid_ranges:
            result = GenomicValidator.validate_genomic_range(chrom, start, end)
            assert result["chromosome"] == str(chrom)
            assert result["start"] == start
            assert result["end"] == end
    
    def test_validate_genomic_range_invalid_order(self):
        """Test genomic range with invalid start/end order."""
        with pytest.raises(ValidationError):
            GenomicValidator.validate_genomic_range("1", 2000, 1000)
    
    def test_validate_genomic_range_equal_positions(self):
        """Test genomic range with equal start/end."""
        result = GenomicValidator.validate_genomic_range("1", 1000, 1000)
        assert result["start"] == 1000
        assert result["end"] == 1000
    
    def test_validate_allele_valid(self):
        """Test validating valid alleles."""
        valid_alleles = [
            "A", "T", "C", "G",  # Single nucleotides
            "AT", "CG", "TA", "GC",  # Dinucleotides
            "ATCG", "GCTA",  # Longer sequences
            "A", "a", "At", "aT",  # Case insensitive
            "",                # Empty allele (deletion)
        ]
        
        for allele in valid_alleles:
            result = GenomicValidator.validate_allele(allele)
            assert isinstance(result, str)
    
    def test_validate_allele_normalization(self):
        """Test allele normalization."""
        assert GenomicValidator.validate_allele("a") == "A"
        assert GenomicValidator.validate_allele("atcg") == "ATCG"
        assert GenomicValidator.validate_allele("AtCg") == "ATCG"
    
    def test_validate_allele_invalid(self):
        """Test validating invalid alleles."""
        invalid_alleles = [
            "N",          # Invalid nucleotide
            "ATCGN",      # Contains invalid nucleotide
            "123",        # Numbers
            "@#$",        # Special characters
            "A T",        # Contains space
        ]
        
        for allele in invalid_alleles:
            with pytest.raises(ValidationError):
                GenomicValidator.validate_allele(allele)
    
    def test_validate_genotype_valid(self):
        """Test validating valid genotypes."""
        valid_genotypes = [
            "A/A", "A/T", "T/C", "C/G", "G/A",
            "AA", "AT", "TC", "CG", "GA",
            "A|A", "A|T", "T|C", "C|G", "G|A",
            "0/0", "0/1", "1/0", "1/1",
            "0|0", "0|1", "1|0", "1|1",
        ]
        
        for genotype in valid_genotypes:
            result = GenomicValidator.validate_genotype(genotype)
            assert isinstance(result, str)
            assert "/" in result or "|" in result
    
    def test_validate_genotype_normalization(self):
        """Test genotype normalization."""
        assert GenomicValidator.validate_genotype("a/a") == "A/A"
        assert GenomicValidator.validate_genotype("A|a") == "A|A"
        assert GenomicValidator.validate_genotype("0/1") == "0/1"
    
    def test_validate_genotype_invalid(self):
        """Test validating invalid genotypes."""
        invalid_genotypes = [
            "",           # Empty
            "A",          # Single allele
            "A//A",       # Double separator
            "A/T/C",      # Three alleles
            "A/T/",       # Missing allele
            "/A/T",       # Missing allele
            "N/N",        # Invalid allele
            "A B",        # Space instead of separator
        ]
        
        for genotype in invalid_genotypes:
            with pytest.raises(ValidationError):
                GenomicValidator.validate_genotype(genotype)


class TestQueryValidator:
    """Test query validation functionality."""
    
    def test_validate_gene_query_valid(self):
        """Test validating valid gene queries."""
        valid_queries = [
            {"gene": "BRCA1"},
            {"genes": ["BRCA1", "TP53"]},
            {"gene_symbol": "EGFR"},
            {"gene_symbols": ["EGFR", "KRAS"]},
            {"gene_id": "ENSG00000141510"},
            {"gene_ids": ["ENSG00000141510", "ENSG00000133703"]},
        ]
        
        for query in valid_queries:
            result = QueryValidator.validate_gene_query(query)
            assert isinstance(result, dict)
            assert len(result) > 0
    
    def test_validate_gene_query_empty(self):
        """Test validating empty gene query."""
        with pytest.raises(ValidationError):
            QueryValidator.validate_gene_query({})
    
    def test_validate_gene_query_invalid(self):
        """Test validating invalid gene queries."""
        invalid_queries = [
            {"invalid": "query"},
            {"gene": ""},  # Empty gene name
            {"genes": []},  # Empty gene list
            {"genes": [""]},  # List with empty string
        ]
        
        for query in invalid_queries:
            with pytest.raises(ValidationError):
                QueryValidator.validate_gene_query(query)
    
    def test_validate_variant_query_valid(self):
        """Test validating valid variant queries."""
        valid_queries = [
            {"variant": "rs123456"},
            {"variants": ["rs123456", "rs789012"]},
            {"variant_id": "chr1:1000:A:T"},
            {"variant_ids": ["chr1:1000:A:T", "chr2:2000:C:G"]},
            {"position": {"chromosome": "1", "position": 1000}},
            {"range": {"chromosome": "1", "start": 1000, "end": 2000}},
            {"rsid": "rs123456"},
            {"rsids": ["rs123456", "rs789012"]},
        ]
        
        for query in valid_queries:
            result = QueryValidator.validate_variant_query(query)
            assert isinstance(result, dict)
            assert len(result) > 0
    
    def test_validate_variant_query_empty(self):
        """Test validating empty variant query."""
        with pytest.raises(ValidationError):
            QueryValidator.validate_variant_query({})
    
    def test_validate_variant_query_invalid(self):
        """Test validating invalid variant queries."""
        invalid_queries = [
            {"invalid": "query"},
            {"variant": ""},  # Empty variant
            {"variants": []},  # Empty variant list
            {"position": {}},  # Empty position
            {"range": {"chromosome": "1"}},  # Incomplete range
        ]
        
        for query in invalid_queries:
            with pytest.raises(ValidationError):
                QueryValidator.validate_variant_query(query)
    
    def test_validate_genomic_range_query_valid(self):
        """Test validating valid genomic range queries."""
        valid_queries = [
            {"chromosome": "1", "start": 1000, "end": 2000},
            {"chr": "X", "start": 1, "end": 100000},
            {"region": "chr1:1000-2000"},
            {"regions": ["chr1:1000-2000", "chr2:3000-4000"]},
        ]
        
        for query in valid_queries:
            result = QueryValidator.validate_genomic_range_query(query)
            assert isinstance(result, dict)
            assert "chromosome" in result or "regions" in result
    
    def test_validate_genomic_range_query_invalid(self):
        """Test validating invalid genomic range queries."""
        invalid_queries = [
            {"chromosome": "1", "start": 2000, "end": 1000},  # Invalid range
            {"region": "invalid"},  # Invalid region format
            {"regions": ["chr1:1000-2000", "invalid"]},  # Mixed valid/invalid
        ]
        
        for query in invalid_queries:
            with pytest.raises(ValidationError):
                QueryValidator.validate_genomic_range_query(query)
    
    def test_validate_search_parameters_valid(self):
        """Test validating valid search parameters."""
        valid_params = [
            {"query": "BRCA1", "limit": 10},
            {"q": "cancer", "page": 2, "page_size": 20},
            {"search": "gene therapy", "filters": {"species": "human"}},
            {"term": "mutation", "sort": "relevance", "order": "desc"},
        ]
        
        for params in valid_params:
            result = QueryValidator.validate_search_parameters(params)
            assert isinstance(result, dict)
            assert "query" in result or "q" in result or "search" in result or "term" in result
    
    def test_validate_search_parameters_invalid(self):
        """Test validating invalid search parameters."""
        invalid_params = [
            {},  # No search term
            {"query": ""},  # Empty query
            {"limit": -1},  # Invalid limit
            {"page": 0},  # Invalid page
            {"sort": "invalid_field"},  # Invalid sort field
        ]
        
        for params in invalid_params:
            with pytest.raises(ValidationError):
                QueryValidator.validate_search_parameters(params)
    
    def test_validate_pagination_parameters_valid(self):
        """Test validating valid pagination parameters."""
        valid_params = [
            {"page": 1, "page_size": 10},
            {"offset": 0, "limit": 20},
            {"page": 5, "per_page": 50},
        ]
        
        for params in valid_params:
            result = QueryValidator.validate_pagination_parameters(params)
            assert isinstance(result, dict)
            assert "page" in result or "offset" in result
    
    def test_validate_pagination_parameters_invalid(self):
        """Test validating invalid pagination parameters."""
        invalid_params = [
            {"page": 0},  # Invalid page
            {"page_size": 0},  # Invalid page size
            {"offset": -1},  # Invalid offset
            {"limit": 0},  # Invalid limit
            {"page": 1, "page_size": 1000},  # Page size too large
        ]
        
        for params in invalid_params:
            with pytest.raises(ValidationError):
                QueryValidator.validate_pagination_parameters(params)


class TestAPIValidator:
    """Test API validation functionality."""
    
    def test_validate_request_headers_valid(self):
        """Test validating valid request headers."""
        valid_headers = [
            {"Content-Type": "application/json"},
            {"Authorization": "Bearer token123"},
            {"Accept": "application/json"},
            {"User-Agent": "MyApp/1.0"},
            {"Content-Type": "application/json", "Authorization": "Bearer token"},
        ]
        
        for headers in valid_headers:
            result = APIValidator.validate_request_headers(headers)
            assert isinstance(result, dict)
    
    def test_validate_request_headers_invalid(self):
        """Test validating invalid request headers."""
        invalid_headers = [
            {},  # Empty headers
            {"": "value"},  # Empty header name
            {"name": ""},  # Empty header value
            {"Authorization": "Invalid token format"},  # Invalid auth format
        ]
        
        for headers in invalid_headers:
            with pytest.raises(ValidationError):
                APIValidator.validate_request_headers(headers)
    
    def test_validate_query_parameters_valid(self):
        """Test validating valid query parameters."""
        valid_params = [
            {"gene": "BRCA1"},
            {"limit": 10},
            {"format": "json"},
            {"gene": "BRCA1", "limit": 10, "format": "json"},
        ]
        
        for params in valid_params:
            result = APIValidator.validate_query_parameters(params)
            assert isinstance(result, dict)
    
    def test_validate_query_parameters_invalid(self):
        """Test validating invalid query parameters."""
        invalid_params = [
            {"limit": -1},  # Invalid limit
            {"format": "xml"},  # Unsupported format
            {"gene": ""},  # Empty gene name
        ]
        
        for params in invalid_params:
            with pytest.raises(ValidationError):
                APIValidator.validate_query_parameters(params)
    
    def test_validate_response_format_valid(self):
        """Test validating valid response formats."""
        valid_formats = [
            {"format": "json"},
            {"output": "json"},
            {"accept": "application/json"},
        ]
        
        for format_spec in valid_formats:
            result = APIValidator.validate_response_format(format_spec)
            assert isinstance(result, dict)
    
    def test_validate_response_format_invalid(self):
        """Test validating invalid response formats."""
        invalid_formats = [
            {"format": "xml"},  # Unsupported format
            {"output": "csv"},  # Unsupported format
            {"accept": "application/xml"},  # Unsupported content type
            {},  # No format specified
        ]
        
        for format_spec in invalid_formats:
            with pytest.raises(ValidationError):
                APIValidator.validate_response_format(format_spec)
    
    def test_validate_api_version_valid(self):
        """Test validating valid API versions."""
        valid_versions = [
            "v1",
            "v2",
            "1.0",
            "2.1",
            "latest",
        ]
        
        for version in valid_versions:
            result = APIValidator.validate_api_version(version)
            assert isinstance(result, str)
    
    def test_validate_api_version_invalid(self):
        """Test validating invalid API versions."""
        invalid_versions = [
            "",  # Empty version
            "v0",  # Invalid version
            "0.0",  # Invalid version
            "invalid",  # Invalid format
        ]
        
        for version in invalid_versions:
            with pytest.raises(ValidationError):
                APIValidator.validate_api_version(version)
    
    def test_validate_request_body_valid(self):
        """Test validating valid request body."""
        valid_bodies = [
            {"gene": "BRCA1"},
            {"variants": ["rs123456", "rs789012"]},
            {"query": "cancer genes", "limit": 10},
        ]
        
        for body in valid_bodies:
            result = APIValidator.validate_request_body(body)
            assert isinstance(result, dict)
    
    def test_validate_request_body_invalid(self):
        """Test validating invalid request body."""
        invalid_bodies = [
            {},  # Empty body
            {"gene": ""},  # Empty gene name
            {"variants": []},  # Empty variant list
            {"limit": -1},  # Invalid limit
        ]
        
        for body in invalid_bodies:
            with pytest.raises(ValidationError):
                APIValidator.validate_request_body(body)


if __name__ == "__main__":
    pytest.main([__file__])