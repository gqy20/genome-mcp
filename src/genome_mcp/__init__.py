"""
Genome MCP - 优化版本：智能基因组数据访问

基于Linus Torvalds设计理念的简洁实现：
- 3个智能工具替代原有8个工具
- 自动识别查询意图
- 批量API优化
- 自然语言搜索支持
- 进化生物学数据分析
"""

__version__ = "0.2.1"

# 核心组件导出
from .core import (
    NCBIClient,
    OrthoDBClient,
    ParsedQuery,
    QueryExecutor,
    QueryParser,
    QueryType,
    UniProtClient,
    analyze_gene_evolution,
    build_phylogenetic_profile,
)

# 兼容性导出（保持向后兼容）
from .core.tools import _apply_filters, _format_simple_result, _query_executor


# 兼容性别名（保持向后兼容）
def get_gene_info(gene_id: str, species: str = "human", include_summary: bool = True):
    """兼容性包装：获取基因信息"""
    import asyncio

    from .core.query_executor import QueryExecutor

    async def _get_gene_info():
        parser = QueryParser()
        executor = QueryExecutor()
        parsed = parser.parse_query(gene_id, query_type="info", species=species)
        result = await executor.execute_query(parsed)
        return _format_simple_result(result)

    return asyncio.run(_get_gene_info())


def search_genes(term: str, species: str = "human", max_results: int = 20):
    """兼容性包装：搜索基因"""
    import asyncio

    from .core.query_executor import QueryExecutor

    async def _search_genes():
        parser = QueryParser()
        executor = QueryExecutor()
        parsed = parser.parse_query(
            term, query_type="search", species=species, max_results=max_results
        )
        result = await executor.execute_query(parsed)
        return result

    return asyncio.run(_search_genes())


def search_by_region(region: str, species: str = "human"):
    """兼容性包装：按区域搜索"""
    import asyncio

    from .core.query_executor import QueryExecutor

    async def _search_by_region():
        parser = QueryParser()
        executor = QueryExecutor()
        parsed = parser.parse_query(region, query_type="region", species=species)
        result = await executor.execute_query(parsed)
        return result

    return asyncio.run(_search_by_region())


def batch_gene_info(gene_ids: list, species: str = "human"):
    """兼容性包装：批量获取基因信息"""
    import asyncio

    from .core.query_executor import QueryExecutor

    async def _batch_gene_info():
        parser = QueryParser()
        executor = QueryExecutor()
        parsed = parser.parse_query(gene_ids, query_type="batch", species=species)
        result = await executor.execute_query(parsed)
        return _format_simple_result(result)

    return asyncio.run(_batch_gene_info())


def get_gene_homologs(gene_id: str, species: str = "human", target_species: str = None):
    """兼容性包装：获取基因同源体"""
    import asyncio

    from .core.query_executor import QueryExecutor

    async def _get_gene_homologs():
        # 简化实现：搜索同源体
        search_term = f"{gene_id}[gene] AND homolog"
        if target_species:
            search_term += f" AND {target_species}[organism]"

        parser = QueryParser()
        executor = QueryExecutor()
        parsed = parser.parse_query(search_term, query_type="search", species=species)
        result = await executor.execute_query(parsed)
        return result

    return asyncio.run(_get_gene_homologs())


# MCP工具导出（主要接口）
# 注意：get_data 在 core.tools 中是局部函数，需要通过create_mcp_tools使用


__all__ = [
    # 版本信息
    "__version__",
    # 核心类
    "QueryParser",
    "QueryExecutor",
    "NCBIClient",
    "UniProtClient",
    "OrthoDBClient",
    "ParsedQuery",
    "QueryType",
    "_query_executor",
    # 进化分析工具
    "analyze_gene_evolution",
    "build_phylogenetic_profile",
    # 兼容性函数
    "get_gene_info",
    "search_genes",
    "search_by_region",
    "batch_gene_info",
    "get_gene_homologs",
    # 辅助函数
    "_format_simple_result",
    "_apply_filters",
]
