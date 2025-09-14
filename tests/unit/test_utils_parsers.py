"""
Tests for data parser utility functions.

This module contains tests for genomic data parsers, JSON parsers, and batch processors.
"""

import pytest
import json
from typing import Dict, Any, List

from genome_mcp.utils.parsers import (
    GenomicDataParser,
    JSONDataParser,
    BatchProcessor,
    DataValidator,
)
from genome_mcp.exceptions import ValidationError, DataFormatError


class TestGenomicDataParser:
    """Test genomic data parsing functionality."""
    
    def test_parse_genomic_position_range(self):
        """Test parsing genomic position range."""
        position_str = "chr1:1000-2000"
        result = GenomicDataParser.parse_genomic_position(position_str)
        
        assert result["chromosome"] == "1"
        assert result["start"] == 1000
        assert result["end"] == 2000
        assert result["original_string"] == position_str
    
    def test_parse_genomic_position_single(self):
        """Test parsing single genomic position."""
        position_str = "chr1:1000"
        result = GenomicDataParser.parse_genomic_position(position_str)
        
        assert result["chromosome"] == "1"
        assert result["start"] == 1000
        assert result["end"] == 1000
        assert result["original_string"] == position_str
    
    def test_parse_genomic_position_chromosome_only(self):
        """Test parsing chromosome only."""
        position_str = "chr1"
        result = GenomicDataParser.parse_genomic_position(position_str)
        
        assert result["chromosome"] == "1"
        assert result["start"] is None
        assert result["end"] is None
        assert result["original_string"] == position_str
    
    def test_parse_genomic_position_uppercase(self):
        """Test parsing uppercase genomic position."""
        position_str = "CHR1:1000-2000"
        result = GenomicDataParser.parse_genomic_position(position_str)
        
        assert result["chromosome"] == "1"
        assert result["start"] == 1000
        assert result["end"] == 2000
    
    def test_parse_genomic_position_invalid_format(self):
        """Test parsing invalid genomic position format."""
        invalid_positions = [
            "invalid",
            "chr1:1000:2000",  # Too many colons
            "chr1:abc-def",    # Non-numeric positions
            "chrX:2000-1000",  # End < start
            "chr1:0-1000",     # Start < 1
        ]
        
        for position in invalid_positions:
            with pytest.raises(ValidationError):
                GenomicDataParser.parse_genomic_position(position)
    
    def test_parse_genomic_position_invalid_chromosome(self):
        """Test parsing invalid chromosome."""
        invalid_chromosomes = [
            "chr0",      # Invalid chromosome number
            "chr23",     # Invalid chromosome number
            "chrABC",    # Invalid chromosome name
        ]
        
        for chrom in invalid_chromosomes:
            with pytest.raises(ValidationError):
                GenomicDataParser.parse_genomic_position(chrom)
    
    def test_parse_variant_id_rsid(self):
        """Test parsing rsID variant."""
        variant_id = "rs123456"
        result = GenomicDataParser.parse_variant_id(variant_id)
        
        assert result["type"] == "rsid"
        assert result["rsid"] == variant_id
        assert result["original_id"] == variant_id
    
    def test_parse_variant_id_genomic_position(self):
        """Test parsing genomic position variant."""
        variant_id = "chr1:1000:A:T"
        result = GenomicDataParser.parse_variant_id(variant_id)
        
        assert result["type"] == "genomic_position"
        assert result["chromosome"] == "1"
        assert result["position"] == 1000
        assert result["ref_allele"] == "A"
        assert result["alt_allele"] == "T"
        assert result["original_id"] == variant_id
    
    def test_parse_variant_id_ensembl(self):
        """Test parsing Ensembl variant ID."""
        variant_id = "ENSV00000123456"
        result = GenomicDataParser.parse_variant_id(variant_id)
        
        assert result["type"] == "ensembl_variant"
        assert result["ensembl_id"] == variant_id
        assert result["original_id"] == variant_id
    
    def test_parse_variant_id_invalid_format(self):
        """Test parsing invalid variant ID format."""
        invalid_variants = [
            "invalid",
            "chr1:1000-2000",  # Range not supported
            "rsabc",          # Invalid rsID
        ]
        
        for variant in invalid_variants:
            with pytest.raises(ValidationError):
                GenomicDataParser.parse_variant_id(variant)
    
    def test_parse_gene_symbol_basic(self):
        """Test parsing basic gene symbol."""
        gene_symbol = "BRCA1"
        result = GenomicDataParser.parse_gene_symbol(gene_symbol)
        
        assert result["symbol"] == "BRCA1"
        assert result["original_symbol"] == "BRCA1"
        assert result["is_valid"] is True
    
    def test_parse_gene_symbol_with_prefix(self):
        """Test parsing gene symbol with prefix."""
        gene_symbols = ["GENE_BRCA1", "BRCA1_GENE", "PROTEIN_BRCA1", "BRCA1_PROTEIN"]
        
        for symbol in gene_symbols:
            result = GenomicDataParser.parse_gene_symbol(symbol)
            assert result["symbol"] == "BRCA1"
            assert result["is_valid"] is True
    
    def test_parse_gene_symbol_case_insensitive(self):
        """Test parsing gene symbol case insensitivity."""
        gene_symbol = "brca1"
        result = GenomicDataParser.parse_gene_symbol(gene_symbol)
        
        assert result["symbol"] == "BRCA1"
        assert result["is_valid"] is True
    
    def test_parse_gene_symbol_invalid(self):
        """Test parsing invalid gene symbols."""
        invalid_genes = [
            "",          # Empty
            "   ",       # Whitespace only
            "A" * 100,   # Too long
            "gene@",      # Invalid characters
        ]
        
        for gene in invalid_genes:
            with pytest.raises(ValidationError):
                GenomicDataParser.parse_gene_symbol(gene)


