#!/usr/bin/env python3
"""
Example usage of Genome MCP FastMCP Implementation (Modern Version)

This example demonstrates how to use the modern MCP tools instead of
the deprecated compatibility functions.
"""

import asyncio
import os
import sys

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


async def example_usage():
    """Example usage of modern Genome MCP tools"""
    print("Genome MCP FastMCP Implementation Example (Modern)")
    print("=" * 50)

    try:
        # Import modern core components
        from genome_mcp.core import QueryExecutor, QueryParser

        # Initialize components
        parser = QueryParser()
        executor = QueryExecutor()

        # Example 1: Search for genes (using get_data tool)
        print("1. Searching for genes related to 'cancer'...")
        search_query = parser.parse("cancer", query_type="search")
        search_result = await executor.execute(search_query)
        print(f"   Found {search_result.get('total_count', 0)} genes:")
        if "results" in search_result:
            for gene in search_result["results"][:3]:
                gene_id = gene.get("gene_id", "Unknown")
                description = gene.get("description", "No description")
                print(f"   - {gene_id}: {description[:60]}...")

        # Example 2: Get detailed information about TP53
        print("\n2. Getting detailed information about TP53...")
        gene_query = parser.parse("TP53", query_type="info")
        tp53_result = await executor.execute(gene_query)
        if "gene_symbol" in tp53_result:
            print(f"   Gene: {tp53_result['gene_symbol']}")
        if "chromosome" in tp53_result:
            print(f"   Chromosome: {tp53_result['chromosome']}")
        if "description" in tp53_result:
            print(f"   Description: {tp53_result['description'][:100]}...")

        # Example 3: Batch query multiple genes
        print("\n3. Batch querying multiple genes...")
        gene_list = ["TP53", "EGFR", "BRCA1"]
        batch_query = parser.parse(gene_list, query_type="batch")
        batch_result = await executor.execute(batch_query)
        print(f"   Queried {batch_result.get('batch_size', len(gene_list))} genes")
        print(f"   Results: {len(batch_result.get('results', []))} successful")

        # Example 4: Region search (bonus example)
        print("\n4. Searching genes in a genomic region...")
        region_query = parser.parse("chr17:7565097-7590856", query_type="region")
        region_result = await executor.execute(region_query)
        if "genes_found" in region_result:
            print(f"   Found {len(region_result['genes_found'])} genes in the region")

        print("\n✅ All examples completed successfully!")
        print(
            "\n💡 Note: This example uses the modern QueryParser + QueryExecutor pattern"
        )
        print("   instead of the deprecated compatibility functions.")

    except Exception as e:
        print(f"❌ Error in example usage: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(example_usage())
    sys.exit(0 if success else 1)
