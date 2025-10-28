#!/usr/bin/env python3
"""
类型定义模块 - 关键类型的TypedDict定义

只为核心公共API定义类型，不过度复杂化
"""

try:
    from typing import TypedDict, List, Dict, Any, Optional, Union
except ImportError:
    from typing_extensions import TypedDict
    from typing import List, Dict, Any, Optional, Union


# 基础数据类型
class GeneInfo(TypedDict):
    """基因信息类型"""
    gene_id: str
    gene_symbol: str
    name: str
    description: str
    chromosome: Optional[str]
    start_position: Optional[int]
    end_position: Optional[int]
    strand: Optional[str]


class ProteinInfo(TypedDict):
    """蛋白质信息类型"""
    uniprot_id: str
    accession: str
    name: str
    description: str
    gene_name: Optional[str]
    sequence_length: Optional[int]


class SearchResult(TypedDict):
    """搜索结果类型"""
    query: str
    results: List[Dict[str, Any]]
    total_count: int
    search_metadata: Dict[str, Any]


class BatchResult(TypedDict):
    """批量查询结果类型"""
    batch_size: int
    successful_count: int
    results: Dict[str, Union[GeneInfo, ProteinInfo, Dict[str, Any]]]


class AdvancedQueryResult(TypedDict):
    """高级查询结果类型"""
    strategy: str
    total_queries: int
    successful: int
    results: Dict[int, Dict[str, Any]]


class ErrorResult(TypedDict):
    """错误结果类型"""
    error: str
    error_code: str
    suggestions: List[str]
    query_info: Optional[Dict[str, Any]]


class EvolutionResult(TypedDict):
    """进化分析结果类型"""
    target_gene: str
    orthologs: List[Dict[str, Any]]
    analysis_info: Dict[str, Any]
    conservation_scores: Optional[Dict[str, float]]


class PhylogeneticProfileResult(TypedDict):
    """系统发育图谱结果类型"""
    query_genes: List[str]
    phylogenetic_data: Dict[str, List[Dict[str, Any]]]
    domain_info: Optional[Dict[str, List[Dict[str, Any]]]]
    profile_metadata: Dict[str, Any]


class KEGGResult(TypedDict):
    """KEGG通路富集分析结果类型"""
    query_genes: List[str]
    enriched_pathways: List[Dict[str, Any]]
    analysis_metadata: Dict[str, Any]
    query_info: Dict[str, Any]


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
    target_species: Optional[List[str]]
    analysis_level: str
    include_sequence_info: bool
    pvalue_threshold: float
    min_gene_count: int


# 通用联合类型
GeneQueryResult = Union[GeneInfo, SearchResult, BatchResult, ErrorResult]
ProteinQueryResult = Union[ProteinInfo, SearchResult, BatchResult, ErrorResult]
EvolutionQueryResult = Union[EvolutionResult, ErrorResult]
PhylogeneticQueryResult = Union[PhylogeneticProfileResult, ErrorResult]
KEGGQueryResult = Union[KEGGResult, ErrorResult]

# 工具返回类型
class ToolResult(TypedDict):
    """通用工具返回类型"""
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    metadata: Optional[Dict[str, Any]]


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
    examples: List[str]


class SpeciesCodes(TypedDict):
    """物种代码类型"""
    common_names: List[str]
    taxid_codes: List[str]
    kegg_codes: List[str]


class IDFormats(TypedDict):
    """ID格式类型"""
    gene_identifiers: Dict[str, IDFormatInfo]
    protein_identifiers: Dict[str, IDFormatInfo]
    species_codes: SpeciesCodes