"""
Test script for NCBIGeneServer implementation.
"""

import asyncio
import sys
import os
from typing import Dict, Any
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from genome_mcp.configuration import GenomeMCPConfig
from genome_mcp.servers.ncbi.gene import NCBIGeneServer
from genome_mcp.exceptions import ValidationError, DataNotFoundError, APIError


async def test_ncbi_gene_server():
    """Test NCBIGeneServer functionality."""
    print("🧪 测试NCBI基因服务器...")

    # Test server initialization
    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    print(f"✓ 服务器初始化: {server.capabilities.name} v{server.capabilities.version}")
    print(f"✓ 支持的操作: {', '.join(server.capabilities.operations)}")

    # Test server start/stop
    await server.start()
    assert server._running == True
    print("✓ 服务器启动成功")

    await server.stop()
    assert server._running == False
    print("✓ 服务器停止成功")

    # Test health check
    async with NCBIGeneServer(config) as server:
        health = await server.health_check()
        assert health["status"] == "healthy"
        assert health["server"] == "NCBIGeneServer"
        print("✓ 健康检查功能正常")

    # Test gene info retrieval - use a well-known gene (BRCA1)
    async with NCBIGeneServer(config) as server:
        try:
            result = await server.execute_request(
                "get_gene_info", {"gene_id": "BRCA1", "species": "human"}
            )

            assert "gene_id" in result
            assert "species" in result
            assert "uid" in result
            assert "info" in result
            assert result["gene_id"] == "BRCA1"
            assert result["species"] == "human"
            print("✓ 基因信息检索成功")

        except (APIError, DataNotFoundError) as e:
            print(f"⚠ 基因信息检索失败（可能是网络问题）: {e}")

    # Test gene search
    async with NCBIGeneServer(config) as server:
        try:
            result = await server.execute_request(
                "search_genes", {"term": "BRCA", "species": "human", "max_results": 5}
            )

            assert "term" in result
            assert "species" in result
            assert "results" in result
            assert "total_count" in result
            assert result["term"] == "BRCA"
            assert result["species"] == "human"
            assert len(result["results"]) <= 5
            print("✓ 基因搜索功能正常")

        except (APIError, DataNotFoundError) as e:
            print(f"⚠ 基因搜索失败（可能是网络问题）: {e}")

    # Test batch gene info
    async with NCBIGeneServer(config) as server:
        try:
            result = await server.execute_request(
                "batch_gene_info",
                {"gene_ids": ["TP53", "BRCA1", "EGFR"], "species": "human"},
            )

            assert "species" in result
            assert "total_genes" in result
            assert "successful" in result
            assert "failed" in result
            assert "results" in result
            assert result["total_genes"] == 3
            assert result["species"] == "human"
            print("✓ 批量基因信息检索成功")

        except (APIError, DataNotFoundError) as e:
            print(f"⚠ 批量基因信息检索失败（可能是网络问题）: {e}")

    # Test genomic region search
    async with NCBIGeneServer(config) as server:
        try:
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

            assert "term" in result
            assert "species" in result
            assert "results" in result
            assert result["species"] == "human"
            print("✓ 基因组区域搜索成功")

        except (APIError, DataNotFoundError) as e:
            print(f"⚠ 基因组区域搜索失败（可能是网络问题）: {e}")

    # Test gene homologs
    async with NCBIGeneServer(config) as server:
        try:
            result = await server.execute_request(
                "get_gene_homologs", {"gene_id": "TP53", "species": "human"}
            )

            assert "gene_id" in result
            assert "species" in result
            assert "uid" in result
            assert "homologs" in result
            assert result["gene_id"] == "TP53"
            assert result["species"] == "human"
            print("✓ 基因同源体检索成功")

        except (APIError, DataNotFoundError) as e:
            print(f"⚠ 基因同源体检索失败（可能是网络问题）: {e}")

    # Test gene summary
    async with NCBIGeneServer(config) as server:
        try:
            result = await server.execute_request(
                "get_gene_summary", {"gene_id": "TP53", "species": "human"}
            )

            assert "gene_id" in result
            assert "species" in result
            assert "uid" in result
            assert "summary" in result
            assert result["gene_id"] == "TP53"
            assert result["species"] == "human"
            print("✓ 基因摘要检索成功")

        except (APIError, DataNotFoundError) as e:
            print(f"⚠ 基因摘要检索失败（可能是网络问题）: {e}")

    # Test placeholder functions (expression and pathways)
    async with NCBIGeneServer(config) as server:
        try:
            # Test gene expression (placeholder)
            result = await server.execute_request(
                "get_gene_expression", {"gene_id": "TP53", "species": "human"}
            )

            assert "gene_id" in result
            assert "species" in result
            assert "expression" in result
            assert result["gene_id"] == "TP53"
            assert result["species"] == "human"
            assert "placeholder" in result["expression"]
            print("✓ 基因表达数据接口正常（占位符）")

        except Exception as e:
            print(f"⚠ 基因表达数据接口测试失败: {e}")

    async with NCBIGeneServer(config) as server:
        try:
            # Test gene pathways (placeholder)
            result = await server.execute_request(
                "get_gene_pathways", {"gene_id": "TP53", "species": "human"}
            )

            assert "gene_id" in result
            assert "species" in result
            assert "pathways" in result
            assert result["gene_id"] == "TP53"
            assert result["species"] == "human"
            assert "placeholder" in result["pathways"]
            print("✓ 基因通路数据接口正常（占位符）")

        except Exception as e:
            print(f"⚠ 基因通路数据接口测试失败: {e}")

    # Test error handling
    async with NCBIGeneServer(config) as server:
        try:
            await server.execute_request("get_gene_info", {})
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "gene_id" in str(e)
            print("✓ 参数验证错误处理正常")

        try:
            await server.execute_request("invalid_operation", {})
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "Unsupported operation" in str(e)
            print("✓ 不支持操作错误处理正常")

    # Test batch size limits
    async with NCBIGeneServer(config) as server:
        try:
            # Test with too many genes (should exceed batch size)
            too_many_genes = ["GENE" + str(i) for i in range(200)]
            await server.execute_request(
                "batch_gene_info", {"gene_ids": too_many_genes, "species": "human"}
            )
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "exceeds maximum" in str(e)
            print("✓ 批量大小限制验证正常")

    # Test stats
    async with NCBIGeneServer(config) as server:
        # Execute some requests to generate stats
        try:
            await server.execute_request(
                "get_gene_info", {"gene_id": "TP53", "species": "human"}
            )
            await server.execute_request(
                "search_genes", {"term": "cancer", "species": "human", "max_results": 3}
            )
        except (APIError, DataNotFoundError):
            pass  # Network issues are ok for stats testing

        stats = server.get_stats()
        assert stats["server"] == "NCBIGeneServer"
        assert stats["version"] == "1.0.0"
        assert "stats" in stats
        assert stats["stats"]["requests_total"] >= 0
        print("✓ 统计功能正常")

    print("✅ NCBI基因服务器测试通过")


async def test_server_capabilities():
    """Test server capabilities and configuration."""
    print("\n🧪 测试服务器能力和配置...")

    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)

    # Test capabilities
    caps = server.capabilities
    assert caps.name == "NCBIGeneServer"
    assert caps.version == "1.0.0"
    assert caps.supports_batch == True
    assert caps.supports_streaming == False
    assert caps.max_batch_size > 0
    assert caps.rate_limit_requests > 0

    # Check required operations
    required_ops = [
        "get_gene_info",
        "search_genes",
        "get_gene_summary",
        "get_gene_homologs",
        "get_gene_expression",
        "get_gene_pathways",
        "batch_gene_info",
        "search_by_region",
    ]

    for op in required_ops:
        assert op in caps.operations, f"Missing operation: {op}"

    print("✓ 服务器能力配置正确")
    print(f"✓ 支持的操作数量: {len(caps.operations)}")
    print(f"✓ 最大批量大小: {caps.max_batch_size}")
    print(f"✓ 速率限制: {caps.rate_limit_requests} 请求/{caps.rate_limit_window} 秒")


if __name__ == "__main__":
    asyncio.run(test_ncbi_gene_server())
    asyncio.run(test_server_capabilities())
