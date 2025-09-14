"""
Tests for core type definitions.

This module contains tests for all type definitions in the types module.
"""

import pytest
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from type_defs.common import DataSource, ConfidenceLevel, APIResponse, PaginationParams
from type_defs.gene import GeneQuery, GeneInfo, GeneLocation, GeneResponse
from type_defs.variant import VariantQuery, VariantInfo, GenomicPosition, VariantResponse


class TestCommonTypes:
    """Test common type definitions."""
    
    def test_data_source_enum(self):
        """Test DataSource enum."""
        assert DataSource.NCBI == "ncbi"
        assert DataSource.ENSEMBL == "ensembl"
        assert DataSource.DBSNP == "dbsnp"
        assert DataSource.CLINVAR == "clinvar"
        assert DataSource.UNKNOWN == "unknown"
    
    def test_confidence_level_enum(self):
        """Test ConfidenceLevel enum."""
        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.LOW == "low"
        assert ConfidenceLevel.UNKNOWN == "unknown"
    
    def test_api_response(self):
        """Test APIResponse model."""
        response = APIResponse(
            success=True,
            data={"test": "data"},
            source=DataSource.NCBI
        )
        assert response.success is True
        assert response.data == {"test": "data"}
        assert response.source == DataSource.NCBI
        assert isinstance(response.timestamp, datetime)
    
    def test_pagination_params(self):
        """Test PaginationParams model."""
        params = PaginationParams(page=2, page_size=50)
        assert params.page == 2
        assert params.page_size == 50
    
    def test_pagination_params_validation(self):
        """Test PaginationParams validation."""
        # Valid page
        params = PaginationParams(page=1, page_size=100)
        assert params.page == 1
        assert params.page_size == 100
        
        # Invalid page (too small)
        with pytest.raises(ValueError):
            PaginationParams(page=0, page_size=20)
        
        # Invalid page_size (too large)
        with pytest.raises(ValueError):
            PaginationParams(page=1, page_size=101)


class TestGeneTypes:
    """Test gene-related type definitions."""
    
    def test_gene_query_validation(self):
        """Test GeneQuery validation."""
        # Valid query
        query = GeneQuery(gene_symbol="TP53", species="homo_sapiens")
        assert query.gene_symbol == "TP53"
        assert query.species == "homo_sapiens"
        
        # Test gene symbol normalization
        query = GeneQuery(gene_symbol="tp53", species="Homo sapiens")
        assert query.gene_symbol == "TP53"
        assert query.species == "homo_sapiens"
        
        # Empty gene symbol
        with pytest.raises(ValueError):
            GeneQuery(gene_symbol="", species="homo_sapiens")
        
        # Empty species
        with pytest.raises(ValueError):
            GeneQuery(gene_symbol="TP53", species="")
    
    def test_gene_location_validation(self):
        """Test GeneLocation validation."""
        # Valid location
        location = GeneLocation(
            chromosome="17",
            start=7661779,
            end=7687538,
            strand="+",
            assembly="GRCh38"
        )
        assert location.chromosome == "17"
        assert location.start == 7661779
        assert location.end == 7687538
        assert location.strand == "+"
        assert location.assembly == "GRCh38"
        
        # Invalid strand
        with pytest.raises(ValueError):
            GeneLocation(
                chromosome="17",
                start=7661779,
                end=7687538,
                strand="*",
                assembly="GRCh38"
            )
        
        # Start > end
        with pytest.raises(ValueError):
            GeneLocation(
                chromosome="17",
                start=7687538,
                end=7661779,
                strand="+",
                assembly="GRCh38"
            )
    
    def test_gene_info(self):
        """Test GeneInfo model."""
        location = GeneLocation(
            chromosome="17",
            start=7661779,
            end=7687538,
            strand="+",
            assembly="GRCh38"
        )
        
        gene_info = GeneInfo(
            gene_id="ENSG00000141510",
            gene_symbol="TP53",
            gene_name="tumor protein p53",
            species="homo_sapiens",
            location=location,
            gene_type="protein_coding",
            description="tumor protein p53",
            synonyms=["P53", "TP53"],
            confidence=ConfidenceLevel.HIGH,
            sources=[DataSource.ENSEMBL]
        )
        
        assert gene_info.gene_id == "ENSG00000141510"
        assert gene_info.gene_symbol == "TP53"
        assert gene_info.gene_name == "tumor protein p53"
        assert gene_info.confidence == ConfidenceLevel.HIGH
        assert DataSource.ENSEMBL in gene_info.sources
    
    def test_gene_response(self):
        """Test GeneResponse model."""
        query = GeneQuery(gene_symbol="TP53", species="homo_sapiens")
        response = GeneResponse(
            query=query,
            execution_time=0.5,
            warnings=["Test warning"]
        )
        
        assert response.query == query
        assert response.execution_time == 0.5
        assert response.warnings == ["Test warning"]
        assert response.gene_info is None


