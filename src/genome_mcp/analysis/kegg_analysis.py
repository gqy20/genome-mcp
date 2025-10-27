#!/usr/bin/env python3
"""
KEGG通路富集分析 - MVP版本
提供KEGG通路的富集分析功能
"""

import asyncio
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
            # 检查输入参数
            if not gene_list:
                return {
                    "error": "基因列表为空",
                    "query_genes": gene_list,
                    "organism": organism,
                    "error_type": "validation_error",
                    "suggestions": ["提供至少一个基因ID", "检查基因ID格式是否正确"],
                }

            # 特殊处理单基因情况
            if len(gene_list) == 1:
                return await self._analyze_single_gene_pathways(
                    gene_list, organism, pvalue_threshold
                )

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

        # 先解析基因符号为Entrez ID
        resolved_genes = await self._resolve_gene_symbols(gene_list, organism)
        if not resolved_genes:
            return {
                "error": "未找到有效的基因ID",
                "suggestions": ["检查基因符号是否正确"],
            }

        # 构建KEGG查询URL
        gene_str = "+".join(resolved_genes)
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

    async def _resolve_gene_symbols(
        self, gene_list: list[str], organism: str
    ) -> list[str]:
        """改进的基因符号解析为Entrez ID"""
        resolved = []

        for gene in gene_list:
            # 如果已经是数字ID，直接使用
            if gene.isdigit():
                resolved.append(gene)
                continue

            # 跳过空字符串
            if not gene or not gene.strip():
                continue

            # 尝试多种方法解析基因符号
            gene_resolved = await self._resolve_single_gene_symbol(gene, organism)
            if gene_resolved:
                resolved.append(gene_resolved)

        return resolved

    async def _resolve_single_gene_symbol(
        self, gene_symbol: str, organism: str
    ) -> str | None:
        """解析单个基因符号"""
        try:
            url = f"https://rest.kegg.jp/find/{organism}/{gene_symbol}"
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None

                text = await response.text()
                if not text.strip():
                    return None

                # 解析返回结果，寻找最匹配的Entrez ID
                best_match = None
                exact_match = None

                for line in text.strip().split("\n"):
                    if not line or "\t" not in line:
                        continue

                    parts = line.split("\t")
                    if len(parts) < 2:
                        continue

                    kegg_id = parts[0]
                    description = parts[1]

                    if ":" in kegg_id:
                        entrez_id = kegg_id.split(":")[1]
                        if not entrez_id.isdigit():
                            continue

                        # 检查精确匹配
                        desc_lower = description.lower()
                        gene_lower = gene_symbol.lower()

                        if (
                            desc_lower.startswith(gene_lower + " ")
                            or desc_lower.startswith(gene_lower + ";")
                            or desc_lower.startswith(gene_lower + ",")
                            or f" ({gene_symbol})" in description
                            or f"[{gene_symbol}]" in description
                        ):
                            exact_match = entrez_id
                            break
                        elif best_match is None:
                            # 如果没有精确匹配，选择第一个数字ID
                            best_match = entrez_id

                # 优先返回精确匹配
                return exact_match or best_match

        except asyncio.TimeoutError:
            print(f"KEGG API超时: {gene_symbol}")
        except Exception as e:
            print(f"解析基因符号 {gene_symbol} 失败: {e}")

        return None

    def _get_background_gene_count(self, organism: str) -> int:
        """获取背景基因总数"""
        return self.background_gene_counts.get(organism, 20000)

    async def _analyze_single_gene_pathways(
        self, gene_list: list[str], organism: str, pvalue_threshold: float
    ) -> dict[str, Any]:
        """
        分析单个基因相关的通路

        对于单基因情况，不进行统计富集分析，而是直接返回该基因参与的所有通路
        """
        try:
            original_gene_symbol = gene_list[0]

            # 1. 解析基因符号为Entrez ID
            resolved_genes = await self._resolve_gene_symbols(gene_list, organism)
            if not resolved_genes:
                return {
                    "error": f"无法解析基因符号 '{original_gene_symbol}'",
                    "query_genes": gene_list,
                    "organism": organism,
                    "error_type": "gene_resolution_failed",
                    "suggestions": [
                        "检查基因符号是否正确",
                        "确认该基因在KEGG数据库中存在",
                        "尝试使用该基因的其他名称或别名",
                    ],
                }

            resolved_gene_id = resolved_genes[0]

            # 2. 获取基因-通路映射（使用解析后的基因ID）
            gene_pathway_mapping = await self._get_gene_pathway_mapping(
                resolved_genes, organism
            )

            if not gene_pathway_mapping or resolved_gene_id not in gene_pathway_mapping:
                return {
                    "error": f"未找到基因 '{original_gene_symbol}' 的通路信息",
                    "query_genes": gene_list,
                    "organism": organism,
                    "error_type": "no_pathways_found",
                    "suggestions": [
                        "检查基因符号是否正确",
                        "确认该基因在KEGG数据库中存在",
                        "尝试使用该基因的其他名称或别名",
                    ],
                }

            # 2. 获取通路详细信息
            pathway_ids = gene_pathway_mapping[resolved_gene_id]
            pathway_details = []

            for pathway_id in pathway_ids:
                # 获取通路名称和描述
                pathway_info = await self._get_pathway_details(pathway_id)
                if pathway_info:
                    pathway_details.append(
                        {
                            "pathway_id": pathway_id,
                            "pathway_name": pathway_info.get("name", pathway_id),
                            "description": pathway_info.get("description", ""),
                            "genes": [original_gene_symbol],  # 显示原始基因符号
                            "resolved_gene_id": resolved_gene_id,  # 添加解析后的基因ID
                            "gene_count": 1,
                            "analysis_type": "single_gene_pathway_listing",
                        }
                    )

            # 3. 按通路名称排序
            pathway_details.sort(key=lambda x: x["pathway_name"])

            return {
                "query_genes": gene_list,
                "organism": organism,
                "background_gene_count": self._get_background_gene_count(organism),
                "total_pathways_found": len(pathway_details),
                "significant_pathway_count": len(
                    pathway_details
                ),  # 对于单基因，所有找到的通路都是"显著"的
                "all_pathways": pathway_details,
                "significant_pathways": pathway_details,
                "analysis_parameters": {
                    "pvalue_threshold": pvalue_threshold,
                    "min_gene_count": 1,
                    "analysis_type": "single_gene_analysis",
                },
                "analysis_info": {
                    "type": "single_gene_pathway_analysis",
                    "note": "单基因分析显示该基因参与的所有通路，不进行统计富集检验",
                    "gene_count": 1,
                },
            }

        except Exception as e:
            return {
                "error": f"单基因通路分析失败: {str(e)}",
                "query_genes": gene_list,
                "organism": organism,
                "error_type": "single_gene_analysis_error",
                "suggestions": [
                    "检查基因符号是否正确",
                    "确认网络连接正常",
                    "稍后重试",
                ],
            }

    async def _get_pathway_details(self, pathway_id: str) -> dict[str, Any]:
        """获取通路详细信息"""
        if not self.session:
            raise RuntimeError("客户端未初始化")

        try:
            url = f"https://rest.kegg.jp/get/{pathway_id}"
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return {"name": pathway_id, "description": ""}

                text = await response.text()

                # 解析KEGG通路信息
                name = ""
                description = ""
                class_info = ""

                for line in text.split("\n"):
                    if line.startswith("NAME"):
                        name = line.replace("NAME", "").strip()
                    elif line.startswith("DESCRIPTION"):
                        description = line.replace("DESCRIPTION", "").strip()
                    elif line.startswith("CLASS"):
                        class_info = line.replace("CLASS", "").strip()

                return {
                    "name": name,
                    "description": description,
                    "class": class_info,
                }

        except Exception as e:
            print(f"获取通路 {pathway_id} 详情失败: {e}")
            return {"name": pathway_id, "description": ""}
