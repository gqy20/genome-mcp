#!/usr/bin/env python3
"""
查询解析器模块 - 智能识别查询意图

支持自动识别和手动指定查询类型
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class QueryType(Enum):
    """查询类型枚举"""

    INFO = "info"  # 基因信息查询
    SEARCH = "search"  # 关键词搜索
    REGION = "region"  # 基因组区域搜索
    BATCH = "batch"  # 批量查询
    PROTEIN = "protein"  # 蛋白质信息查询
    GENE_PROTEIN = "gene_protein"  # 基因-蛋白质整合查询
    ORTHOLOG = "ortholog"  # 同源基因查询
    EVOLUTION = "evolution"  # 进化分析查询
    PATHWAY_ENRICHMENT = "pathway_enrichment"  # 通路富集分析
    UNKNOWN = "unknown"  # 未知类型


@dataclass
class ParsedQuery:
    """解析后的查询对象"""

    type: QueryType
    query: str
    params: dict[str, Any]
    is_batch: bool = False


class QueryParser:
    """智能查询解析器 - 自动识别查询意图"""

    @staticmethod
    def parse(query: str | list[str], query_type: str = "auto") -> ParsedQuery:
        """解析查询意图"""

        # 处理批量查询 - 但是对于特殊查询类型，需要特殊处理
        if isinstance(query, list):
            # 对于通路富集分析，将列表转换为字符串
            if query_type == "pathway_enrichment":
                query_str = ",".join(str(item) for item in query)
                return QueryParser._parse_pathway_enrichment(query_str)
            else:
                return QueryParser._parse_batch(query)

        query = str(query).strip()

        # 指定类型查询
        if query_type != "auto":
            return QueryParser._parse_by_type(query, query_type)

        # 自动识别查询类型
        return QueryParser._parse_auto(query)

    @staticmethod
    def _parse_batch(gene_ids: list[str]) -> ParsedQuery:
        """解析批量查询"""
        return ParsedQuery(
            type=QueryType.BATCH,
            query=",".join(gene_ids),
            params={"gene_ids": gene_ids},
            is_batch=True,
        )

    @staticmethod
    def _parse_by_type(query: str, query_type: str) -> ParsedQuery:
        """按指定类型解析"""
        if query_type == "info":
            return QueryParser._parse_gene_info(query)
        elif query_type == "region":
            return QueryParser._parse_region(query)
        elif query_type == "search":
            return QueryParser._parse_search(query)
        elif query_type == "batch":
            return QueryParser._parse_batch([query])
        elif query_type == "protein":
            return QueryParser._parse_protein(query)
        elif query_type == "gene_protein":
            return QueryParser._parse_gene_protein(query)
        elif query_type == "ortholog":
            return QueryParser._parse_ortholog(query)
        elif query_type == "evolution":
            return QueryParser._parse_evolution(query)
        elif query_type == "pathway_enrichment":
            return QueryParser._parse_pathway_enrichment(query)
        else:
            return QueryParser._parse_auto(query)

    @staticmethod
    def _parse_auto(query: str) -> ParsedQuery:
        """自动识别查询类型"""

        # UniProt 访问号模式 (如 P04637)
        if re.match(r"^[A-Z0-9]{6,10}$", query) and not re.match(
            r"^[A-Z]{2,}\d+$", query
        ):
            return QueryParser._parse_protein(query)

        # 基因ID模式
        if re.match(r"^[A-Z]{2,}\d+$", query):
            return QueryParser._parse_gene_info(query)

        # 区域格式
        if re.match(r"^(?:chr)?[XY\d]+[:\[]\d+-\d+", query.replace(" ", "")):
            return QueryParser._parse_region(query)

        # 批量ID格式
        if "," in query and all(
            re.match(r"^[A-Z]{2,}\d+$", id.strip()) for id in query.split(",")
        ):
            return QueryParser._parse_batch([id.strip() for id in query.split(",")])

        # 通路富集分析关键词检测
        pathway_keywords = [
            "pathway",
            "enrichment",
            "kegg",
            "pathway analysis",
            "functional analysis",
            "go enrichment",
            "pathway enrichment",
        ]

        # 进化生物学关键词检测
        ortholog_keywords = ["homolog", "ortholog", "paralog", "across species"]
        evolution_keywords = [
            "conservation",
            "phylogen",
            "evolution",
            "comparative",
            "species",
            "conserved",
            "family",
            "ancestral",
        ]

        if any(keyword in query.lower() for keyword in pathway_keywords):
            return QueryParser._parse_pathway_enrichment(query)
        elif any(keyword in query.lower() for keyword in ortholog_keywords):
            return QueryParser._parse_ortholog(query)
        elif any(keyword in query.lower() for keyword in evolution_keywords):
            return QueryParser._parse_evolution(query)

        # 蛋白质相关关键词检测
        protein_keywords = [
            "protein",
            "sequence",
            "domain",
            "enzyme",
            "kinase",
            "receptor",
        ]
        if any(keyword in query.lower() for keyword in protein_keywords):
            return QueryParser._parse_protein(query)

        # 默认为搜索
        return QueryParser._parse_search(query)

    @staticmethod
    def _parse_gene_info(query: str) -> ParsedQuery:
        """解析基因信息查询"""
        gene_id = query.strip()
        return ParsedQuery(
            type=QueryType.INFO, query=gene_id, params={"gene_id": gene_id}
        )

    @staticmethod
    def _parse_search(query: str) -> ParsedQuery:
        """解析搜索查询"""
        return ParsedQuery(
            type=QueryType.SEARCH,
            query=query,
            params={"term": query, "max_results": 20},
        )

    @staticmethod
    def _parse_region(query: str) -> ParsedQuery:
        """解析区域查询"""
        # 标准化区域格式
        query = query.replace(" ", "")

        patterns = [
            r"(?:chr)?(\d+|[XY]):(\d+)-(\d+)",
            r"(?:chr)?(\d+|[XY])\[(\d+)-(\d+)\]",
        ]

        for pattern in patterns:
            match = re.match(pattern, query)
            if match:
                chromosome, start, end = match.groups()
                chromosome = (
                    f"chr{chromosome}"
                    if not chromosome.startswith("chr")
                    else chromosome
                )
                return ParsedQuery(
                    type=QueryType.REGION,
                    query=f"{chromosome}:{start}-{end}",
                    params={
                        "chromosome": chromosome,
                        "start": int(start),
                        "end": int(end),
                    },
                )

        raise ValueError(f"Invalid region format: {query}")

    @staticmethod
    def _parse_protein(query: str) -> ParsedQuery:
        """解析蛋白质查询"""
        return ParsedQuery(
            type=QueryType.PROTEIN,
            query=query,
            params={
                "protein_query": query,
                "max_results": 20,
                "organism": "9606",  # Default to human
            },
        )

    @staticmethod
    def _parse_gene_protein(query: str) -> ParsedQuery:
        """解析基因-蛋白质整合查询"""
        return ParsedQuery(
            type=QueryType.GENE_PROTEIN,
            query=query,
            params={
                "gene_query": query,
                "max_results": 20,
                "organism": "9606",  # Default to human
            },
        )

    @staticmethod
    def _extract_gene_symbol_from_query(query: str) -> str:
        """从查询中提取基因符号"""
        import re

        # 移除常见的查询词汇
        cleaned_query = query.lower()
        for word in [
            "homolog",
            "homologs",
            "ortholog",
            "orthologs",
            "evolution",
            "conservation",
            "across",
            "species",
        ]:
            cleaned_query = cleaned_query.replace(word, " ")

        # 查找可能的基因符号（通常是大写字母加数字）
        words = cleaned_query.split()
        for word in words:
            word = word.upper().strip()
            # 基因符号模式：大写字母开头，可能包含数字
            if re.match(r"^[A-Z][A-Z0-9]*$", word) and len(word) >= 2:
                return word

        # 如果没有找到，返回原始查询的第一个词
        return query.split()[0].upper() if query.split() else query

    @staticmethod
    def _parse_ortholog(query: str) -> ParsedQuery:
        """解析同源基因查询"""
        # 从查询中提取基因符号
        gene_symbol = QueryParser._extract_gene_symbol_from_query(query)

        return ParsedQuery(
            type=QueryType.ORTHOLOG,
            query=query,
            params={"gene_query": gene_symbol, "limit": 50, "target_species": None},
        )

    @staticmethod
    def _parse_evolution(query: str) -> ParsedQuery:
        """解析进化分析查询"""
        return ParsedQuery(
            type=QueryType.EVOLUTION,
            query=query,
            params={"evolution_query": query, "analysis_type": "comprehensive"},
        )

    @staticmethod
    def _parse_pathway_enrichment(query: str) -> ParsedQuery:
        """解析通路富集分析查询"""
        # 将查询字符串解析为基因列表
        gene_list = [gene.strip() for gene in query.split(",") if gene.strip()]

        return ParsedQuery(
            type=QueryType.PATHWAY_ENRICHMENT,
            query=query,
            params={
                "pathway_query": query,
                "gene_list": gene_list,  # 添加解析后的基因列表
                "organism": "hsa",  # 默认人类
                "pvalue_threshold": 0.05,
                "min_gene_count": 2,  # 添加默认最小基因数量
            },
        )

    @staticmethod
    def parse_by_type(query: str, query_type: str) -> ParsedQuery:
        """兼容性方法：按指定类型解析"""
        return QueryParser._parse_by_type(query, query_type)
