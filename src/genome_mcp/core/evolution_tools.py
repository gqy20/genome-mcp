#!/usr/bin/env python3
"""
进化分析专用工具模块

提供高级进化生物学分析功能
"""

from typing import Any

from .query_executor import QueryExecutor
from .query_parser import QueryParser


def _generate_evolutionary_insights(result: dict[str, Any]) -> dict[str, Any]:
    """生成进化洞察"""
    insights = {
        "conservation_level": "unknown",
        "evolutionary_rate": "unknown",
        "functional_constraints": [],
    }

    # 基于同源基因数量评估保守性
    orthologs_data = result.get("result", {}).get("orthologs", [])
    orthologs_count = len(orthologs_data)

    if orthologs_count > 100:
        insights["conservation_level"] = "highly_conserved"
        insights["functional_constraints"].append("Strong purifying selection")
    elif orthologs_count > 20:
        insights["conservation_level"] = "moderately_conserved"
        insights["functional_constraints"].append("Moderate functional constraints")
    else:
        insights["conservation_level"] = "lineage_specific"
        insights["functional_constraints"].append(
            "Potential lineage-specific adaptation"
        )

    return insights


def _calculate_conservation_score(result: dict[str, Any]) -> float:
    """计算保守性评分"""
    orthologs_data = result.get("result", {}).get("orthologs", [])

    # 基于物种分布计算保守性评分
    species_count = len(
        {ortholog.get("organism_name", "") for ortholog in orthologs_data}
    )

    # 归一化评分 (0-1)
    if species_count > 50:
        return 1.0
    elif species_count > 20:
        return 0.8
    elif species_count > 10:
        return 0.6
    elif species_count > 5:
        return 0.4
    else:
        return 0.2


def _analyze_phylogenetic_distribution(result: dict[str, Any]) -> dict[str, Any]:
    """分析系统发育分布"""
    orthologs_data = result.get("result", {}).get("orthologs", [])

    distribution = {}
    for ortholog in orthologs_data:
        organism = ortholog.get("organism_name", "Unknown")
        distribution[organism] = distribution.get(organism, 0) + 1

    # 统计主要类群
    major_groups = {
        "mammals": 0,
        "birds": 0,
        "reptiles": 0,
        "fish": 0,
        "invertebrates": 0,
        "plants": 0,
        "fungi": 0,
    }

    for organism in distribution.keys():
        organism_lower = organism.lower()
        if any(
            mammal in organism_lower
            for mammal in ["mammal", "human", "mouse", "rat", "dog", "cat"]
        ):
            major_groups["mammals"] += 1
        elif "fish" in organism_lower or "zebrafish" in organism_lower:
            major_groups["fish"] += 1
        elif "fly" in organism_lower or "insect" in organism_lower:
            major_groups["invertebrates"] += 1
        elif "plant" in organism_lower or "arabidopsis" in organism_lower:
            major_groups["plants"] += 1
        elif "yeast" in organism_lower or "fungi" in organism_lower:
            major_groups["fungi"] += 1

    return {
        "species_distribution": distribution,
        "major_group_counts": major_groups,
        "total_species": len(distribution),
    }


def _build_presence_absence_matrix(
    results: dict, species_set: list[str]
) -> dict[str, dict]:
    """构建存在/缺失矩阵"""
    matrix = {}

    for gene_symbol, gene_result in results.items():
        gene_row = {}
        orthologs_data = gene_result.get("result", {}).get("orthologs", [])
        present_species = set()

        # 标准化物种名称
        for ortholog in orthologs_data:
            organism_name = ortholog.get("organism_name", "").lower()
            # 标准化物种名称（移除下划线，转换为小写）
            normalized_name = organism_name.replace("_", " ")
            present_species.add(normalized_name)

        for species in species_set:
            species_lower = species.lower()
            # 检查各种可能的物种名称格式
            species_variants = [
                species_lower,
                species_lower.replace(" ", "_"),
                species_lower.replace(" ", ""),
            ]

            gene_row[species] = any(
                variant in present_species
                or any(variant in present for present in present_species)
                for variant in species_variants
            )

        matrix[gene_symbol] = gene_row

    return matrix


def _analyze_gene_family_evolution(
    results: dict, species_set: list[str]
) -> dict[str, Any]:
    """分析基因家族进化"""
    # 计算基因保守性
    conservation_scores = {}
    for gene_symbol, gene_result in results.items():
        conservation_scores[gene_symbol] = _calculate_conservation_score(gene_result)

    # 识别保守性模式
    most_conserved = max(conservation_scores.items(), key=lambda x: x[1])
    least_conserved = min(conservation_scores.items(), key=lambda x: x[1])

    return {
        "conservation_scores": conservation_scores,
        "most_conserved_gene": most_conserved[0],
        "least_conserved_gene": least_conserved[0],
        "conservation_range": most_conserved[1] - least_conserved[1],
    }


