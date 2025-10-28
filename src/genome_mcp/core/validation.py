#!/usr/bin/env python3
"""
参数验证模块 - 简化但有效的参数验证

只验证真正重要的参数，防止滥用和性能问题
"""


class ValidationError(Exception):
    """参数验证错误"""

    pass


def validate_common_params(
    max_results: int = 20, species: str = "human", query_type: str = "auto"
) -> tuple[int, str]:
    """
    验证通用参数

    Args:
        max_results: 最大结果数
        species: 物种
        query_type: 查询类型

    Returns:
        验证后的参数元组

    Raises:
        ValidationError: 参数验证失败
    """
    # 验证max_results
    if not isinstance(max_results, int):
        raise ValidationError("max_results must be an integer")

    if max_results < 1:
        max_results = 1
    elif max_results > 100:
        max_results = 100

    # 验证species
    valid_species = {
        "human": "9606",
        "mouse": "10090",
        "rat": "10116",
        "zebrafish": "7955",
        "fruitfly": "7227",
        "worm": "6239",
        # 直接支持NCBI taxid
        "9606": "9606",
        "10090": "10090",
        "10116": "10116",
        "7955": "7955",
        "7227": "7227",
        "6239": "6239",
    }

    if species not in valid_species:
        # 记录警告但不抛出错误，使用默认值
        species = "human"

    # 验证query_type
    valid_query_types = {
        "auto",
        "info",
        "search",
        "region",
        "protein",
        "gene_protein",
        "ortholog",
        "evolution",
        "batch",
    }

    if query_type not in valid_query_types:
        query_type = "auto"

    return max_results, species, query_type


def validate_gene_params(
    gene_symbol: str,
    target_species: list | None = None,
    analysis_level: str = "Eukaryota",
) -> tuple[str, list | None, str]:
    """
    验证基因分析参数

    Args:
        gene_symbol: 基因符号
        target_species: 目标物种列表
        analysis_level: 分析层级

    Returns:
        验证后的参数元组

    Raises:
        ValidationError: 基因符号验证失败
    """
    if not gene_symbol or not gene_symbol.strip():
        raise ValidationError("Gene symbol cannot be empty")

    gene_symbol = gene_symbol.strip()

    # 验证target_species
    if target_species is not None:
        if not isinstance(target_species, list):
            target_species = [target_species]

        # 过滤有效物种
        valid_species = {"human", "mouse", "rat", "zebrafish", "fruitfly", "worm"}
        target_species = [s for s in target_species if s in valid_species]

        if not target_species:
            target_species = ["human"]

    # 验证analysis_level
    valid_levels = {"Eukaryota", "Metazoa", "Vertebrata", "Mammalia"}
    if analysis_level not in valid_levels:
        analysis_level = "Eukaryota"

    return gene_symbol, target_species, analysis_level


def validate_kegg_params(
    gene_list: list,
    organism: str = "hsa",
    pvalue_threshold: float = 0.05,
    min_gene_count: int = 2,
) -> tuple[list, str, float, int]:
    """
    验证KEGG通路分析参数

    Args:
        gene_list: 基因列表
        organism: 生物体代码
        pvalue_threshold: p值阈值
        min_gene_count: 最小基因数量

    Returns:
        验证后的参数元组

    Raises:
        ValidationError: 基因列表验证失败
    """
    if not gene_list or not isinstance(gene_list, list):
        raise ValidationError("Gene list must be a non-empty list")

    # 过滤有效的基因符号
    valid_genes = []
    for gene in gene_list:
        if isinstance(gene, str) and gene.strip():
            valid_genes.append(gene.strip())

    if not valid_genes:
        raise ValidationError("No valid gene symbols found in the list")

    # 验证organism
    valid_organisms = {"hsa", "mmu", "rno", "dre", "cel", "scf"}
    if organism not in valid_organisms:
        organism = "hsa"

    # 验证pvalue_threshold
    try:
        pvalue_threshold = float(pvalue_threshold)
        if pvalue_threshold <= 0 or pvalue_threshold >= 1:
            pvalue_threshold = 0.05
    except (ValueError, TypeError):
        pvalue_threshold = 0.05

    # 验证min_gene_count
    try:
        min_gene_count = int(min_gene_count)
        if min_gene_count < 1:
            min_gene_count = 1
        elif min_gene_count > 10:
            min_gene_count = 10
    except (ValueError, TypeError):
        min_gene_count = 2

    return valid_genes, organism, pvalue_threshold, min_gene_count


def validate_search_params(
    description: str, context: str = "genomics", max_results: int = 20
) -> tuple[str, str, int]:
    """
    验证搜索参数

    Args:
        description: 搜索描述
        context: 搜索上下文
        max_results: 最大结果数

    Returns:
        验证后的参数元组

    Raises:
        ValidationError: 搜索描述验证失败
    """
    if not description or not description.strip():
        raise ValidationError("Search description cannot be empty")

    description = description.strip()

    # 验证context
    valid_contexts = {"genomics", "proteomics", "pathway"}
    if context not in valid_contexts:
        context = "genomics"

    # 验证max_results
    if not isinstance(max_results, int) or max_results < 1:
        max_results = 20
    elif max_results > 50:
        max_results = 50

    return description, context, max_results
