#!/usr/bin/env python3
"""
类型定义模块 - 关键类型的TypedDict定义

只为核心公共API定义类型，不过度复杂化
"""

import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


# 基础数据类型
class GeneInfo(TypedDict):
    """基因信息类型"""

    gene_id: str
    gene_symbol: str
    name: str
    description: str
    chromosome: str | None
    start_position: int | None
    end_position: int | None
    strand: str | None


class ProteinInfo(TypedDict):
    """蛋白质信息类型"""

    uniprot_id: str
    accession: str
    name: str
    description: str
    gene_name: str | None
    sequence_length: int | None


class SearchResult(TypedDict):
    """搜索结果类型"""

    query: str
    results: list[dict[str, Any]]
    total_count: int
    search_metadata: dict[str, Any]


class BatchResult(TypedDict):
    """批量查询结果类型"""

    batch_size: int
    successful_count: int
    results: dict[str, GeneInfo | ProteinInfo | dict[str, Any]]


class AdvancedQueryResult(TypedDict):
    """高级查询结果类型"""

    strategy: str
    total_queries: int
    successful: int
    results: dict[int, dict[str, Any]]


class ErrorResult(TypedDict):
    """错误结果类型"""

    error: str
    error_code: str
    suggestions: list[str]
    query_info: dict[str, Any] | None


class EvolutionResult(TypedDict):
    """进化分析结果类型"""

    target_gene: str
    orthologs: list[dict[str, Any]]
    analysis_info: dict[str, Any]
    conservation_scores: dict[str, float] | None


class PhylogeneticProfileResult(TypedDict):
    """系统发育图谱结果类型"""

    query_genes: list[str]
    phylogenetic_data: dict[str, list[dict[str, Any]]]
    domain_info: dict[str, list[dict[str, Any]]] | None
    profile_metadata: dict[str, Any]


class KEGGResult(TypedDict):
    """KEGG通路富集分析结果类型"""

    query_genes: list[str]
    enriched_pathways: list[dict[str, Any]]
    analysis_metadata: dict[str, Any]
    query_info: dict[str, Any]


# 参数类型
class QueryParams(TypedDict, total=False):
    """查询参数类型"""

    query: str
    query_type: str
    data_type: str
    format: str
    species: str
    max_results: int
    organism: str


class AnalysisParams(TypedDict, total=False):
    """分析参数类型"""

    target_species: list[str] | None
    analysis_level: str
    include_sequence_info: bool
    pvalue_threshold: float
    min_gene_count: int


# 通用联合类型
GeneQueryResult = GeneInfo | SearchResult | BatchResult | ErrorResult
ProteinQueryResult = ProteinInfo | SearchResult | BatchResult | ErrorResult
EvolutionQueryResult = EvolutionResult | ErrorResult
PhylogeneticQueryResult = PhylogeneticProfileResult | ErrorResult
KEGGQueryResult = KEGGResult | ErrorResult


# 工具返回类型
class ToolResult(TypedDict):
    """通用工具返回类型"""

    success: bool
    data: dict[str, Any] | None
    error: str | None
    metadata: dict[str, Any] | None


# 数据源类型
class DataSourceInfo(TypedDict):
    """数据源信息类型"""

    name: str
    status: str
    description: str
    last_checked: str


class DatabaseStatus(TypedDict):
    """数据库状态类型"""

    ncbi_gene: DataSourceInfo
    uniprot: DataSourceInfo
    ensembl: DataSourceInfo
    kegg: DataSourceInfo


# ID格式信息类型
class IDFormatInfo(TypedDict):
    """ID格式信息类型"""

    format: str
    description: str
    examples: list[str]


class SpeciesCodes(TypedDict):
    """物种代码类型"""

    common_names: list[str]
    taxid_codes: list[str]
    kegg_codes: list[str]


class IDFormats(TypedDict):
    """ID格式类型"""

    gene_identifiers: dict[str, IDFormatInfo]
    protein_identifiers: dict[str, IDFormatInfo]
    species_codes: SpeciesCodes
