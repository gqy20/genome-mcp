"""
核心功能单元测试
"""

import os
import sys

import pytest

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from genome_mcp.main import QueryParser, QueryType, _format_simple_result


class TestQueryParser:
    """查询解析器测试"""

    def test_parse_gene_info(self):
        """测试基因信息查询解析"""
        parsed = QueryParser.parse("TP53", "info")
        assert parsed.type == QueryType.INFO
        assert parsed.query == "TP53"
        assert parsed.params["gene_id"] == "TP53"

    def test_parse_search(self):
        """测试搜索查询解析"""
        parsed = QueryParser.parse("cancer", "search")
        assert parsed.type == QueryType.SEARCH
        assert parsed.query == "cancer"
        assert parsed.params["term"] == "cancer"

    def test_parse_region(self):
        """测试区域查询解析"""
        parsed = QueryParser.parse("chr17:7565097-7590856", "region")
        assert parsed.type == QueryType.REGION
        assert parsed.params["chromosome"] == "chr17"
        assert parsed.params["start"] == 7565097
        assert parsed.params["end"] == 7590856

    def test_parse_batch(self):
        """测试批量查询解析"""
        gene_ids = ["TP53", "BRCA1", "EGFR"]
        parsed = QueryParser.parse(gene_ids, "batch")
        assert parsed.type == QueryType.BATCH
        assert parsed.params["gene_ids"] == gene_ids
        assert parsed.is_batch

    def test_auto_recognition_gene_id(self):
        """测试自动识别基因ID"""
        parsed = QueryParser.parse("TP53", "auto")
        assert parsed.type == QueryType.INFO

    def test_auto_recognition_region(self):
        """测试自动识别区域格式"""
        test_cases = [
            "chr17:7565097-7590856",
            "17:7565097-7590856",
            "chr17[7565097-7590856]",
            "17[7565097-7590856]",
        ]

        for region in test_cases:
            parsed = QueryParser.parse(region, "auto")
            assert parsed.type == QueryType.REGION, f"Failed for {region}"

    def test_auto_recognition_search(self):
        """测试自动识别搜索"""
        parsed = QueryParser.parse("cancer genes", "auto")
        assert parsed.type == QueryType.SEARCH

    def test_auto_recognition_batch(self):
        """测试自动识别批量查询"""
        parsed = QueryParser.parse(["TP53", "BRCA1"], "auto")
        assert parsed.type == QueryType.BATCH

    def test_invalid_region_format(self):
        """测试无效区域格式"""
        with pytest.raises(ValueError):
            QueryParser.parse("invalid_region", "region")


class TestFormatResult:
    """结果格式化测试"""

    def test_format_simple_gene_result(self):
        """测试简单基因结果格式化"""
        result = {
            "gene_id": "TP53",
            "uid": "7157",
            "data": {
                "name": "tumor protein p53",
                "description": "This gene encodes tumor protein p53",
                "chromosome": "17p13.1",
                "summary": "TP53 is a tumor suppressor gene that responds to various cellular stressors",
            },
        }

        formatted = _format_simple_result(result)

        assert formatted["gene_id"] == "TP53"
        assert formatted["name"] == "tumor protein p53"
        assert formatted["description"] == "This gene encodes tumor protein p53"
        assert formatted["chromosome"] == "17p13.1"
        assert "TP53 is a tumor suppressor" in formatted["summary"]
        assert len(formatted["summary"]) <= 203  # 200 chars + "..."

    def test_format_batch_result(self):
        """测试批量结果格式化"""
        result = {
            "batch_size": 3,
            "results": {
                "TP53": {"gene_id": "TP53", "data": {"name": "TP53"}},
                "BRCA1": {"gene_id": "BRCA1", "data": {"name": "BRCA1"}},
                "INVALID": {"error": "Gene not found"},
            },
        }

        formatted = _format_simple_result(result)

        assert formatted["batch_size"] == 3
        assert formatted["successful_count"] == 2
        assert "TP53" in formatted["results"]
        assert "BRCA1" in formatted["results"]
        assert "INVALID" not in formatted["results"]  # 错误结果被过滤

    def test_format_error_result(self):
        """测试错误结果格式化"""
        result = {"error": "Gene not found", "gene_id": "INVALID"}

        formatted = _format_simple_result(result)

        assert formatted == result  # 错误结果直接返回

    def test_format_result_with_none_data(self):
        """测试空数据处理"""
        result = {"gene_id": "TP53", "data": None}

        formatted = _format_simple_result(result)

        assert formatted == result  # 空数据直接返回

    def test_format_result_with_long_summary(self):
        """测试长摘要截断"""
        long_summary = "A" * 300
        result = {"gene_id": "TP53", "data": {"name": "TP53", "summary": long_summary}}

        formatted = _format_simple_result(result)

        assert len(formatted["summary"]) <= 203
        assert formatted["summary"].endswith("...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
