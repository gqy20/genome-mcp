#!/usr/bin/env python3
"""
数据验证模块 - 提供输入验证和清理功能
"""

from typing import Any


class ValidationError(Exception):
    """验证错误异常"""

    pass


def validate_gene_list(gene_list: list[str]) -> None:
    """
    验证基因列表

    Args:
        gene_list: 基因列表

    Raises:
        ValidationError: 如果基因列表无效
    """
    if not gene_list:
        raise ValidationError("基因列表不能为空")

    # 注释掉强制要求2个基因的限制，允许单基因分析
    # if len(gene_list) == 1:
    #     raise ValidationError("基因列表需要至少包含2个基因进行富集分析")

    for gene in gene_list:
        if not gene or not gene.strip():
            raise ValidationError("基因ID不能为空")
        if not isinstance(gene, str):
            raise ValidationError("基因ID必须是字符串")


def validate_organism(organism: str) -> str:
    """
    验证生物体代码

    Args:
        organism: 生物体代码

    Returns:
        标准化的生物体代码

    Raises:
        ValidationError: 如果生物体代码无效
    """
    if not organism or not organism.strip():
        raise ValidationError("生物体代码不能为空")

    organism = organism.strip().upper()

    # 支持的KEGG生物体代码（简化版）
    valid_organisms = {
        "HSA": "hsa",  # 人类
        "MMU": "mmu",  # 小鼠
        "RNO": "rno",  # 大鼠
        "DME": "dme",  # 果蝇
        "CEL": "cel",  # 线虫
        "SCE": "sce",  # 酵母
    }

    if organism in valid_organisms:
        return valid_organisms[organism]
    elif organism in valid_organisms.values():
        return organism
    else:
        raise ValidationError(f"不支持的生物体代码: {organism}")


def validate_parameters(params: dict[str, Any]) -> dict[str, Any]:
    """
    验证和标准化参数

    Args:
        params: 参数字典

    Returns:
        验证后的参数字典

    Raises:
        ValidationError: 如果参数无效
    """
    validated = {}

    # 验证基因列表
    if "gene_list" not in params:
        raise ValidationError("缺少必需参数: gene_list")

    gene_list = params["gene_list"]
    if isinstance(gene_list, str):
        gene_list = [gene.strip() for gene in gene_list.split(",")]

    validate_gene_list(gene_list)
    validated["gene_list"] = clean_gene_list(gene_list)

    # 验证生物体
    organism = params.get("organism", "hsa")
    validated["organism"] = validate_organism(organism)

    # 验证p值阈值
    pvalue_threshold = params.get("pvalue_threshold", 0.05)
    if not isinstance(pvalue_threshold, int | float) or not (0 < pvalue_threshold <= 1):
        raise ValidationError("pvalue_threshold 必须是0到1之间的数值")
    validated["pvalue_threshold"] = float(pvalue_threshold)

    # 验证最小基因数量
    min_gene_count = params.get("min_gene_count", 2)
    if not isinstance(min_gene_count, int) or min_gene_count < 1:
        raise ValidationError("min_gene_count 必须是大于0的整数")
    validated["min_gene_count"] = int(min_gene_count)

    return validated


def clean_gene_list(gene_list: list[str]) -> list[str]:
    """
    清理基因列表，去除重复和无效项

    Args:
        gene_list: 原始基因列表

    Returns:
        清理后的基因列表
    """
    cleaned = []
    seen = set()

    for gene in gene_list:
        if isinstance(gene, str):
            gene_clean = gene.strip()
            if gene_clean and gene_clean not in seen:
                # 过滤掉明显无效的基因ID
                if (
                    gene_clean
                    and not gene_clean.isspace()
                    and len(gene_clean) >= 2  # 基因ID通常至少2个字符
                    and gene_clean.replace("_", "")
                    .replace("-", "")
                    .isalnum()  # 基因ID通常只包含字母、数字、下划线、连字符
                    and gene_clean.lower()
                    not in ["invalid", "unknown", "test", "dummy"]
                ):  # 过滤常见的测试词汇
                    cleaned.append(gene_clean)
                    seen.add(gene_clean)

    return cleaned
