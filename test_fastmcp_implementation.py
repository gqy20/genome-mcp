#!/usr/bin/env python3
"""
Test script for Genome MCP FastMCP implementation
"""

import asyncio
import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_gene_info():
    """Test get_gene_info function"""
    try:
        from genome_mcp.main import get_gene_info
        
        print("Testing get_gene_info...")
        # Call the tool function correctly
        # First try searching for TP53 to get the correct gene ID
        from genome_mcp.main import search_genes
        search_result = await search_genes.fn(term="TP53", max_results=1)
        if search_result['results']:
            gene_id = search_result['results'][0]['gene_id']
            result = await get_gene_info.fn(gene_id=gene_id)
            print(f"Gene name: {result['info']['name']}")
            print(f"Gene description: {result['info']['description'][:100]}...")
            print("✅ get_gene_info test passed")
            return True
        else:
            print("❌ Could not find TP53 gene for testing")
            return False
    except Exception as e:
        print(f"❌ get_gene_info test failed: {e}")
        return False

async def test_search_genes():
    """Test search_genes function"""
    try:
        from genome_mcp.main import search_genes
        
        print("\nTesting search_genes...")
        result = await search_genes.fn(term="cancer", max_results=5)
        print(f"Found {len(result['results'])} genes")
        for gene in result['results'][:3]:  # Show first 3
            print(f"  - {gene['gene_id']}: {gene['description'][:50]}...")
        print("✅ search_genes test passed")
        return True
    except Exception as e:
        print(f"❌ search_genes test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Testing Genome MCP FastMCP Implementation")
    print("=" * 50)
    
    tests = [
        test_gene_info,
        test_search_genes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)