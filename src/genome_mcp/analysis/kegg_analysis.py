#!/usr/bin/env python3
"""
KEGG通路富集分析 - MVP版本
提供KEGG通路的富集分析功能
"""

from typing import Any

import aiohttp

from .simple_stats import (
    benjamini_hochberg_fdr,
    calculate_fold_enrichment,
    filter_significant_results,
    hypergeometric_test,
)


class KEGGEnrichment:
    """KEGG通路富集分析器"""

    def __init__(self):
        self.session: aiohttp.ClientSession | None = None

        # 常用生物体的基因总数估计值
        self.background_gene_counts = {
            "hsa": 20000,  # 人类
            "mmu": 23000,  # 小鼠
            "rno": 25000,  # 大鼠
            "dre": 26000,  # 斑马鱼
            "cel": 20000,  # 线虫
            "dme": 14000,  # 果蝇
            "sce": 6000,  # 酵母
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def analyze_pathways(
        self,
        gene_list: list[str],
        organism: str = "hsa",
        pvalue_threshold: float = 0.05,
        min_gene_count: int = 2,
    ) -> dict[str, Any]:
        """
        执行KEGG通路富集分析

        Args:
            gene_list: 基因列表
            organism: 生物体代码 (如 "hsa" 人类)
            pvalue_threshold: p值阈值
            min_gene_count: 通路中最小基因数量

        Returns:
            富集分析结果
        """
        try:
            # 1. 获取基因-通路映射
            gene_pathway_mapping = await self._get_gene_pathway_mapping(
                gene_list, organism
            )

            if not gene_pathway_mapping:
                return {
                    "error": "未找到任何通路映射",
                    "query_genes": gene_list,
                    "organism": organism,
                }

            # 2. 构建通路-基因反向映射
            pathway_gene_mapping = self._build_pathway_gene_mapping(
                gene_pathway_mapping
            )

            # 3. 获取背景信息
            background_total = self._get_background_gene_count(organism)

            # 4. 执行富集分析
            enrichment_results = await self._calculate_enrichment(
                pathway_gene_mapping, gene_list, organism, background_total
            )

            # 5. FDR校正
            corrected_results = benjamini_hochberg_fdr(
                enrichment_results, alpha=pvalue_threshold
            )

            # 6. 过滤显著结果
            significant_results = filter_significant_results(
                corrected_results,
                fdr_threshold=pvalue_threshold,
                min_gene_count=min_gene_count,
            )

            return {
                "query_genes": gene_list,
                "organism": organism,
                "background_gene_count": background_total,
                "total_pathways_found": len(corrected_results),
                "significant_pathway_count": len(significant_results),
                "all_pathways": corrected_results,
                "significant_pathways": significant_results,
                "analysis_parameters": {
                    "pvalue_threshold": pvalue_threshold,
                    "min_gene_count": min_gene_count,
                },
            }

        except Exception as e:
            return {
                "error": f"KEGG分析失败: {str(e)}",
                "query_genes": gene_list,
                "organism": organism,
            }

    async def _get_gene_pathway_mapping(
        self, gene_list: list[str], organism: str
    ) -> dict[str, list[str]]:
        """获取基因-通路映射关系"""
        if not self.session:
            raise RuntimeError("客户端未初始化，请使用 async with 语法")

        # 构建KEGG查询URL
        gene_str = "+".join(gene_list)
        url = f"https://rest.kegg.jp/link/pathway/{organism}:{gene_str}"

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {}

                text = await response.text()

                # 解析结果
                gene_pathway_mapping = {}
                for line in text.strip().split("\n"):
                    if "\t" in line:
                        gene_id, pathway_id = line.split("\t", 1)

                        # 标准化基因ID格式
                        gene_id = self._normalize_gene_id(gene_id)

                        if gene_id not in gene_pathway_mapping:
                            gene_pathway_mapping[gene_id] = []
                        gene_pathway_mapping[gene_id].append(pathway_id)

                return gene_pathway_mapping

        except Exception as e:
            print(f"KEGG API调用失败: {e}")
            return {}

    def _build_pathway_gene_mapping(
        self, gene_pathway_mapping: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        """构建通路-基因反向映射"""
        pathway_gene_mapping = {}

        for gene_id, pathways in gene_pathway_mapping.items():
            for pathway_id in pathways:
                if pathway_id not in pathway_gene_mapping:
                    pathway_gene_mapping[pathway_id] = []
                pathway_gene_mapping[pathway_id].append(gene_id)

        return pathway_gene_mapping

    async def _calculate_enrichment(
        self,
        pathway_gene_mapping: dict[str, list[str]],
        query_genes: list[str],
        organism: str,
        background_total: int,
    ) -> list[dict[str, Any]]:
        """计算富集显著性"""
        results = []
        query_total = len(query_genes)

        # 获取所有通路的信息用于背景计算
        all_pathway_info = await self._get_all_pathway_info(organism)

        for pathway_id, pathway_genes in pathway_gene_mapping.items():
            query_count = len(pathway_genes)

            # 获取通路中总的基因数
            pathway_total = all_pathway_info.get(pathway_id, {}).get(
                "gene_count", query_count
            )

            if pathway_total == 0:
                continue

            # 计算超几何检验p值
            p_value = hypergeometric_test(
                k=query_count,  # 查询基因中该通路基因数
                K=pathway_total,  # 背景中该通路基因总数
                n=query_total,  # 查询基因总数
                N=background_total,  # 背景基因总数
            )

            # 计算富集倍数
            fold_enrichment = calculate_fold_enrichment(
                query_count, query_total, pathway_total, background_total
            )

            results.append(
                {
                    "pathway_id": pathway_id,
                    "pathway_name": all_pathway_info.get(pathway_id, {}).get(
                        "name", pathway_id
                    ),
                    "genes": pathway_genes,
                    "gene_count": query_count,
                    "pathway_gene_count": pathway_total,
                    "pvalue": p_value,
                    "fold_enrichment": fold_enrichment,
                }
            )

        return results

    async def _get_all_pathway_info(self, organism: str) -> dict[str, dict[str, Any]]:
        """获取生物体所有通路的基本信息"""
        if not self.session:
            raise RuntimeError("客户端未初始化")

        url = f"https://rest.kegg.jp/list/pathway/{organism}"

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {}

                text = await response.text()
                pathway_info = {}

                for line in text.strip().split("\n"):
                    if "\t" in line:
                        pathway_id, pathway_name = line.split("\t", 1)
                        pathway_info[pathway_id] = {
                            "name": pathway_name,
                            "gene_count": 0,  # 暂时设为0，实际中可以通过其他API获取
                        }

                return pathway_info

        except Exception as e:
            print(f"获取通路信息失败: {e}")
            return {}

    def _normalize_gene_id(self, gene_id: str) -> str:
        """标准化基因ID格式"""
        # KEGG返回的基因ID格式可能是 organism:gene_id
        if ":" in gene_id:
            return gene_id.split(":", 1)[1]
        return gene_id

    def _get_background_gene_count(self, organism: str) -> int:
        """获取背景基因总数"""
        return self.background_gene_counts.get(organism, 20000)
