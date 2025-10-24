#!/usr/bin/env python3
"""
基础统计工具 - MVP版本
提供生物学分析所需的基础统计计算
"""

import math
from typing import Any


def hypergeometric_test(k: int, K: int, n: int, N: int) -> float:
    """
    超几何分布检验

    Args:
        k: 查询集合中成功元素的数量
        K: 总体中成功元素的总数
        n: 查询集合的大小
        N: 总体的大小

    Returns:
        p-value

    Example:
        # 计算富集显著性
        p = hypergeometric_test(k=5, K=20, n=100, N=20000)
    """
    if k > K or k > n or K > N or n > N:
        return 1.0

    if k == 0:
        return 1.0

    try:
        # 计算超几何分布的概率质量函数
        # P(X = k) = C(K, k) * C(N-K, n-k) / C(N, n)

        # 使用对数防止数值溢出
        log_p = (
            math.log(math.comb(K, k))
            + math.log(math.comb(N - K, n - k))
            - math.log(math.comb(N, n))
        )

        p_exact = math.exp(log_p)

        # 计算累积概率 P(X >= k)
        p_cumulative = 0.0
        for i in range(k, min(K, n) + 1):
            if i > 0:
                try:
                    log_pi = (
                        math.log(math.comb(K, i))
                        + math.log(math.comb(N - K, n - i))
                        - math.log(math.comb(N, n))
                    )
                    p_cumulative += math.exp(log_pi)
                except (ValueError, OverflowError):
                    # 数值溢出时跳过
                    continue
            else:
                p_cumulative += p_exact

        return min(p_cumulative, 1.0)

    except (ValueError, OverflowError, ZeroDivisionError):
        # 数值计算错误时返回保守值
        return 1.0


def benjamini_hochberg_fdr(
    results: list[dict[str, Any]], alpha: float = 0.05
) -> list[dict[str, Any]]:
    """
    Benjamini-Hochberg FDR校正

    Args:
        results: 包含p值的分析结果列表
        alpha: 显著性水平阈值

    Returns:
        包含校正后p值的结果列表

    Example:
        results = [{"pvalue": 0.01}, {"pvalue": 0.05}]
        corrected = benjamini_hochberg_fdr(results)
    """
    if not results:
        return results

    # 按p值排序
    sorted_results = sorted(results, key=lambda x: x.get("pvalue", 1.0))
    m = len(sorted_results)

    # 应用Benjamini-Hochberg校正
    for i, result in enumerate(sorted_results):
        p_value = result.get("pvalue", 1.0)
        # FDR = p_value * m / (i + 1)
        fdr = p_value * m / (i + 1)
        result["fdr"] = min(fdr, 1.0)

        # 添加显著性标记
        result["significant"] = result["fdr"] < alpha

    return sorted_results


def calculate_fold_enrichment(
    query_count: int, query_total: int, pathway_count: int, background_total: int
) -> float:
    """
    计算富集倍数

    Args:
        query_count: 查询基因中属于通路的基因数
        query_total: 查询基因总数
        pathway_count: 背景中通路的基因总数
        background_total: 背景基因总数

    Returns:
        富集倍数
    """
    try:
        # (query_count/query_total) / (pathway_count/background_total)
        observed_ratio = query_count / query_total
        expected_ratio = pathway_count / background_total

        if expected_ratio == 0:
            return float("inf") if observed_ratio > 0 else 0.0

        return observed_ratio / expected_ratio
    except ZeroDivisionError:
        return 0.0


def filter_significant_results(
    results: list[dict[str, Any]], fdr_threshold: float = 0.05, min_gene_count: int = 2
) -> list[dict[str, Any]]:
    """
    过滤显著的结果

    Args:
        results: 分析结果列表
        fdr_threshold: FDR阈值
        min_gene_count: 最小基因数量

    Returns:
        过滤后的结果列表
    """
    filtered = []

    for result in results:
        # 检查FDR显著性
        if result.get("fdr", 1.0) > fdr_threshold:
            continue

        # 检查基因数量
        gene_count = result.get("gene_count", len(result.get("genes", [])))
        if gene_count < min_gene_count:
            continue

        filtered.append(result)

    return filtered
