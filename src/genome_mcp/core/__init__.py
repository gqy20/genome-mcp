#!/usr/bin/env python3
"""
核心模块 - 包含所有核心组件

提供客户端、查询解析器、执行器和工具函数
"""

from .clients import NCBIClient, UniProtClient
from .ensembl_client import EnsemblClient
from .evolution_tools import analyze_gene_evolution, build_phylogenetic_profile
from .query_executor import QueryExecutor
from .query_parser import ParsedQuery, QueryParser, QueryType

__all__ = [
    # 客户端
    "NCBIClient",
    "UniProtClient",
    "EnsemblClient",
    # 查询相关
    "QueryParser",
    "QueryType",
    "ParsedQuery",
    "QueryExecutor",
    # 进化分析工具
    "analyze_gene_evolution",
    "build_phylogenetic_profile",
]
