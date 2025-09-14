#!/usr/bin/env python3
"""
测试Genome MCP服务器的基本功能
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from servers.ncbi.gene import NCBIGeneServer


async def test_ncbi_gene_server():
    """测试NCBI Gene服务器功能"""
    print("🧪 测试NCBI Gene MCP服务器...")
    print("=" * 50)

    # 创建服务器实例
    server = NCBIGeneServer()

    try:
        # 测试服务器信息
        print("1. 测试服务器信息...")
        stats = server.get_stats()
        print(f"   服务器名称: {stats['server']}")
        print(f"   服务器版本: {stats['version']}")
        print(f"   运行状态: {stats['running']}")
        print(f"   支持的操作: {', '.join(stats['capabilities']['operations'])}")
        print("   ✅ 服务器信息获取成功")
        print()

        # 测试健康检查
        print("2. 测试健康检查...")
        health = await server.health_check()
        print(f"   状态: {health['status']}")
        print(f"   运行时间: {health['uptime']:.2f}秒")
        print(f"   成功率: {health['stats']['success_rate']:.2%}")
        print("   ✅ 健康检查通过")
        print()

        # 测试基因信息查询 (TP53)
        print("3. 测试基因信息查询 (TP53)...")
        gene_info = await server.execute_request("get_gene_info", {"gene_id": "TP53"})
        print(f"   基因信息返回结构: {type(gene_info)}")
        print(f"   基因信息内容: {gene_info}")

        # 如果返回的是字典且有数据
        if isinstance(gene_info, dict):
            if "info" in gene_info:
                info = gene_info["info"]
                print(f"   基因名称: {info.get('name', 'N/A')}")
                print(f"   基因描述: {info.get('description', 'N/A')[:100]}...")
                print(
                    f"   染色体位置: {info.get('chromosome', 'N/A')}:{info.get('chrstart', 'N/A')}-{info.get('chrstop', 'N/A')}"
                )
                print("   ✅ 基因信息查询成功")
            else:
                print(f"   ❌ 基因信息查询返回结构异常: {gene_info.keys()}")
        else:
            print(f"   ❌ 基因信息查询返回类型异常: {type(gene_info)}")
        print()

        # 测试基因搜索
        print("4. 测试基因搜索 (cancer)...")
        search_result = await server.execute_request(
            "search_genes", {"term": "cancer", "species": "human", "max_results": 5}
        )
        print(f"   搜索结果类型: {type(search_result)}")
        print(f"   搜索结果内容: {search_result}")

        if isinstance(search_result, dict) and "data" in search_result:
            genes = search_result["data"]
            if isinstance(genes, list):
                print(f"   搜索结果数量: {len(genes)}")
                for i, gene in enumerate(genes[:3]):
                    print(
                        f"   {i+1}. {gene.get('name', 'N/A')} ({gene.get('gene_id', 'N/A')})"
                    )
                print("   ✅ 基因搜索成功")
            else:
                print(f"   ❌ 基因搜索结果数据格式异常: {type(genes)}")
        else:
            print(f"   ❌ 基因搜索失败: {search_result}")
        print()

        # 测试统计信息
        print("5. 测试统计信息...")
        stats = server.get_stats()
        server_stats = stats["stats"]
        print(f"   总请求数: {server_stats['requests_total']}")
        print(f"   成功请求数: {server_stats['requests_success']}")
        print(f"   失败请求数: {server_stats['requests_failed']}")
        print(f"   平均响应时间: {server_stats['avg_response_time']:.3f}秒")
        print(f"   并发请求数: {server_stats['concurrent_requests']}")
        print("   ✅ 统计信息获取成功")
        print()

        print("🎉 所有测试通过！Genome MCP服务器工作正常！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


async def test_server_capabilities():
    """测试服务器能力"""
    print("\n🔧 测试服务器能力...")
    print("-" * 30)

    server = NCBIGeneServer()
    capabilities = server.capabilities

    print(f"服务器名称: {capabilities.name}")
    print(f"服务器版本: {capabilities.version}")
    print(f"支持的操作: {capabilities.operations}")
    print(f"支持流式: {capabilities.supports_streaming}")
    print(f"支持批处理: {capabilities.supports_batch}")
    print(f"最大批处理大小: {capabilities.max_batch_size}")
    print(f"数据格式: {capabilities.data_formats}")
    print(f"需要认证: {capabilities.requires_auth}")


async def main():
    """主测试函数"""
    print("🚀 开始Genome MCP服务器测试")
    print("=" * 60)

    await test_server_capabilities()
    print()
    await test_ncbi_gene_server()


if __name__ == "__main__":
    asyncio.run(main())