class TestVariantTypes:
    """Test variant-related type definitions."""
    
    def test_variant_query_validation(self):
        """Test VariantQuery validation."""
        # Valid query
        query = VariantQuery(variant_id="rs123456", assembly="GRCh38")
        assert query.variant_id == "rs123456"
        assert query.assembly == "GRCh38"
        
        # Valid assembly alternatives
        valid_assemblies = ["GRCh37", "GRCh38", "hg19", "hg38"]
        for assembly in valid_assemblies:
            query = VariantQuery(variant_id="rs123456", assembly=assembly)
            assert query.assembly == assembly
        
        # Invalid assembly
        with pytest.raises(ValueError):
            VariantQuery(variant_id="rs123456", assembly="invalid")
        
        # Empty variant ID
        with pytest.raises(ValueError):
            VariantQuery(variant_id="", assembly="GRCh38")
    
    def test_genomic_position_validation(self):
        """Test GenomicPosition validation."""
        # Valid position
        position = GenomicPosition(
            chromosome="17",
            position=7675088,
            ref_allele="C",
            alt_allele="T",
            assembly="GRCh38"
        )
        assert position.chromosome == "17"
        assert position.position == 7675088
        assert position.ref_allele == "C"
        assert position.alt_allele == "T"
        
        # Test allele normalization
        position = GenomicPosition(
            chromosome="17",
            position=7675088,
            ref_allele="c",
            alt_allele="t",
            assembly="GRCh38"
        )
        assert position.ref_allele == "C"
        assert position.alt_allele == "T"
        
        # Empty allele
        with pytest.raises(ValueError):
            GenomicPosition(
                chromosome="17",
                position=7675088,
                ref_allele="",
                alt_allele="T",
                assembly="GRCh38"
            )
    
    def test_variant_info(self):
        """Test VariantInfo model."""
        position = GenomicPosition(
            chromosome="17",
            position=7675088,
            ref_allele="C",
            alt_allele="T",
            assembly="GRCh38"
        )
        
        variant_info = VariantInfo(
            variant_id="rs121913254",
            rsid="rs121913254",
            position=position,
            variant_type="SNV",
            genes=["TP53"],
            consequences=["missense_variant"],
            confidence=ConfidenceLevel.HIGH,
            sources=[DataSource.DBSNP]
        )
        
        assert variant_info.variant_id == "rs121913254"
        assert variant_info.rsid == "rs121913254"
        assert variant_info.variant_type == "SNV"
        assert "TP53" in variant_info.genes
        assert variant_info.confidence == ConfidenceLevel.HIGH
    
    def test_variant_response(self):
        """Test VariantResponse model."""
        query = VariantQuery(variant_id="rs123456", assembly="GRCh38")
        response = VariantResponse(
            query=query,
            execution_time=0.3,
            warnings=["Test warning"]
        )
        
        assert response.query == query
        assert response.execution_time == 0.3
        assert response.warnings == ["Test warning"]
        assert response.variant_info is None


if __name__ == "__main__":
    pytest.main([__file__])