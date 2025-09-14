#!/usr/bin/env python3
"""
Genome MCP Server 使用示例

本文件展示了如何使用 Genome MCP 服务器进行基因数据查询和操作。
"""

import asyncio
import json
from pathlib import Path
import sys

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from servers.ncbi.gene import NCBIGeneServer


async def example_basic_gene_query():
    """基础基因查询示例"""
    print("🔬 基础基因查询示例")
    print("-" * 40)

    server = NCBIGeneServer()

    # 查询TP53基因信息
    tp53_info = await server.execute_request(
        "get_gene_info", {"gene_id": "TP53", "species": "human"}
    )

    print(f"基因名称: {tp53_info['info']['name']}")
    print(f"基因描述: {tp53_info['info']['description']}")
    print(f"染色体位置: {tp53_info['info']['chromosome']}:")
    print(f"  - 起始位置: {tp53_info['info']['chrstart']:,}")
    # 从genomicinfo获取结束位置
    if tp53_info['info']['genomicinfo']:
        genomic_info = tp53_info['info']['genomicinfo'][0]
        print(f"  - 结束位置: {genomic_info['chrstop']:,}")
    print(f"基因ID: {tp53_info['info']['uid']}")

    return tp53_info


async def example_gene_search():
    """基因搜索示例"""
    print("\n🔍 基因搜索示例")
    print("-" * 40)

    server = NCBIGeneServer()

    # 搜索与癌症相关的基因
    search_results = await server.execute_request(
        "search_genes", {"term": "cancer", "species": "human", "max_results": 5}
    )

    print(f"搜索关键词: {search_results['term']}")
    print(f"物种: {search_results['species']}")
    print(f"找到的基因数量: {len(search_results['results'])}")
    print()

    for i, gene in enumerate(search_results["results"], 1):
        print(f"{i}. {gene['gene_id']} - {gene['description']}")
        print(f"   基因ID: {gene['uid']}")
        print(f"   染色体位置: {gene['summary']['chromosome']}")
        print()

    return search_results


async def example_batch_gene_query():
    """批量基因查询示例"""
    print("\n📊 批量基因查询示例")
    print("-" * 40)

    server = NCBIGeneServer()

    # 批量查询多个基因
    batch_results = await server.execute_request(
        "batch_gene_info",
        {"gene_ids": ["TP53", "EGFR", "APOE", "TNF", "BRCA1"], "species": "human"},
    )

    print(f"总共查询基因数: {batch_results['total_genes']}")
    print(f"成功查询数: {batch_results['successful']}")
    print(f"失败查询数: {batch_results['failed']}")
    print()

    for result in batch_results["results"]:
        gene_id = result["gene_id"]
        if result["success"]:
            info = result["data"]["info"]
            print(f"✅ {gene_id}: {info['name']} - {info['description']}")
        else:
            print(f"❌ {gene_id}: {result['error']}")

    return batch_results


async def example_regional_search():
    """基因组区域搜索示例"""
    print("\n🧬 基因组区域搜索示例")
    print("-" * 40)

    server = NCBIGeneServer()

    # 搜索17号染色体上的基因 (TP53基因所在区域)
    regional_results = await server.execute_request(
        "search_by_region",
        {
            "chromosome": "17",
            "start": 7660000,
            "end": 7690000,
            "species": "human",
            "max_results": 3,
        },
    )

    print(f"搜索区域: 染色体17:7,660,000-7,690,000")
    print(f"找到的基因数量: {len(regional_results['results'])}")
    print()

    if regional_results['results']:
        for i, gene in enumerate(regional_results["results"], 1):
            print(f"{i}. {gene['gene_id']} ({gene['uid']})")
            print(f"   描述: {gene['description']}")
            print(
                f"   位置: {gene['summary']['chromosome']}:{gene['summary']['chrstart']:,}"
            )
            if gene['summary'].get('genomicinfo'):
                genomic_info = gene['summary']['genomicinfo'][0]
                print(f"   结束位置: {genomic_info['chrstop']:,}")
            print()
    else:
        print("   注意: 区域搜索功能可能需要特定的NCBI API格式支持")
        print("   建议使用基因名称搜索或批量查询替代")
        print()

    return regional_results


async def example_gene_summary():
    """基因摘要查询示例"""
    print("\n📄 基因摘要查询示例")
    print("-" * 40)

    server = NCBIGeneServer()

    # 获取TP53基因的详细摘要
    summary_result = await server.execute_request(
        "get_gene_summary", {"gene_id": "TP53", "species": "human"}
    )

    print(f"基因ID: {summary_result['gene_id']}")
    print(f"物种: {summary_result['species']}")
    print(f"NCBI UID: {summary_result['uid']}")
    print("\n基因摘要:")
    print("=" * 60)
    print(
        summary_result["summary"][:500] + "..."
        if len(summary_result["summary"]) > 500
        else summary_result["summary"]
    )

    return summary_result


async def example_server_stats():
    """服务器统计信息示例"""
    print("\n📈 服务器统计信息")
    print("-" * 40)

    server = NCBIGeneServer()

    # 获取服务器统计信息
    stats = server.get_stats()

    print(f"服务器名称: {stats['server']}")
    print(f"服务器版本: {stats['version']}")
    print(f"运行状态: {stats['running']}")
    print()
    print("请求统计:")
    server_stats = stats["stats"]
    print(f"  总请求数: {server_stats['requests_total']}")
    print(f"  成功请求数: {server_stats['requests_success']}")
    print(f"  失败请求数: {server_stats['requests_failed']}")
    print(f"  平均响应时间: {server_stats['avg_response_time']:.3f}秒")
    print(f"  缓存命中: {server_stats['cache_hits']}")
    print(f"  缓存未命中: {server_stats['cache_misses']}")

    return stats


async def main():
    """主函数 - 运行所有示例"""
    print("🚀 Genome MCP Server 使用示例")
    print("=" * 60)

    try:
        # 运行各种示例
        await example_basic_gene_query()
        await example_gene_search()
        await example_batch_gene_query()
        await example_regional_search()
        await example_gene_summary()
        await example_server_stats()

        print("\n🎉 所有示例执行完成！")

    except Exception as e:
        print(f"❌ 执行过程中出现错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