def _identify_conservation_patterns(matrix: dict[str, dict]) -> list[str]:
    """识别保守性模式"""
    patterns = []

    # 分析基因存在模式
    for gene_symbol, species_data in matrix.items():
        presence_count = sum(species_data.values())
        total_species = len(species_data)

        if presence_count == total_species:
            patterns.append(f"{gene_symbol}: Universally conserved")
        elif presence_count > total_species * 0.8:
            patterns.append(f"{gene_symbol}: Highly conserved")
        elif presence_count > total_species * 0.5:
            patterns.append(f"{gene_symbol}: Moderately conserved")
        else:
            patterns.append(f"{gene_symbol}: Lineage-specific")

    return patterns


async def analyze_gene_evolution(
    gene_symbol: str,
    target_species: list[str] = None,
    analysis_level: str = "Eukaryota",
    include_sequence_info: bool = True,
    query_executor: QueryExecutor = None,
) -> dict[str, Any]:
    """
    基因进化分析 - 分析基因在跨物种间的进化关系

    功能包括：
    - 同源基因识别和检索
    - 系统发育关系分析
    - 物种分布统计
    - 进化保守性评估

    Args:
        gene_symbol: 基因符号（如 TP53, BRCA1）
        target_species: 目标物种列表（如 ["mouse", "rat", "zebrafish"]）
        analysis_level: 分析层级（如 Eukaryota, Metazoa, Vertebrata）
        include_sequence_info: 是否包含序列信息
        query_executor: 查询执行器实例

    Returns:
        进化分析结果，包含同源基因信息、系统发育数据和统计信息

    Examples:
        # 分析 TP53 在哺乳动物中的进化
        analyze_gene_evolution("TP53", ["human", "mouse", "rat", "dog"])

        # 分析基因在所有真核生物中的进化
        analyze_gene_evolution("BRCA1", analysis_level="Eukaryota")
    """
    if query_executor is None:
        query_executor = QueryExecutor()

    try:
        # 验证输入参数
        if not gene_symbol or not gene_symbol.strip():
            return {
                "error": "基因符号不能为空",
                "gene_symbol": gene_symbol,
                "error_type": "validation_error",
                "suggestions": ["提供有效的基因符号，如 TP53, BRCA1"],
            }

        gene_symbol = gene_symbol.strip()

        # 构建查询
        if target_species:
            query = f"{gene_symbol} across species {' '.join(target_species)}"
        else:
            query = f"{gene_symbol} evolution conservation"

        # 执行同源基因查询
        parsed = QueryParser._parse_ortholog(query)
        if target_species:
            parsed.params["target_species"] = target_species
        parsed.params["gene_symbol"] = gene_symbol

        result = await query_executor.execute(parsed)

        # 检查查询结果
        if not result.get("success") and result.get("error"):
            return {
                "error": f"同源基因查询失败: {result.get('error', '未知错误')}",
                "gene_symbol": gene_symbol,
                "status": "service_unavailable",
                "message": "Ensembl API服务暂时不可用，无法进行同源基因分析",
                "suggestions": [
                    "稍后重试",
                    "检查网络连接",
                    "确认基因符号正确",
                    "尝试使用其他基因符号（如大写格式）",
                ],
                "alternative_resources": [
                    {
                        "name": "Ensembl Web界面",
                        "url": f"https://www.ensembl.org/Homo_sapiens/Search?q={gene_symbol}",
                        "description": "在Ensembl网站手动搜索基因",
                    },
                    {
                        "name": "NCBI Gene",
                        "url": f"https://www.ncbi.nlm.nih.gov/gene?term={gene_symbol}",
                        "description": "NCBI基因数据库",
                    },
                ],
                "debug_info": {
                    "parsed_query": query,
                    "query_params": parsed.params,
                    "original_error": result.get("error"),
                },
            }

        # 检查是否有同源基因数据
        orthologs = result.get("result", {}).get("orthologs", [])
        if not orthologs:
            return {
                "error": f"未找到基因 '{gene_symbol}' 的同源基因",
                "gene_symbol": gene_symbol,
                "status": "no_orthologs_found",
                "message": "该基因可能不存在于Ensembl数据库中，或者没有同源基因记录",
                "suggestions": [
                    "检查基因符号拼写是否正确",
                    "尝试使用该基因的其他名称或别名",
                    "确认该基因在参考基因组中存在",
                ],
                "query_result": result,
            }

        # 添加进化分析信息
        evolution_analysis = {
            "gene_symbol": gene_symbol,
            "analysis_level": analysis_level,
            "target_species": target_species,
            "include_sequence_info": include_sequence_info,
            "evolutionary_insights": _generate_evolutionary_insights(result),
            "conservation_score": _calculate_conservation_score(result),
            "phylogenetic_distribution": _analyze_phylogenetic_distribution(result),
            "data_quality": {
                "orthologs_count": len(orthologs),
                "species_count": len({o.get("organism_name") for o in orthologs}),
                "high_confidence_count": len(
                    [o for o in orthologs if o.get("confidence") == "high"]
                ),
            },
        }

        result["evolution_analysis"] = evolution_analysis
        result["success"] = True  # 明确标记成功

        return result

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()

        return {
            "error": f"基因进化分析异常: {str(e)}",
            "gene_symbol": gene_symbol,
            "error_type": "gene_evolution_error",
            "suggestions": [
                "检查基因符号是否正确",
                "确认网络连接正常",
                "稍后重试",
                "联系技术支持",
            ],
            "troubleshooting": {
                "target_species": target_species,
                "analysis_level": analysis_level,
                "possible_causes": [
                    "基因符号不存在",
                    "Ensembl API不可用",
                    "网络连接问题",
                    "服务器内部错误",
                ],
                "error_trace": error_trace,
            },
        }