class TestJSONDataParser:
    """Test JSON data parsing functionality."""
    
    def test_safe_parse_json_valid(self):
        """Test parsing valid JSON."""
        json_str = '{"key": "value", "number": 123}'
        result = JSONDataParser.safe_parse_json(json_str)
        
        assert result == {"key": "value", "number": 123}
    
    def test_safe_parse_json_invalid(self):
        """Test parsing invalid JSON."""
        invalid_jsons = [
            "not json",
            '{"key": "value",}',  # Trailing comma
            "{key: value}",      # Unquoted keys
            "",                  # Empty string
        ]
        
        for json_str in invalid_jsons:
            with pytest.raises(DataFormatError):
                JSONDataParser.safe_parse_json(json_str)
    
    def test_extract_nested_value_simple(self):
        """Test extracting simple nested value."""
        data = {"a": {"b": {"c": "value"}}}
        result = JSONDataParser.extract_nested_value(data, "a.b.c")
        
        assert result == "value"
    
    def test_extract_nested_value_default(self):
        """Test extracting nested value with default."""
        data = {"a": {"b": "value"}}
        result = JSONDataParser.extract_nested_value(data, "a.b.c", "default")
        
        assert result == "default"
    
    def test_extract_nested_value_missing_key(self):
        """Test extracting nested value with missing key."""
        data = {"a": {"b": "value"}}
        result = JSONDataParser.extract_nested_value(data, "a.x.y", "default")
        
        assert result == "default"
    
    def test_extract_nested_value_non_dict(self):
        """Test extracting nested value from non-dict."""
        data = {"a": "not a dict"}
        result = JSONDataParser.extract_nested_value(data, "a.b", "default")
        
        assert result == "default"
    
    def test_flatten_dict_simple(self):
        """Test flattening simple dictionary."""
        data = {"a": 1, "b": 2}
        result = JSONDataParser.flatten_dict(data)
        
        assert result == {"a": 1, "b": 2}
    
    def test_flatten_dict_nested(self):
        """Test flattening nested dictionary."""
        data = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3
                }
            },
            "f": 4
        }
        result = JSONDataParser.flatten_dict(data)
        
        expected = {
            "a": 1,
            "b.c": 2,
            "b.d.e": 3,
            "f": 4
        }
        assert result == expected
    
    def test_flatten_dict_with_lists(self):
        """Test flattening dictionary with lists."""
        data = {
            "a": [1, 2, 3],
            "b": {
                "c": [{"x": 1}, {"y": 2}]
            }
        }
        result = JSONDataParser.flatten_dict(data)
        
        assert "a[0]" in result
        assert "a[1]" in result
        assert "a[2]" in result
        assert "b.c[0].x" in result
        assert "b.c[1].y" in result
    
    def test_flatten_dict_custom_separator(self):
        """Test flattening dictionary with custom separator."""
        data = {"a": {"b": {"c": "value"}}}
        result = JSONDataParser.flatten_dict(data, separator="_")
        
        assert result == {"a_b_c": "value"}
    
    def test_clean_response_data_simple(self):
        """Test cleaning simple response data."""
        data = {"a": 1, "b": None, "c": "value"}
        result = JSONDataParser.clean_response_data(data)
        
        assert result == {"a": 1, "c": "value"}
    
    def test_clean_response_data_nested(self):
        """Test cleaning nested response data."""
        data = {
            "a": 1,
            "b": {
                "c": None,
                "d": {
                    "e": None,
                    "f": "value"
                }
            },
            "g": None
        }
        result = JSONDataParser.clean_response_data(data)
        
        expected = {
            "a": 1,
            "b": {
                "d": {
                    "f": "value"
                }
            }
        }
        assert result == expected
    
    def test_clean_response_data_with_lists(self):
        """Test cleaning response data with lists."""
        data = {
            "a": [1, None, 3],
            "b": [
                {"x": None},
                {"y": "value"},
                None
            ]
        }
        result = JSONDataParser.clean_response_data(data)
        
        assert result == {
            "a": [1, 3],
            "b": [
                {},
                {"y": "value"}
            ]
        }
    
    def test_clean_response_data_non_dict(self):
        """Test cleaning non-dict response data."""
        data = [1, 2, 3]
        result = JSONDataParser.clean_response_data(data)
        
        assert result == data


