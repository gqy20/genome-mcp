#!/usr/bin/env python3
"""
MCP工具模块 - 实现所有MCP工具接口

包含主要的基因组数据查询和分析工具
"""

import asyncio
from typing import Any

from fastmcp import FastMCP

from .evolution_tools import analyze_gene_evolution, build_phylogenetic_profile
from .query_executor import QueryExecutor
from .query_parser import QueryParser

# 全局查询执行器实例
_query_executor = QueryExecutor()


def _format_simple_result(result: dict[str, Any]) -> dict[str, Any]:
    """格式化简单结果"""
    if "error" in result:
        return result

    # 根据查询类型简化结果
    if result.get("source") == "cache":
        return {"gene_id": result["gene_id"], "data": result["data"]}

    if result.get("source") == "ncbi":
        gene_data = result.get("data", {})
        return {
            "gene_id": result.get("gene_id"),
            "name": gene_data.get("name", ""),
            "description": gene_data.get("description", ""),
            "chromosome": gene_data.get("chromosome", ""),
            "summary": gene_data.get("summary", ""),
        }

    if result.get("source") == "integrated":
        return {
            "gene_query": result.get("gene_query"),
            "gene_found": result.get("integration_info", {}).get("gene_found", False),
            "protein_count": result.get("integration_info", {}).get("protein_count", 0),
        }

    return result


def _apply_filters(query: str, filters: dict[str, Any] = None) -> str:
    """应用搜索过滤器"""
    if not filters:
        return query

    filter_parts = []

    # 物种过滤
    if "species" in filters:
        species = filters["species"].lower()
        if species != "human":
            filter_parts.append(f"{species}[organism]")

    # 基因类型过滤
    if "gene_type" in filters:
        gene_type = filters["gene_type"]
        if gene_type == "protein_coding":
            filter_parts.append("protein_coding[Properties]")

    # 合并过滤器
    if filter_parts:
        return f"{query} AND {' AND '.join(filter_parts)}"

    return query


