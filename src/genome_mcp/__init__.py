"""
Genome MCP - 优化版本：智能基因组数据访问

基于Linus Torvalds设计理念的简洁实现：
- 3个智能工具替代原有8个工具
- 自动识别查询意图
- 批量API优化
- 自然语言搜索支持
- 进化生物学数据分析
"""

__version__ = "0.2.5"

# 核心组件导出
from .core import (
    EnsemblClient,
    NCBIClient,
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

# MCP工具导出（主要接口）
# 注意：所有MCP工具通过 FastMCP 框架自动注册


__all__ = [
    # 版本信息
    "__version__",
    # 核心类
    "QueryParser",
    "QueryExecutor",
    "NCBIClient",
    "UniProtClient",
    "EnsemblClient",
    "ParsedQuery",
    "QueryType",
    "_query_executor",
    # 进化分析工具
    "analyze_gene_evolution",
    "build_phylogenetic_profile",
    # 辅助函数
    "_format_simple_result",
    "_apply_filters",
]
