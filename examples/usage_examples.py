#!/usr/bin/env python3
"""
Genome MCP 使用示例

本文件展示了如何使用 Genome MCP 系统的各种功能。
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from genome_mcp.configuration import GenomeMCPConfig
from genome_mcp.exceptions import DataNotFoundError, ValidationError
from genome_mcp.servers.ncbi.gene import NCBIGeneServer


async def basic_gene_info_example():
    """基本基因信息查询示例"""
    print("🧬 基本基因信息查询示例")
    print("=" * 40)

    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    async with server:
        try:
            # 查询 TP53 基因信息
            result = await server.execute_request(
                "get_gene_info",
                {"gene_id": "TP53", "species": "human", "include_summary": True},
            )

            print(f"基因 ID: {result['gene_id']}")
            print(f"物种: {result['species']}")
            print(f"UID: {result['uid']}")
            print(f"名称: {result['info'].get('name', 'N/A')}")
            print(f"描述: {result['info'].get('description', 'N/A')}")
            print(f"染色体位置: {result['info'].get('chromosome', 'N/A')}")

            if "summary" in result:
                print(f"摘要: {result['summary'][:200]}...")

        except Exception as e:
            print(f"查询失败: {e}")


async def gene_search_example():
    """基因搜索示例"""
    print("\n🔍 基因搜索示例")
    print("=" * 40)

    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    async with server:
        try:
            # 搜索包含 "BRCA" 的基因
            result = await server.execute_request(
                "search_genes", {"term": "BRCA", "species": "human", "max_results": 5}
            )

            print(f"搜索词: {result['term']}")
            print(f"物种: {result['species']}")
            print(f"总结果数: {result['total_count']}")
            print(f"显示结果数: {len(result['results'])}")

            for i, gene in enumerate(result["results"], 1):
                print(
                    f"{i}. {gene.get('gene_id', 'N/A')} - {gene.get('description', 'N/A')}"
                )

        except Exception as e:
            print(f"搜索失败: {e}")


async def batch_operations_example():
    """批量操作示例"""
    print("\n📦 批量操作示例")
    print("=" * 40)

    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    async with server:
        try:
            # 批量查询多个基因
            result = await server.execute_request(
                "batch_gene_info",
                {
                    "gene_ids": ["TP53", "BRCA1", "EGFR", "MYC", "KRAS"],
                    "species": "human",
                },
            )

            print(f"物种: {result['species']}")
            print(f"总基因数: {result['total_genes']}")
            print(f"成功: {result['successful']}")
            print(f"失败: {result['failed']}")

            for gene_result in result["results"]:
                if gene_result["success"]:
                    data = gene_result["data"]
                    print(f"✅ {data['gene_id']}: {data['info'].get('name', 'N/A')}")
                else:
                    print(f"❌ {gene_result['gene_id']}: {gene_result['error']}")

        except Exception as e:
            print(f"批量操作失败: {e}")


async def genomic_region_search_example():
    """基因组区域搜索示例"""
    print("\n🧬 基因组区域搜索示例")
    print("=" * 40)

    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    async with server:
        try:
            # 搜索染色体 17 上的特定区域
            result = await server.execute_request(
                "search_by_region",
                {
                    "chromosome": "17",
                    "start": 43044295,
                    "end": 43125483,
                    "species": "human",
                    "max_results": 10,
                },
            )

            print(
                f"搜索区域: 染色体 {result['results'][0].get('summary', {}).get('chromosome', 'N/A')}"
            )
            print(f"总结果数: {result['total_count']}")

            for i, gene in enumerate(result["results"][:3], 1):
                summary = gene.get("summary", {})
                print(
                    f"{i}. {summary.get('name', 'N/A')} ({summary.get('uid', 'N/A')})"
                )

        except Exception as e:
            print(f"区域搜索失败: {e}")


async def gene_homologs_example():
    """基因同源体查询示例"""
    print("\n🧬 基因同源体查询示例")
    print("=" * 40)

    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    async with server:
        try:
            # 查询 TP53 的同源体
            result = await server.execute_request(
                "get_gene_homologs",
                {"gene_id": "TP53", "species": "human", "target_species": "mouse"},
            )

            print(f"源基因: {result['gene_id']} ({result['species']})")
            print(f"同源体数量: {len(result['homologs'])}")

            for homolog in result["homologs"][:5]:
                print(
                    f"  • {homolog['species']}: {homolog['gene_id']} "
                    f"(相似度: {homolog.get('identity', 'N/A')})"
                )

        except Exception as e:
            print(f"同源体查询失败: {e}")


async def concurrent_operations_example():
    """并发操作示例"""
    print("\n⚡ 并发操作示例")
    print("=" * 40)

    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    async with server:
        try:
            # 并发执行多个不同的操作
            tasks = [
                server.execute_request("get_gene_info", {"gene_id": "TP53"}),
                server.execute_request("get_gene_info", {"gene_id": "BRCA1"}),
                server.execute_request(
                    "search_genes", {"term": "cancer", "max_results": 5}
                ),
                server.execute_request("get_gene_summary", {"gene_id": "EGFR"}),
                server.execute_request("get_gene_homologs", {"gene_id": "MYC"}),
            ]

            print("并发执行 5 个请求...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"请求 {i+1} 失败: {result}")
                else:
                    operation = [
                        "TP53信息",
                        "BRCA1信息",
                        "癌症基因搜索",
                        "EGFR摘要",
                        "MYC同源体",
                    ][i]
                    if "gene_id" in result:
                        print(f"✅ 请求 {i+1} ({operation}): {result['gene_id']}")
                    elif "term" in result:
                        print(
                            f"✅ 请求 {i+1} ({operation}): {result['total_count']} 个结果"
                        )
                    else:
                        print(f"✅ 请求 {i+1} ({operation}): 成功")

            # 显示服务器统计信息
            stats = server.get_stats()
            print("\n📊 服务器统计:")
            print(f"   总请求数: {stats['stats']['requests_total']}")
            print(f"   成功请求: {stats['stats']['requests_success']}")
            print(f"   失败请求: {stats['stats']['requests_failed']}")
            print(f"   平均响应时间: {stats['stats']['avg_response_time']:.3f} 秒")
            print(f"   缓存命中: {stats['stats']['cache_hits']}")
            print(f"   缓存未命中: {stats['stats']['cache_misses']}")

        except Exception as e:
            print(f"并发操作失败: {e}")


async def error_handling_example():
    """错误处理示例"""
    print("\n⚠️ 错误处理示例")
    print("=" * 40)

    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    async with server:
        # 测试各种错误情况

        # 1. 参数验证错误
        try:
            await server.execute_request("get_gene_info", {})
        except ValidationError as e:
            print(f"✅ 参数验证错误捕获: {e}")

        # 2. 数据未找到错误
        try:
            await server.execute_request(
                "get_gene_info", {"gene_id": "NONEXISTENT_GENE"}
            )
        except DataNotFoundError as e:
            print(f"✅ 数据未找到错误捕获: {e}")
        except Exception as e:
            print(f"⚠️ 其他错误: {e}")

        # 3. 不支持的操作
        try:
            await server.execute_request("unsupported_operation", {})
        except ValidationError as e:
            print(f"✅ 不支持操作错误捕获: {e}")

        # 4. 批量大小超限
        try:
            too_many_genes = [f"GENE{i}" for i in range(200)]
            await server.execute_request(
                "batch_gene_info", {"gene_ids": too_many_genes}
            )
        except ValidationError as e:
            print(f"✅ 批量大小超限错误捕获: {e}")


async def performance_comparison_example():
    """性能对比示例"""
    print("\n⚡ 性能对比示例")
    print("=" * 40)

    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    gene_ids = [
        "TP53",
        "BRCA1",
        "EGFR",
        "MYC",
        "KRAS",
        "AKT1",
        "PIK3CA",
        "PTEN",
        "RB1",
        "CDKN2A",
    ]

    async with server:
        import time

        # 方法 1: 逐个请求
        print("方法 1: 逐个请求")
        start_time = time.time()

        individual_results = []
        for gene_id in gene_ids:
            try:
                result = await server.execute_request(
                    "get_gene_info", {"gene_id": gene_id}
                )
                individual_results.append(result)
            except Exception as e:
                print(f"  ❌ {gene_id}: {e}")

        individual_time = time.time() - start_time
        print(
            f"  完成 {len(individual_results)} 个请求，耗时: {individual_time:.2f} 秒"
        )

        # 重置统计
        server.reset_stats()

        # 方法 2: 批量请求
        print("\n方法 2: 批量请求")
        start_time = time.time()

        try:
            batch_result = await server.execute_request(
                "batch_gene_info", {"gene_ids": gene_ids}
            )
            batch_time = time.time() - start_time
            print(
                f"  完成 {batch_result['successful']} 个请求，耗时: {batch_time:.2f} 秒"
            )

            if individual_time > 0:
                speedup = individual_time / batch_time
                print(f"  批量操作比逐个请求快 {speedup:.1f} 倍")
        except Exception as e:
            print(f"  ❌ 批量请求失败: {e}")


async def main():
    """主函数：运行所有示例"""
    print("🚀 Genome MCP 使用示例")
    print("=" * 60)

    try:
        await basic_gene_info_example()
        await gene_search_example()
        await batch_operations_example()
        await genomic_region_search_example()
        await gene_homologs_example()
        await concurrent_operations_example()
        await error_handling_example()
        await performance_comparison_example()

        print("\n🎉 所有示例运行完成！")

    except KeyboardInterrupt:
        print("\n⏹️ 示例被用户中断")
    except Exception as e:
        print(f"\n💥 示例运行出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())