def create_mcp_tools(mcp: FastMCP) -> None:
    """创建并注册所有MCP工具"""

    @mcp.tool()
    async def get_data(
        query: str | list[str],
        query_type: str = "auto",
        data_type: str = "gene",
        format: str = "simple",
        species: str = "human",
        max_results: int = 20,
    ) -> dict[str, Any]:
        """
        智能数据获取接口 - 统一处理所有查询类型

        自动识别查询类型：
        - "TP53" → 基因信息查询
        - "P04637" → 蛋白质详细信息查询
        - "cancer" → 基因搜索
        - "protein kinase" → 蛋白质功能搜索
        - "chr17:7565097-7590856" → 区域搜索
        - "TP53, BRCA1" → 批量基因信息
        - "breast cancer genes" → 智能搜索
        - "TP53 homologs" → 同源基因查询
        - "evolutionary conservation" → 进化分析查询

        Args:
            query: 查询内容（可以是基因ID、蛋白质ID、搜索词、区域、ID列表、进化相关查询）
            query_type: 查询类型（auto/info/search/region/protein/gene_protein/ortholog/evolution）
            data_type: 数据类型（gene/protein/gene_protein/ortholog/evolution）
            format: 返回格式（simple/detailed/raw）
            species: 物种（默认：human，支持9606/human/mouse/rat等）
            max_results: 最大结果数（默认：20）

        Returns:
            查询结果字典，包含基因和/或蛋白质信息

        Examples:
            # 基因信息查询
            get_data("TP53")
            get_data("TP53", format="detailed")

            # 批量查询
            get_data(["TP53", "BRCA1", "BRCA2"])

            # 区域搜索
            get_data("chr17:7565097-7590856")

            # 蛋白质查询
            get_data("P04637", data_type="protein")

            # 基因-蛋白质整合查询
            get_data("TP53", data_type="gene_protein")

            # 蛋白质功能搜索
            get_data("tumor suppressor", data_type="protein")
        """
        try:
            # 根据data_type参数调整查询类型
            if data_type == "protein" and query_type == "auto":
                query_type = "protein"
            elif data_type == "gene_protein" and query_type == "auto":
                query_type = "gene_protein"
            elif data_type == "ortholog" and query_type == "auto":
                query_type = "ortholog"
            elif data_type == "evolution" and query_type == "auto":
                query_type = "evolution"
            elif data_type == "gene" and query_type == "auto":
                query_type = "auto"  # 保持原有的自动识别

            # 解析查询意图
            parsed = QueryParser.parse(query, query_type)

            # 添加物种信息到参数中
            organism_mapping = {
                "human": "9606",
                "mouse": "10090",
                "rat": "10116",
                "zebrafish": "7955",
                "fruitfly": "7227",
                "worm": "6239",
            }
            if "organism" not in parsed.params:
                organism_code = organism_mapping.get(species.lower(), "9606")
                parsed.params["organism"] = organism_code

            # 执行查询
            result = await _query_executor.execute(parsed, max_results=max_results)

            # 格式化结果
            if format == "simple":
                return _format_simple_result(result)
            elif format == "detailed":
                return result
            else:
                return result

        except Exception as e:
            return {"error": str(e), "query": query, "data_type": data_type}

    @mcp.tool()
    async def advanced_query(
        queries: list[dict[str, Any]],
        strategy: str = "parallel",
        delay: float = 0.34,  # NCBI API频率限制
    ) -> dict[str, Any]:
        """
        高级批量查询 - 支持复杂查询策略

        Args:
            queries: 查询列表，每个元素包含 {"query": str, "type": str}
            strategy: 执行策略（parallel/sequential）
            delay: 查询间隔（秒）

        Returns:
            批量查询结果

        Examples:
            advanced_query([
                {"query": "TP53", "type": "info"},
                {"query": "BRCA1", "type": "info"},
                {"query": "cancer", "type": "search"}
            ])
        """
        results = {}

        async def execute_single_query(index: int, query_dict: dict[str, Any]):
            try:
                parsed = QueryParser.parse_by_type(
                    query_dict["query"], query_dict.get("type", "auto")
                )
                result = await _query_executor.execute(parsed, **query_dict)
                results[index] = result
                await asyncio.sleep(delay)  # 遵守频率限制
            except Exception as e:
                results[index] = {"error": str(e), "query": query_dict}

        if strategy == "parallel":
            # 并发查询
            await asyncio.gather(
                *[execute_single_query(i, q) for i, q in enumerate(queries)]
            )

        else:
            # 顺序查询（适用于依赖查询）
            for i, query_dict in enumerate(queries):
                try:
                    parsed = QueryParser.parse_by_type(
                        query_dict["query"], query_dict.get("type", "auto")
                    )
                    result = await _query_executor.execute(parsed, **query_dict)
                    results[i] = result
                    await asyncio.sleep(delay)  # 遵守频率限制
                except Exception as e:
                    results[i] = {"error": str(e), "query": query_dict}

        return {
            "strategy": strategy,
            "total_queries": len(queries),
            "successful": len([r for r in results.values() if "error" not in r]),
            "results": results,
        }

    @mcp.tool()
    async def smart_search(
        description: str,
        context: str = "genomics",
        filters: dict[str, Any] = None,
        max_results: int = 20,
    ) -> dict[str, Any]:
        """
        智能语义搜索 - 理解自然语言描述并执行相应查询

        语义理解示例：
        - "breast cancer genes on chromosome 17" → 查找17号染色体上的乳腺癌基因
        - "TP53 protein interactions" → 查找TP53蛋白相互作用
        - "tumor suppressor genes" → 查找肿瘤抑制基因
        - "genes related to DNA repair" → 查找DNA修复相关基因

        Args:
            description: 自然语言描述
            context: 搜索上下文（genomics/proteomics/pathway）
            filters: 过滤条件
            max_results: 最大结果数

        Returns:
            智能搜索结果

        Examples:
            smart_search("breast cancer genes on chromosome 17")
            smart_search("TP53 protein interactions", context="proteomics")
            smart_search("DNA repair genes", filters={"species": "human"})
        """
        try:
            # 智能解析查询意图
            query = _apply_filters(description, filters)

            # 根据上下文调整查询
            if context == "proteomics":
                query_type = "protein"
            elif context == "pathway":
                query_type = "search"
            else:
                query_type = "auto"

            # 执行查询
            result = await get_data(
                query=query,
                query_type=query_type,
                max_results=max_results,
                format="detailed",
            )

            # 添加智能解析信息
            result["smart_search_info"] = {
                "description": description,
                "context": context,
                "parsed_query": query,
                "filters_applied": filters is not None,
            }

            return result

        except Exception as e:
            return {"error": str(e), "description": description}

    @mcp.tool()
    async def analyze_gene_evolution_tool(
        gene_symbol: str,
        target_species: list[str] = None,
        analysis_level: str = "Eukaryota",
        include_sequence_info: bool = True,
    ) -> dict[str, Any]:
        """
        基因进化分析工具 - MCP接口包装

        Args:
            gene_symbol: 基因符号（如 TP53, BRCA1）
            target_species: 目标物种列表（如 ["mouse", "rat", "zebrafish"]）
            analysis_level: 分析层级（如 Eukaryota, Metazoa, Vertebrata）
            include_sequence_info: 是否包含序列信息

        Returns:
            进化分析结果

        Examples:
            # 分析 TP53 在哺乳动物中的进化
            analyze_gene_evolution_tool("TP53", ["human", "mouse", "rat", "dog"])
        """
        return await analyze_gene_evolution(
            gene_symbol,
            target_species,
            analysis_level,
            include_sequence_info,
            _query_executor,
        )

    @mcp.tool()
    async def build_phylogenetic_profile_tool(
        gene_symbols: list[str],
        species_set: list[str] = None,
        include_domain_info: bool = True,
    ) -> dict[str, Any]:
        """
        系统发育图谱构建工具 - MCP接口包装

        Args:
            gene_symbols: 基因符号列表
            species_set: 物种集合（默认包含常用模式生物）
            include_domain_info: 是否包含结构域信息

        Returns:
            系统发育图谱数据

        Examples:
            # 分析p53家族在脊椎动物中的分布
            build_phylogenetic_profile_tool(["TP53", "TP63", "TP73"], ["human", "mouse", "zebrafish"])
        """
        return await build_phylogenetic_profile(
            gene_symbols, species_set, include_domain_info, _query_executor
        )

    @mcp.tool()
    async def kegg_pathway_enrichment_tool(
        gene_list: list[str],
        organism: str = "hsa",
        pvalue_threshold: float = 0.05,
        min_gene_count: int = 2,
    ) -> dict[str, Any]:
        """
        KEGG通路富集分析工具 - MVP版本

        分析基因列表在KEGG通路中的富集情况，识别显著相关的生物学通路

        Args:
            gene_list: 基因列表（如 ["TP53", "BRCA1", "BRCA2"]）
            organism: 生物体代码（默认 "hsa" 人类）
            pvalue_threshold: p值显著性阈值（默认 0.05）
            min_gene_count: 通路中最小基因数量（默认 2）

        Returns:
            通路富集分析结果，包含：
            - 显著富集的通路列表
            - p值和FDR校正后的统计显著性
            - 富集倍数和基因数量信息
            - 分析参数和元数据

        Examples:
            # 分析癌症相关基因的通路富集
            kegg_pathway_enrichment_tool(["TP53", "BRCA1", "BRCA2", "EGFR"])

            # 分析小鼠基因的通路富集
            kegg_pathway_enrichment_tool(["Trp53", "Brca1"], organism="mmu")

            # 使用更严格的显著性阈值
            kegg_pathway_enrichment_tool(["TP53", "BRCA1"], pvalue_threshold=0.01)
        """
        try:
            # 使用QueryParser解析为通路富集查询
            parsed = QueryParser.parse(gene_list, query_type="pathway_enrichment")

            # 更新参数
            parsed.params.update(
                {
                    "gene_list": gene_list,
                    "organism": organism,
                    "pvalue_threshold": pvalue_threshold,
                    "min_gene_count": min_gene_count,
                }
            )

            # 执行查询
            result = await _query_executor.execute(parsed)

            # 格式化结果
            if "result" in result:
                enrichment_data = result["result"]

                # 添加查询信息
                enrichment_data["query_info"] = {
                    "gene_list": gene_list,
                    "analysis_date": "2025-10-24",
                    "organism": organism,
                    "method": "KEGG Pathway Enrichment",
                    "parameters": {
                        "pvalue_threshold": pvalue_threshold,
                        "min_gene_count": min_gene_count,
                    },
                }

                return enrichment_data
            elif "error" in result:
                return {
                    "error": result["error"],
                    "query_genes": gene_list,
                    "organism": organism,
                    "suggestions": [
                        "检查基因ID格式是否正确",
                        "确认生物体代码是否支持",
                        "验证网络连接是否正常",
                    ],
                }
            else:
                return {
                    "error": "Unknown error occurred during pathway enrichment analysis",
                    "query_genes": gene_list,
                    "organism": organism,
                }

        except Exception as e:
            return {
                "error": f"KEGG pathway enrichment analysis failed: {str(e)}",
                "query_genes": gene_list,
                "organism": organism,
            }
