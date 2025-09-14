#!/usr/bin/env python3
"""
Example usage of Genome MCP FastMCP implementation
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def example_usage():
    """Example usage of Genome MCP tools"""
    print("Genome MCP FastMCP Implementation Example")
    print("=" * 50)
    
    try:
        # Import tools
        import main
        get_gene_info = main.get_gene_info
        search_genes = main.search_genes
        batch_gene_info = main.batch_gene_info
        
        # Example 1: Search for genes
        print("1. Searching for genes related to 'cancer'...")
        search_result = await search_genes.fn(term="cancer", max_results=3)
        print(f"   Found {len(search_result['results'])} genes:")
        for gene in search_result['results']:
            print(f"   - {gene['gene_id']}: {gene['description'][:60]}...")
        
        # Example 2: Get detailed information about TP53
        print("\n2. Getting detailed information about TP53...")
        tp53_info = await get_gene_info.fn(gene_id="TP53")
        print(f"   Gene: {tp53_info['info']['name']}")
        print(f"   Chromosome: {tp53_info['info']['chromosome']}")
        print(f"   Description: {tp53_info['info']['description'][:100]}...")
        
        # Example 3: Batch query multiple genes
        print("\n3. Batch querying multiple genes...")
        gene_list = ["TP53", "EGFR", "BRCA1"]
        batch_result = await batch_gene_info.fn(gene_ids=gene_list)
        print(f"   Queried {batch_result['total_genes']} genes")
        print(f"   Successful: {batch_result['successful']}")
        print(f"   Failed: {batch_result['failed']}")
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in example usage: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(example_usage())
    sys.exit(0 if success else 1)