class TestBatchProcessor:
    """Test batch processing functionality."""
    
    def test_chunk_list_basic(self):
        """Test basic list chunking."""
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = BatchProcessor.chunk_list(items, 3)
        
        expected = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
        assert result == expected
    
    def test_chunk_list_exact(self):
        """Test chunking exact division."""
        items = [1, 2, 3, 4, 5, 6]
        result = BatchProcessor.chunk_list(items, 3)
        
        expected = [[1, 2, 3], [4, 5, 6]]
        assert result == expected
    
    def test_chunk_list_single_item(self):
        """Test chunking single item."""
        items = [1, 2, 3]
        result = BatchProcessor.chunk_list(items, 1)
        
        expected = [[1], [2], [3]]
        assert result == expected
    
    def test_chunk_list_invalid_size(self):
        """Test chunking with invalid size."""
        with pytest.raises(ValueError):
            BatchProcessor.chunk_list([1, 2, 3], 0)
        
        with pytest.raises(ValueError):
            BatchProcessor.chunk_list([1, 2, 3], -1)
    
    def test_validate_batch_size_valid(self):
        """Test validating valid batch size."""
        assert BatchProcessor.validate_batch_size(10, max_size=100) == 10
        assert BatchProcessor.validate_batch_size(5, max_size=10) == 5
    
    def test_validate_batch_size_too_small(self):
        """Test validating batch size too small."""
        assert BatchProcessor.validate_batch_size(0) == 1
        assert BatchProcessor.validate_batch_size(-1) == 1
    
    def test_validate_batch_size_too_large(self):
        """Test validating batch size too large."""
        assert BatchProcessor.validate_batch_size(150, max_size=100) == 100
    
    def test_merge_batch_results_basic(self):
        """Test merging basic batch results."""
        results = [
            {"id": 1, "data": "a"},
            {"id": 2, "data": "b"},
            {"id": 3, "data": "c"}
        ]
        result = BatchProcessor.merge_batch_results(results)
        
        expected = {
            1: {"id": 1, "data": "a"},
            2: {"id": 2, "data": "b"},
            3: {"id": 3, "data": "c"}
        }
        assert result == expected
    
    def test_merge_batch_results_custom_key(self):
        """Test merging batch results with custom key."""
        results = [
            {"key": "a", "value": 1},
            {"key": "b", "value": 2}
        ]
        result = BatchProcessor.merge_batch_results(results, key_field="key")
        
        expected = {
            "a": {"key": "a", "value": 1},
            "b": {"key": "b", "value": 2}
        }
        assert result == expected
    
    def test_merge_batch_results_missing_key(self):
        """Test merging batch results with missing keys."""
        results = [
            {"id": 1, "data": "a"},
            {"data": "b"},  # Missing id
            {"id": 3, "data": "c"}
        ]
        result = BatchProcessor.merge_batch_results(results)
        
        expected = {
            1: {"id": 1, "data": "a"},
            3: {"id": 3, "data": "c"}
        }
        assert result == expected