async def build_phylogenetic_profile(
    gene_symbols: list[str],
    species_set: list[str] = None,
    include_domain_info: bool = True,
    query_executor: QueryExecutor = None,
) -> dict[str, Any]:
    """
    构建系统发育图谱 - 分析多个基因在指定物种集合中的分布

    用于研究：
    - 基因家族进化
    - 物种特异性基因丢失
    - 功能保守性分析
    - 比较基因组学研究

    Args:
        gene_symbols: 基因符号列表
        species_set: 物种集合（默认包含常用模式生物）
        include_domain_info: 是否包含结构域信息
        query_executor: 查询执行器实例

    Returns:
        系统发育图谱数据，包含存在/缺失矩阵和进化分析

    Examples:
        # 分析p53家族在脊椎动物中的分布
        build_phylogenetic_profile(["TP53", "TP63", "TP73"], ["human", "mouse", "zebrafish"])
    """
    if query_executor is None:
        query_executor = QueryExecutor()

    if species_set is None:
        species_set = [
            "human",
            "mouse",
            "rat",
            "zebrafish",
            "fruitfly",
            "worm",
            "yeast",
        ]

    try:
        # 批量分析基因
        results = {}
        service_unavailable_count = 0

        for gene_symbol in gene_symbols:
            # 分析每个基因的同源关系
            gene_result = await analyze_gene_evolution(
                gene_symbol,
                species_set,
                include_sequence_info=include_domain_info,
                query_executor=query_executor,
            )

            # 检查服务状态
            if (
                gene_result.get("error")
                and gene_result.get("status") == "service_unavailable"
            ):
                service_unavailable_count += 1

            results[gene_symbol] = gene_result

        # 如果所有基因都查询失败，返回服务不可用
        if service_unavailable_count == len(gene_symbols):
            return {
                "error": "系统发育分析服务不可用",
                "gene_symbols": gene_symbols,
                "status": "service_unavailable",
                "message": "Ensembl API服务不可用，无法构建系统发育图谱",
                "suggestions": ["稍后重试", "检查网络连接", "确认基因符号正确"],
                "alternative_resources": [
                    {
                        "name": "Ensembl Web界面",
                        "url": "https://www.ensembl.org/Homo_sapiens/Search",
                        "description": "在Ensembl网站手动搜索基因",
                    },
                    {
                        "name": "NCBI Gene",
                        "url": "https://www.ncbi.nlm.nih.gov/gene",
                        "description": "NCBI基因数据库",
                    },
                ],
            }

        # 构建存在/缺失矩阵
        presence_matrix = _build_presence_absence_matrix(results, species_set)

        # 分析基因家族进化
        family_analysis = _analyze_gene_family_evolution(results, species_set)

        return {
            "gene_symbols": gene_symbols,
            "species_set": species_set,
            "presence_matrix": presence_matrix,
            "family_analysis": family_analysis,
            "individual_results": results,
            "summary": {
                "total_genes": len(gene_symbols),
                "total_species": len(species_set),
                "successful_queries": len(gene_symbols) - service_unavailable_count,
                "failed_queries": service_unavailable_count,
                "conservation_patterns": _identify_conservation_patterns(
                    presence_matrix
                ),
            },
        }

    except Exception as e:
        return {
            "error": str(e),
            "gene_symbols": gene_symbols,
            "error_type": "phylogenetic_profile_error",
            "suggestions": [
                "检查基因符号列表是否正确",
                "确认物种列表格式正确",
                "减少基因数量后重试",
            ],
            "troubleshooting": {
                "gene_count": len(gene_symbols),
                "species_count": len(species_set) if species_set else 0,
                "possible_causes": [
                    "某些基因符号不存在",
                    "网络连接问题",
                    "Ensembl API限制",
                ],
            },
        }
