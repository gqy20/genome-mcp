"""
Genome MCP - 优化版本：智能基因组数据访问

基于Linus Torvalds设计理念的简洁实现：
- 3个智能工具替代原有8个工具
- 自动识别查询意图
- 批量API优化
- 自然语言搜索支持
"""

__version__ = "0.2.0"

# 辅助函数导出
# MCP工具导出（主要接口）
# 核心类导出
from .main import (
    NCBIClient,
    ParsedQuery,
    QueryExecutor,
    QueryParser,
    QueryType,
    _apply_filters,
    _format_simple_result,
    _query_executor,
    _understand_query,
    advanced_query,
    get_data,
    smart_search,
)


# 兼容性别名（保持向后兼容）
def get_gene_info(gene_id: str, species: str = "human", include_summary: bool = True):
    """兼容性包装：获取基因信息"""
    import asyncio

    result = asyncio.run(get_data(gene_id, query_type="info", species=species))
    return _format_simple_result(result)


def search_genes(term: str, species: str = "human", max_results: int = 20):
    """兼容性包装：搜索基因"""
    import asyncio

    result = asyncio.run(
        get_data(term, query_type="search", species=species, max_results=max_results)
    )
    return result


def search_by_region(region: str, species: str = "human"):
    """兼容性包装：按区域搜索"""
    import asyncio

    result = asyncio.run(get_data(region, query_type="region", species=species))
    return result


def batch_gene_info(gene_ids: list, species: str = "human"):
    """兼容性包装：批量获取基因信息"""
    import asyncio

    result = asyncio.run(get_data(gene_ids, query_type="batch", species=species))
    return _format_simple_result(result)


def get_gene_homologs(gene_id: str, species: str = "human", target_species: str = None):
    """兼容性包装：获取基因同源体"""
    import asyncio

    # 简化实现：搜索同源体
    search_term = f"{gene_id}[gene] AND homolog"
    if target_species:
        search_term += f" AND {target_species}[organism]"
    result = asyncio.run(get_data(search_term, query_type="search", species=species))
    return result


__all__ = [
    # 版本信息
    "__version__",
    # 核心类
    "QueryParser",
    "QueryExecutor",
    "NCBIClient",
    "ParsedQuery",
    "QueryType",
    "_query_executor",
    # 主要MCP工具
    "get_data",
    "advanced_query",
    "smart_search",
    # 兼容性函数
    "get_gene_info",
    "search_genes",
    "search_by_region",
    "batch_gene_info",
    "get_gene_homologs",
    # 辅助函数
    "_format_simple_result",
    "_understand_query",
    "_apply_filters",
]
