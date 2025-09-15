#!/usr/bin/env python3
"""
Genome MCP - Model Context Protocol Server for Genomic Data

A FastMCP-based server that provides unified access to genomic databases
through the Model Context Protocol interface.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional, List

from fastmcp import FastMCP
from genome_mcp.configuration import get_config
from genome_mcp.servers.ncbi.gene import NCBIGeneServer
from genome_mcp.exceptions import GenomeMCPError


# Create FastMCP server instance
mcp = FastMCP(
    name="Genome MCP Server",
    version="0.1.4",
    instructions="Genomic data MCP server for NCBI Gene database access"
)

# Global server instance
_gene_server: Optional[NCBIGeneServer] = None


async def initialize_server():
    """Initialize the NCBI Gene server."""
    global _gene_server
    if _gene_server is None:
        try:
            config = get_config()
            _gene_server = NCBIGeneServer(config)
            await _gene_server.start()
            logging.info("NCBI Gene server initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize NCBI Gene server: {e}")
            raise


@mcp.tool()
async def get_gene_info(
    gene_id: str,
    species: str = "human",
    include_summary: bool = True
) -> Dict[str, Any]:
    """
    Get detailed information about a specific gene.
    
    Args:
        gene_id: Gene ID (e.g., TP53)
        species: Species name (default: human)
        include_summary: Include gene summary text (default: True)
        
    Returns:
        Dictionary containing gene information
    """
    await initialize_server()
    params = {
        "gene_id": gene_id,
        "species": species,
        "include_summary": include_summary
    }
    return await _gene_server.execute_request("get_gene_info", params)


@mcp.tool()
async def search_genes(
    term: str,
    species: str = "human",
    max_results: int = 20
) -> Dict[str, Any]:
    """
    Search for genes by term.
    
    Args:
        term: Search term
        species: Species name (default: human)
        max_results: Maximum number of results (default: 20)
        
    Returns:
        Dictionary containing search results
    """
    await initialize_server()
    params = {
        "term": term,
        "species": species,
        "max_results": max_results
    }
    return await _gene_server.execute_request("search_genes", params)


@mcp.tool()
async def batch_gene_info(
    gene_ids: List[str],
    species: str = "human"
) -> Dict[str, Any]:
    """
    Get information for multiple genes in batch.
    
    Args:
        gene_ids: List of gene IDs
        species: Species name (default: human)
        
    Returns:
        Dictionary containing batch results
    """
    await initialize_server()
    params = {
        "gene_ids": gene_ids,
        "species": species
    }
    return await _gene_server.execute_request("batch_gene_info", params)


@mcp.tool()
async def search_by_region(
    chromosome: str,
    start: int,
    end: int,
    species: str = "human"
) -> Dict[str, Any]:
    """
    Search for genes in a genomic region.
    
    Args:
        chromosome: Chromosome (e.g., "1", "X", "Y")
        start: Start position
        end: End position
        species: Species name (default: human)
        
    Returns:
        Dictionary containing genes in the region
    """
    await initialize_server()
    params = {
        "chromosome": chromosome,
        "start": start,
        "end": end,
        "species": species
    }
    return await _gene_server.execute_request("search_by_region", params)


@mcp.tool()
async def get_gene_homologs(
    gene_id: str,
    species: str = "human",
    target_species: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get gene homologs across species.
    
    Args:
        gene_id: Gene ID
        species: Source species (default: human)
        target_species: Target species (optional)
        
    Returns:
        Dictionary containing gene homologs
    """
    await initialize_server()
    params = {
        "gene_id": gene_id,
        "species": species,
        "target_species": target_species
    }
    return await _gene_server.execute_request("get_gene_homologs", params)


def main():
    """Main entry point for the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Genome MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport mode (default: stdio)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for HTTP transports (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for HTTP transports (default: 8080)"
    )
    
    args = parser.parse_args()
    
    # Run the server with the specified transport
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()