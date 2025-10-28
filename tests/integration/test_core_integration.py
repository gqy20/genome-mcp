"""
核心集成测试
"""

import os
import sys

import pytest

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from genome_mcp.core import QueryParser
from genome_mcp.core.tools import _query_executor


class TestCoreIntegration:
    """核心功能集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_gene_query(self):
        """端到端基因查询测试"""
        # 1. 解析查询
        parsed = QueryParser.parse("TP53", "auto")
        assert parsed.type.value == "info"

        # 2. 执行查询
        result = await _query_executor.execute(parsed)

        # 3. 验证结果
        assert "gene_id" in result or "error" in result
        if "gene_id" in result:
            assert result["gene_id"] == "TP53"

    @pytest.mark.asyncio
    async def test_end_to_end_search(self):
        """端到端搜索测试"""
        # 1. 解析查询
        parsed = QueryParser.parse("cancer", "auto")
        assert parsed.type.value == "search"

        # 2. 执行查询
        result = await _query_executor.execute(parsed)

        # 3. 验证结果
        assert "term" in result
        assert result["term"] == "cancer"
        assert "total_count" in result
        assert isinstance(result["total_count"], int)

    @pytest.mark.asyncio
    async def test_end_to_end_region_search(self):
        """端到端区域搜索测试"""
        # 1. 解析查询
        parsed = QueryParser.parse("chr17:7565097-7590856", "auto")
        assert parsed.type.value == "region"

        # 2. 执行查询
        result = await _query_executor.execute(parsed)

        # 3. 验证结果
        assert "chromosome" in result
        assert "start" in result
        assert "end" in result
        assert "genes_found" in result

    @pytest.mark.asyncio
    async def test_end_to_end_batch_query(self):
        """端到端批量查询测试"""
        # 1. 解析查询
        gene_ids = ["TP53", "BRCA1"]
        parsed = QueryParser.parse(gene_ids, "auto")
        assert parsed.type.value == "batch"

        # 2. 执行查询
        result = await _query_executor.execute(parsed)

        # 3. 验证结果
        assert "batch_size" in result
        assert result["batch_size"] == len(gene_ids)
        assert "results" in result

    def test_intelligent_query_recognition(self):
        """智能查询识别测试"""
        test_cases = [
            ("TP53", "info"),
            ("BRCA1", "info"),
            ("chr17:7565097-7590856", "region"),
            ("17[7565097-7590856]", "region"),
            ("cancer genes", "search"),
            (["TP53", "BRCA1"], "batch"),
        ]

        for query, expected_type in test_cases:
            parsed = QueryParser.parse(query, "auto")
            assert parsed.type.value == expected_type, f"Failed for {query}"

    def test_error_handling(self):
        """错误处理测试"""
        # 测试无效区域格式
        with pytest.raises(ValueError):
            QueryParser.parse("invalid_region", "region")

        # 测试空批量查询应该能处理
        parsed = QueryParser.parse([], "batch")
        assert parsed.type.value == "batch"
        assert parsed.params["gene_ids"] == []


class TestMCPToolStructure:
    """MCP工具结构测试"""

    def test_mcp_tools_structure(self):
        """测试MCP工具结构"""
        from genome_mcp.main import mcp

        # 验证MCP实例存在并可用
        assert mcp is not None, "MCP instance should exist"

        # 验证MCP服务器具有基本属性
        assert hasattr(mcp, "name"), "MCP should have name attribute"
        assert hasattr(mcp, "version"), "MCP should have version attribute"

        # 验证MCP服务器名称和版本
        assert mcp.name == "Genome MCP"
        assert "0.2.5" in mcp.version


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