class TestDataValidator:
    """Test data validation functionality."""
    
    def test_validate_genomic_assembly_valid(self):
        """Test validating valid genome assemblies."""
        valid_assemblies = [
            "GRCH37", "HG19",  # Same assembly
            "GRCH38", "HG38",  # Same assembly
            "T2T-CHM13", "CHM13",
            "GRCM38", "MM10",  # Mouse
            "GRCM39",          # Mouse
        ]
        
        for assembly in valid_assemblies:
            result = DataValidator.validate_genomic_assembly(assembly)
            assert isinstance(result, str)
    
    def test_validate_genomic_assembly_case_insensitive(self):
        """Test validating assembly case insensitivity."""
        assert DataValidator.validate_genomic_assembly("grch37") == "GRCH37"
        assert DataValidator.validate_genomic_assembly("hg38") == "GRCH38"
        assert DataValidator.validate_genomic_assembly("mm10") == "GRCM38"
    
    def test_validate_genomic_assembly_normalization(self):
        """Test assembly normalization."""
        assert DataValidator.validate_genomic_assembly("HG19") == "GRCH37"
        assert DataValidator.validate_genomic_assembly("HG38") == "GRCH38"
        assert DataValidator.validate_genomic_assembly("MM10") == "GRCM38"
        assert DataValidator.validate_genomic_assembly("CHM13") == "T2T-CHM13"
    
    def test_validate_genomic_assembly_invalid(self):
        """Test validating invalid genome assemblies."""
        invalid_assemblies = [
            "INVALID",
            "GRCH36",
            "UNKNOWN",
            "",
        ]
        
        for assembly in invalid_assemblies:
            with pytest.raises(ValidationError):
                DataValidator.validate_genomic_assembly(assembly)
    
    def test_validate_species_name_valid(self):
        """Test validating valid species names."""
        valid_species = [
            "HOMO_SAPIENS",
            "MUS_MUSCULUS",
            "RATTUS_NORVEGICUS",
            "DROSOPHILA_MELANOGASTER",
            "CAENORHABDITIS_ELEGANS",
            "SACCHAROMYCES_CEREVISIAE",
        ]
        
        for species in valid_species:
            result = DataValidator.validate_species_name(species)
            assert isinstance(result, str)
    
    def test_validate_species_name_normalization(self):
        """Test species name normalization."""
        assert DataValidator.validate_species_name("human") == "HOMO_SAPIENS"
        assert DataValidator.validate_species_name("mouse") == "MUS_MUSCULUS"
        assert DataValidator.validate_species_name("rat") == "RATTUS_NORVEGICUS"
        assert DataValidator.validate_species_name("drosophila") == "DROSOPHILA_MELANOGASTER"
    
    def test_validate_species_name_case_and_spaces(self):
        """Test species name case and space handling."""
        assert DataValidator.validate_species_name("Human") == "HOMO_SAPIENS"
        assert DataValidator.validate_species_name("Mus musculus") == "MUS_MUSCULUS"
        assert DataValidator.validate_species_name("  RAT  ") == "RATTUS_NORVEGICUS"
    
    def test_validate_species_name_invalid(self):
        """Test validating invalid species names."""
        invalid_species = [
            "invalid_species",
            "Homo@Sapiens",
            "123",
            "",
        ]
        
        for species in invalid_species:
            with pytest.raises(ValidationError):
                DataValidator.validate_species_name(species)
    
    def test_validate_confidence_score_valid(self):
        """Test validating valid confidence scores."""
        valid_scores = [0.0, 0.5, 1.0, 0.123, 0.999]
        
        for score in valid_scores:
            result = DataValidator.validate_confidence_score(score)
            assert 0.0 <= result <= 1.0
            assert isinstance(result, float)
    
    def test_validate_confidence_score_rounding(self):
        """Test confidence score rounding."""
        result = DataValidator.validate_confidence_score(0.123456)
        assert result == 0.123
        
        result = DataValidator.validate_confidence_score(0.999999)
        assert result == 1.0
    
    def test_validate_confidence_score_invalid(self):
        """Test validating invalid confidence scores."""
        invalid_scores = [-0.1, 1.1, 2.0, -1.0]
        
        for score in invalid_scores:
            with pytest.raises(ValidationError):
                DataValidator.validate_confidence_score(score)


if __name__ == "__main__":
    pytest.main([__file__])