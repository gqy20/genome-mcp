#!/usr/bin/env python3
"""
测试新功能的简单脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from genome_mcp.data.parsers import GenomicDataParser
from genome_mcp.servers.ncbi.gene import NCBIGeneServer
from genome_mcp.configuration import GenomeMCPConfig


async def test_genomic_position_parser():
    """测试基因组位置解析器"""
    print("🧬 测试基因组位置解析器")
    print("=" * 40)
    
    test_cases = [
        "chr1:1000-2000",
        "chr1[1000-2000]", 
        "1:1000-2000",
        "1[1000-2000]",
        "chrX:50000-60000",
        "chrY[1000-2000]",
    ]
    
    for test_case in test_cases:
        try:
            result = GenomicDataParser.parse_genomic_position(test_case)
            print(f"✅ {test_case} -> {result}")
        except Exception as e:
            print(f"❌ {test_case} -> ERROR: {e}")
    
    print()


async def test_enhanced_region_search():
    """测试增强的区域搜索"""
    print("🔍 测试增强的区域搜索")
    print("=" * 40)
    
    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)
    
    test_regions = [
        "chr17:43044295-43125483",  # TP53 region
        "chr17[43044295-43125483]",  # TP53 region (bracket format)
    ]
    
    async with server:
        for region in test_regions:
            try:
                print(f"搜索区域: {region}")
                result = await server.execute_request("search_by_region_enhanced", {
                    "region": region,
                    "species": "human",
                    "max_results": 5
                })
                
                print(f"  总结果数: {result.get('total_count', 0)}")
                print(f"  显示结果数: {len(result.get('results', []))}")
                
                for i, gene in enumerate(result.get('results', [])[:3], 1):
                    summary = gene.get('summary', {})
                    print(f"    {i}. {summary.get('name', 'N/A')} ({summary.get('uid', 'N/A')})")
                
                print()
                
            except Exception as e:
                print(f"❌ 搜索失败 {region}: {e}")
                print()


async def test_batch_homologs():
    """测试批量同源基因查询"""
    print("🧬 测试批量同源基因查询")
    print("=" * 40)
    
    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)
    
    test_genes = ["TP53", "BRCA1", "EGFR"]
    
    async with server:
        try:
            print(f"批量查询基因: {test_genes}")
            result = await server.execute_request("batch_gene_homologs", {
                "gene_ids": test_genes,
                "source_species": "human",
                "max_batch_size": 10
            })
            
            print(f"源物种: {result['source_species']}")
            print(f"总基因数: {result['total_genes']}")
            print(f"成功: {result['successful']}")
            print(f"失败: {result['failed']}")
            print()
            
            for gene_id, gene_result in result['results'].items():
                if gene_result['success']:
                    homologs = gene_result['homologs']
                    print(f"✅ {gene_id}: 找到 {len(homologs)} 个同源基因")
                    for homolog in homologs[:3]:  # 显示前3个
                        print(f"    • {homolog['species']}: {homolog['gene_id']}")
                else:
                    print(f"❌ {gene_id}: {gene_result['error']}")
            
        except Exception as e:
            print(f"❌ 批量查询失败: {e}")


async def main():
    """主测试函数"""
    print("🚀 Genome MCP 新功能测试")
    print("=" * 60)
    
    await test_genomic_position_parser()
    await test_enhanced_region_search()
    await test_batch_homologs()
    
    print("🎉 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())