"""
NCBI Gene Server implementation.

This module provides MCP server functionality for NCBI Gene database operations.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from urllib.parse import urljoin, urlencode
import structlog

from genome_mcp.servers.base import BaseMCPServer, ServerCapabilities
from genome_mcp.configuration import GenomeMCPConfig
from genome_mcp.http_utils import HTTPClient
from genome_mcp.data.parsers import GenomicDataParser, JSONDataParser
from genome_mcp.data.validators import GenomicValidator
from genome_mcp.exceptions import (
    APIError,
    ValidationError,
    DataNotFoundError,
    create_error_from_exception,
)

logger = structlog.get_logger(__name__)


class NCBIGeneServer(BaseMCPServer):
    """MCP Server for NCBI Gene database operations."""

    def _define_capabilities(self) -> ServerCapabilities:
        return ServerCapabilities(
            name="NCBIGeneServer",
            version="0.1.0",
            description="NCBI Gene database MCP server",
            operations=[
                "get_gene_info",
                "search_genes",
                "get_gene_summary",
                "get_gene_homologs",
                "get_gene_expression",
                "get_gene_pathways",
                "batch_gene_info",
                "search_by_region",
                "search_by_region_enhanced",  # Enhanced region search with format support
                "batch_gene_homologs",  # Batch homologs search
            ],
            supports_batch=True,
            supports_streaming=False,
            max_batch_size=self.config.data_sources.ncbi.max_batch_size,
            rate_limit_requests=10,  # NCBI has strict rate limits
            rate_limit_window=60,
            data_formats=["json", "xml"],
        )

    def _get_base_url(self) -> str:
        return self.config.data_sources.ncbi.base_url

    async def _execute_operation(
        self, operation: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute NCBI Gene operation."""

        if operation == "get_gene_info":
            return await self._get_gene_info(params)
        elif operation == "search_genes":
            return await self._search_genes(params)
        elif operation == "get_gene_summary":
            return await self._get_gene_summary(params)
        elif operation == "get_gene_homologs":
            return await self._get_gene_homologs(params)
        elif operation == "get_gene_expression":
            return await self._get_gene_expression(params)
        elif operation == "get_gene_pathways":
            return await self._get_gene_pathways(params)
        elif operation == "batch_gene_info":
            return await self._batch_gene_info(params)
        elif operation == "search_by_region":
            return await self._search_by_region(params)
        elif operation == "search_by_region_enhanced":
            return await self._search_by_region_enhanced(params)
        elif operation == "batch_gene_homologs":
            return await self._batch_gene_homologs(params)
        else:
            raise ValidationError(f"Unknown operation: {operation}")

    async def _get_gene_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific gene.

        Args:
            params: Parameters containing gene identifier
                - gene_id: Gene ID (required)
                - species: Species name (optional, default: human)
                - include_summary: Include gene summary (optional, default: true)
        """
        gene_id = params.get("gene_id")
        if not gene_id:
            raise ValidationError("gene_id is required", field_name="gene_id")

        species = params.get("species", "human")
        include_summary = params.get("include_summary", True)

        # Build NCBI EUtils URL
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

        # First, get the gene UID
        search_params = {
            "db": "gene",
            "term": f"{gene_id}[Gene] AND {species}[Organism]",
            "retmode": "json",
            "retmax": 1,
        }

        try:
            # Search for gene
            search_url = f"{base_url}esearch.fcgi?{urlencode(search_params)}"
            search_response = await self.http_client.get(search_url)

            if not search_response.get("esearchresult", {}).get("idlist"):
                raise DataNotFoundError(f"Gene not found: {gene_id} in {species}")

            gene_uid = search_response["esearchresult"]["idlist"][0]

            # Get gene summary
            summary_params = {"db": "gene", "id": gene_uid, "retmode": "json"}

            summary_url = f"{base_url}esummary.fcgi?{urlencode(summary_params)}"
            summary_response = await self.http_client.get(summary_url)

            result = {
                "gene_id": gene_id,
                "species": species,
                "uid": gene_uid,
                "info": summary_response.get("result", {}).get(str(gene_uid), {}),
                "source": "NCBI Gene",
            }

            if include_summary:
                result["summary"] = await self._get_gene_text_summary(gene_uid)

            return result

        except Exception as e:
            if isinstance(e, (ValidationError, DataNotFoundError)):
                raise
            raise APIError(f"Failed to get gene info for {gene_id}: {str(e)}")

    async def _search_genes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for genes by term.

        Args:
            params: Search parameters
                - term: Search term (required)
                - species: Species name (optional, default: human)
                - max_results: Maximum results (optional, default: 20)
                - offset: Result offset (optional, default: 0)
        """
        term = params.get("term")
        if not term:
            raise ValidationError("term is required", field_name="term")

        species = params.get("species", "human")
        max_results = min(params.get("max_results", 20), 100)
        offset = params.get("offset", 0)

        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

        search_params = {
            "db": "gene",
            "term": f"{term} AND {species}[Organism]",
            "retmode": "json",
            "retmax": max_results,
            "retstart": offset,
        }

        try:
            search_url = f"{base_url}esearch.fcgi?{urlencode(search_params)}"
            response = await self.http_client.get(search_url)

            search_result = response.get("esearchresult", {})

            # Get summary for found genes
            gene_uids = search_result.get("idlist", [])
            if gene_uids:
                summary_params = {
                    "db": "gene",
                    "id": ",".join(gene_uids),
                    "retmode": "json",
                }

                summary_url = f"{base_url}esummary.fcgi?{urlencode(summary_params)}"
                summary_response = await self.http_client.get(summary_url)

                gene_summaries = summary_response.get("result", {})

                # Build result list
                results = []
                for uid in gene_uids:
                    gene_data = gene_summaries.get(str(uid), {})
                    if gene_data:
                        results.append(
                            {
                                "uid": uid,
                                "gene_id": gene_data.get("name", ""),
                                "description": gene_data.get("description", ""),
                                "summary": gene_data,
                            }
                        )
            else:
                results = []

            return {
                "term": term,
                "species": species,
                "results": results,
                "total_count": int(search_result.get("count", 0)),
                "offset": offset,
                "max_results": max_results,
            }

        except Exception as e:
            raise APIError(f"Failed to search genes for term '{term}': {str(e)}")

    async def _get_gene_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get gene summary text.

        Args:
            params: Parameters
                - gene_id: Gene ID (required)
                - species: Species name (optional, default: human)
        """
        gene_id = params.get("gene_id")
        if not gene_id:
            raise ValidationError("gene_id is required", field_name="gene_id")

        species = params.get("species", "human")

        # Get gene UID first
        gene_uid = await self._get_gene_uid(gene_id, species)

        return {
            "gene_id": gene_id,
            "species": species,
            "uid": gene_uid,
            "summary": await self._get_gene_text_summary(gene_uid),
        }

    async def _get_gene_homologs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get gene homologs across species.

        Args:
            params: Parameters
                - gene_id: Gene ID (required)
                - species: Source species (optional, default: human)
                - target_species: Target species (optional)
        """
        gene_id = params.get("gene_id")
        if not gene_id:
            raise ValidationError("gene_id is required", field_name="gene_id")

        species = params.get("species", "human")
        target_species = params.get("target_species")

        # Get gene UID first
        gene_uid = await self._get_gene_uid(gene_id, species)

        # NCBI HomoloGene database
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

        search_params = {
            "db": "homologene",
            "term": f"{gene_uid}[Gene ID]",
            "retmode": "json",
        }

        try:
            search_url = f"{base_url}esearch.fcgi?{urlencode(search_params)}"
            response = await self.http_client.get(search_url)

            homologene_ids = response.get("esearchresult", {}).get("idlist", [])

            if homologene_ids:
                # Get homology data
                summary_params = {
                    "db": "homologene",
                    "id": homologene_ids[0],  # Use first homology group
                    "retmode": "json",
                }

                summary_url = f"{base_url}esummary.fcgi?{urlencode(summary_params)}"
                summary_response = await self.http_client.get(summary_url)

                homologs_data = summary_response.get("result", {})

                # Process homologs
                homologs = []
                for homolog_id, homolog_info in homologs_data.items():
                    if homolog_id != "uids":
                        homolog_species = homolog_info.get("taxname", "")
                        if (
                            not target_species
                            or target_species.lower() in homolog_species.lower()
                        ):
                            homologs.append(
                                {
                                    "species": homolog_species,
                                    "gene_id": homolog_info.get("name", ""),
                                    "symbol": homolog_info.get("symbol", ""),
                                    "protein_id": homolog_info.get("proteinid", ""),
                                    "identity": homolog_info.get("identity", ""),
                                }
                            )

                return {
                    "gene_id": gene_id,
                    "species": species,
                    "uid": gene_uid,
                    "homologs": homologs,
                }
            else:
                return {
                    "gene_id": gene_id,
                    "species": species,
                    "uid": gene_uid,
                    "homologs": [],
                }

        except Exception as e:
            raise APIError(f"Failed to get gene homologs for {gene_id}: {str(e)}")

    async def _batch_gene_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information for multiple genes in batch.

        Args:
            params: Parameters
                - gene_ids: List of gene IDs (required)
                - species: Species name (optional, default: human)
        """
        gene_ids = params.get("gene_ids", [])
        if not gene_ids or not isinstance(gene_ids, list):
            raise ValidationError(
                "gene_ids must be a non-empty list", field_name="gene_ids"
            )

        if len(gene_ids) > self.capabilities.max_batch_size:
            raise ValidationError(
                f"Batch size {len(gene_ids)} exceeds maximum {self.capabilities.max_batch_size}",
                field_name="gene_ids",
            )

        species = params.get("species", "human")

        # Execute requests in parallel
        tasks = []
        for gene_id in gene_ids:
            task = self._get_gene_info(
                {
                    "gene_id": gene_id,
                    "species": species,
                    "include_summary": False,  # Skip summary for batch to improve performance
                }
            )
            tasks.append(task)

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "gene_id": gene_ids[i],
                            "success": False,
                            "error": str(result),
                            "error_type": type(result).__name__,
                        }
                    )
                else:
                    processed_results.append(
                        {"gene_id": gene_ids[i], "success": True, "data": result}
                    )

            return {
                "species": species,
                "total_genes": len(gene_ids),
                "successful": len([r for r in processed_results if r["success"]]),
                "failed": len([r for r in processed_results if not r["success"]]),
                "results": processed_results,
            }

        except Exception as e:
            raise APIError(f"Failed to execute batch gene info: {str(e)}")

    async def _search_by_region(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for genes in a genomic region.

        Args:
            params: Parameters
                - chromosome: Chromosome (required)
                - start: Start position (required)
                - end: End position (required)
                - species: Species name (optional, default: human)
        """
        chromosome = params.get("chromosome")
        start = params.get("start")
        end = params.get("end")

        if not all([chromosome, start, end]):
            raise ValidationError("chromosome, start, and end are required")

        species = params.get("species", "human")

        # Validate genomic position
        try:
            position = GenomicDataParser.parse_genomic_position(
                f"{chromosome}:{start}-{end}"
            )
            chromosome = position["chromosome"]
            start = position["start"]
            end = position["end"]
        except Exception as e:
            raise ValidationError(f"Invalid genomic position: {str(e)}")

        # Build search term for genomic region
        search_term = (
            f"{chromosome}:{start}-{end}[chr] AND {species}[Organism]"
        )

        return await self._search_genes(
            {
                "term": search_term,
                "species": species,
                "max_results": params.get("max_results", 50),
            }
        )

    async def _get_gene_expression(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get gene expression data (placeholder for GEO integration).

        Args:
            params: Parameters
                - gene_id: Gene ID (required)
                - species: Species name (optional, default: human)
        """
        # Placeholder implementation
        # In a real implementation, this would query GEO or Expression Atlas
        gene_id = params.get("gene_id")
        species = params.get("species", "human")

        return {
            "gene_id": gene_id,
            "species": species,
            "expression": {
                "message": "Gene expression data integration coming soon",
                "available_sources": ["GEO", "Expression Atlas"],
                "status": "placeholder",
            },
        }

    async def _get_gene_pathways(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get gene pathway information (placeholder for KEGG/Reactome integration).

        Args:
            params: Parameters
                - gene_id: Gene ID (required)
                - species: Species name (optional, default: human)
        """
        # Placeholder implementation
        # In a real implementation, this would query KEGG or Reactome
        gene_id = params.get("gene_id")
        species = params.get("species", "human")

        return {
            "gene_id": gene_id,
            "species": species,
            "pathways": {
                "message": "Pathway data integration coming soon",
                "available_sources": ["KEGG", "Reactome", "BioCyc"],
                "status": "placeholder",
            },
        }

    async def _get_gene_uid(self, gene_id: str, species: str) -> str:
        """Get NCBI Gene UID for a gene identifier."""
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

        search_params = {
            "db": "gene",
            "term": f"{gene_id}[Gene] AND {species}[Organism]",
            "retmode": "json",
            "retmax": 1,
        }

        search_url = f"{base_url}esearch.fcgi?{urlencode(search_params)}"
        response = await self.http_client.get(search_url)

        gene_uids = response.get("esearchresult", {}).get("idlist", [])
        if not gene_uids:
            raise DataNotFoundError(f"Gene not found: {gene_id} in {species}")

        return gene_uids[0]

    async def _get_gene_text_summary(self, gene_uid: str) -> str:
        """Get gene summary text from Gene database."""
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

        # Use efetch to get gene summary in text format
        fetch_params = {
            "db": "gene",
            "id": gene_uid,
            "rettype": "docsum",
            "retmode": "text",
        }

        fetch_url = f"{base_url}efetch.fcgi?{urlencode(fetch_params)}"

        try:
            response = await self.http_client.session.get(fetch_url)
            return await response.text()
        except Exception:
            # Fallback to basic summary
            return f"Gene summary for UID: {gene_uid}"

    async def _search_by_region_enhanced(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced search for genes in a genomic region with format support.

        Args:
            params: Parameters
                - region: Genomic region string (required) - supports formats:
                  "chr1:1000-2000", "chr1[1000-2000]", "1:1000-2000", "1[1000-2000]"
                - species: Species name (optional, default: human)
                - max_results: Maximum results (optional, default: 50)
        """
        region = params.get("region")
        if not region:
            raise ValidationError("region is required", field_name="region")

        species = params.get("species", "human")
        max_results = params.get("max_results", 50)

        # Parse the region string
        try:
            parsed_region = GenomicDataParser.parse_genomic_position(region)
        except ValidationError as e:
            raise ValidationError(f"Invalid region format: {str(e)}", field_name="region")

        # Validate that we have a complete region
        if parsed_region["start"] is None or parsed_region["end"] is None:
            raise ValidationError("Region must include start and end positions", field_name="region")

        # Call the existing search_by_region method with parsed parameters
        return await self._search_by_region({
            "chromosome": parsed_region["chromosome"],
            "start": parsed_region["start"],
            "end": parsed_region["end"],
            "species": species,
            "max_results": max_results,
        })

    async def _batch_gene_homologs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get homologs for multiple genes in batch.

        Args:
            params: Parameters
                - gene_ids: List of gene IDs (required)
                - source_species: Source species (optional, default: human)
                - target_species: List of target species (optional)
                - max_batch_size: Maximum batch size (optional, default: 25)
        """
        gene_ids = params.get("gene_ids", [])
        if not gene_ids or not isinstance(gene_ids, list):
            raise ValidationError(
                "gene_ids must be a non-empty list", field_name="gene_ids"
            )

        if len(gene_ids) > 100:  # Safety limit
            raise ValidationError(
                f"Batch size {len(gene_ids)} exceeds maximum 100",
                field_name="gene_ids",
            )

        source_species = params.get("source_species", "human")
        target_species = params.get("target_species")
        max_batch_size = min(params.get("max_batch_size", 25), 50)

        # Process in batches to avoid overwhelming the API
        all_results = {}
        
        for i in range(0, len(gene_ids), max_batch_size):
            batch_gene_ids = gene_ids[i:i + max_batch_size]
            
            # Create tasks for concurrent execution
            tasks = []
            for gene_id in batch_gene_ids:
                task = self._get_gene_homologs({
                    "gene_id": gene_id,
                    "species": source_species,
                    "target_species": target_species,
                })
                tasks.append(task)
            
            try:
                # Execute batch concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for gene_id, result in zip(batch_gene_ids, batch_results):
                    if isinstance(result, Exception):
                        all_results[gene_id] = {
                            "success": False,
                            "error": str(result),
                            "error_type": type(result).__name__,
                            "gene_id": gene_id,
                            "species": source_species,
                            "homologs": [],
                        }
                    else:
                        all_results[gene_id] = {
                            "success": True,
                            "gene_id": gene_id,
                            "species": source_species,
                            "homologs": result.get("homologs", []),
                        }
                        
            except Exception as e:
                # If batch fails completely, record error for all genes in batch
                for gene_id in batch_gene_ids:
                    all_results[gene_id] = {
                        "success": False,
                        "error": f"Batch processing failed: {str(e)}",
                        "error_type": "BatchError",
                        "gene_id": gene_id,
                        "species": source_species,
                        "homologs": [],
                    }

        # Calculate statistics
        successful_count = len([r for r in all_results.values() if r["success"]])
        failed_count = len(all_results) - successful_count

        return {
            "source_species": source_species,
            "target_species": target_species,
            "total_genes": len(gene_ids),
            "successful": successful_count,
            "failed": failed_count,
            "results": all_results,
        }
