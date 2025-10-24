"""
KEGG MVP功能测试

测试KEGG通路富集分析的核心功能
"""

import asyncio
import os
import sys

import pytest

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from genome_mcp.analysis.kegg_analysis import KEGGEnrichment
from genome_mcp.utils.validation import ValidationError


class TestKEGGMVP:
    """KEGG MVP功能测试"""

    @pytest.mark.asyncio
    async def test_kegg_enrichment_basic(self):
        """测试基础通路富集分析"""
        analyzer = KEGGEnrichment()

        # 测试数据：癌症相关基因（使用Entrez ID）
        test_genes = ["7157", "672", "675"]  # TP53, BRCA1, BRCA2的Entrez ID
        organism = "hsa"

        async with analyzer:
            result = await analyzer.analyze_pathways(
                gene_list=test_genes,
                organism=organism,
                pvalue_threshold=0.1,  # 放宽阈值用于测试
                min_gene_count=1,
            )

        # 验证结果结构
        assert "query_genes" in result
        assert result["query_genes"] == test_genes
        assert "organism" in result
        assert result["organism"] == organism
        assert "all_pathways" in result
        assert isinstance(result["all_pathways"], list)

        # 如果找到了通路，验证通路数据结构
        if result["all_pathways"]:
            pathway = result["all_pathways"][0]
            assert "pathway_id" in pathway
            assert "genes" in pathway
            assert "pvalue" in pathway
            assert "fold_enrichment" in pathway
            assert 0 <= pathway["pvalue"] <= 1

    @pytest.mark.asyncio
    async def test_kegg_enrichment_empty_genes(self):
        """测试空基因列表"""
        analyzer = KEGGEnrichment()

        async with analyzer:
            result = await analyzer.analyze_pathways(gene_list=[], organism="hsa")

        # 应该返回错误或空结果
        assert "error" in result or result.get("total_pathways_found", 0) == 0

    @pytest.mark.asyncio
    async def test_kegg_enrichment_invalid_organism(self):
        """测试无效生物体"""
        analyzer = KEGGEnrichment()

        async with analyzer:
            result = await analyzer.analyze_pathways(
                gene_list=["TP53"], organism="invalid"
            )

        # 应该能处理或返回错误
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_kegg_client_basic(self):
        """测试KEGG客户端基本功能"""
        from genome_mcp.core.clients import KEGGClient

        client = KEGGClient()

        async with client:
            # 测试获取通路列表
            pathways = await client.get_pathway_list("hsa")
            assert isinstance(pathways, dict)
            assert "pathways" in pathways

            if pathways["pathways"]:
                # 验证通路数据格式
                pathway_id, pathway_name = list(pathways["pathways"].items())[0]
                assert isinstance(pathway_id, str)
                assert isinstance(pathway_name, str)

    @pytest.mark.asyncio
    async def test_statistics_hypergeometric_test(self):
        """测试超几何分布检验"""
        from genome_mcp.analysis.simple_stats import hypergeometric_test

        # 测试基本情况
        p = hypergeometric_test(k=5, K=100, n=20, N=10000)
        assert 0 <= p <= 1

        # 测试边界情况
        p = hypergeometric_test(k=0, K=100, n=20, N=10000)
        assert p == 1.0

    @pytest.mark.asyncio
    async def test_statistics_fdr_correction(self):
        """测试FDR校正"""
        from genome_mcp.analysis.simple_stats import benjamini_hochberg_fdr

        # 创建测试数据
        test_data = [
            {"pvalue": 0.001},
            {"pvalue": 0.05},
            {"pvalue": 0.1},
            {"pvalue": 0.2},
        ]

        corrected = benjamini_hochberg_fdr(test_data)

        # 验证FDR校正结果
        assert len(corrected) == len(test_data)
        for result in corrected:
            assert "fdr" in result
            assert 0 <= result["fdr"] <= 1
            assert result["fdr"] >= result["pvalue"]

    def test_validation_gene_list(self):
        """测试基因列表验证"""
        from genome_mcp.utils.validation import validate_gene_list

        # 测试有效基因列表
        validate_gene_list(["TP53", "BRCA1", "EGFR"])

        # 测试空基因列表
        with pytest.raises(ValidationError):
            validate_gene_list([])

        # 测试单个基因
        with pytest.raises(ValidationError):
            validate_gene_list(["TP53"])

        # 测试无效基因ID
        with pytest.raises(ValidationError):
            validate_gene_list(["", "  "])

    def test_validation_organism(self):
        """测试生物体验证"""
        from genome_mcp.utils.validation import validate_organism

        # 测试有效生物体
        validate_organism("hsa")
        validate_organism("mmu")
        validate_organism("HSA")  # 应该能转换为大写

        # 测试无效生物体
        with pytest.raises(ValidationError):
            validate_organism("invalid")

        # 测试空生物体
        with pytest.raises(ValidationError):
            validate_organism("")

    def test_validation_parameters(self):
        """测试参数验证"""
        from genome_mcp.utils.validation import validate_parameters

        # 测试有效参数
        params = {
            "gene_list": ["TP53", "BRCA1"],
            "organism": "hsa",
            "pvalue_threshold": 0.05,
        }
        validated = validate_parameters(params)
        assert "gene_list" in validated
        assert "organism" in validated
        assert "pvalue_threshold" in validated

        # 测试默认值设置
        params = {"gene_list": ["TP53", "BRCA1"]}
        validated = validate_parameters(params)
        assert validated["organism"] == "hsa"
        assert validated["pvalue_threshold"] == 0.05

    def test_utility_clean_gene_list(self):
        """测试基因列表清理"""
        from genome_mcp.utils.validation import clean_gene_list

        # 测试包含无效数据的基因列表
        messy_genes = ["TP53", "", " BRCA1", "invalid", "EGFR", "  TP53  "]
        cleaned = clean_gene_list(messy_genes)

        assert isinstance(cleaned, list)
        assert "TP53" in cleaned
        assert "BRCA1" in cleaned
        assert "EGFR" in cleaned
        assert "" not in cleaned
        assert "invalid" not in cleaned
        assert len(set(cleaned)) == len(cleaned)  # 无重复


if __name__ == "__main__":
    # 简单的测试运行
    async def run_basic_test():
        test = TestKEGGMVP()
        await test.test_kegg_enrichment_basic()
        print("✅ 基础通路富集分析测试通过")

    asyncio.run(run_basic_test())
