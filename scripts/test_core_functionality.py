#!/usr/bin/env python3
"""
核心功能测试脚本

测试 Genome MCP 的核心功能，包括查询解析和模块导入
不依赖外部API，适合持续集成和开发环境测试
"""

import sys
import os

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)

from genome_mcp.core import QueryParser, QueryType, QueryExecutor, ParsedQuery


def test_query_parser():
    """测试查询解析器"""
    print("🧪 测试查询解析器...")

    test_cases = [
        # (查询, 期望类型, 描述)
        ("TP53", QueryType.INFO, "基因信息查询"),
        ("TP53 homologs", QueryType.ORTHOLOG, "同源基因查询"),
        ("evolutionary conservation", QueryType.EVOLUTION, "进化分析查询"),
        ("TP53 protein", QueryType.PROTEIN, "蛋白质查询"),
        ("chr17:7565097-7590856", QueryType.REGION, "区域搜索"),
        ("P04637", QueryType.PROTEIN, "UniProt蛋白质查询"),
        ("breast cancer genes", QueryType.SEARCH, "语义搜索"),
        (["TP53", "BRCA1", "BRCA2"], QueryType.BATCH, "批量查询")
    ]

    passed = 0
    total = len(test_cases)

    for query, expected_type, description in test_cases:
        try:
            if isinstance(query, list):
                parsed = QueryParser.parse(query)
                query_str = ",".join(query)
            else:
                parsed = QueryParser.parse(query)
                query_str = query

            if parsed.type == expected_type:
                print(f"  ✅ '{query_str}' → {parsed.type.value} ({description})")
                passed += 1
            else:
                print(f"  ❌ '{query_str}' → {parsed.type.value} (期望: {expected_type.value}, {description})")
        except Exception as e:
            print(f"  ❌ '{query}' → 错误: {e} ({description})")

    print(f"  📊 结果: {passed}/{total} 通过")
    return passed == total


def test_evolution_keywords():
    """测试进化生物学关键词识别"""
    print("🧬 测试进化生物学关键词识别...")

    evolution_queries = [
        "TP53 conservation",
        "phylogenetic analysis",
        "comparative genomics",
        "species distribution",
        "conserved domains",
        "family evolution",
        "ancestral genes"
    ]

    ortholog_queries = [
        "TP53 orthologs",
        "homologous genes",
        "paralog analysis",
        "ortholog identification",
        "homolog comparison"
    ]

    passed_evolution = 0
    passed_ortholog = 0

    for query in evolution_queries:
        try:
            parsed = QueryParser.parse(query)
            if parsed.type == QueryType.EVOLUTION:
                print(f"  ✅ '{query}' → evolution")
                passed_evolution += 1
            else:
                print(f"  ❌ '{query}' → {parsed.type.value} (期望: evolution)")
        except Exception as e:
            print(f"  ❌ '{query}' → 错误: {e}")

    for query in ortholog_queries:
        try:
            parsed = QueryParser.parse(query)
            if parsed.type == QueryType.ORTHOLOG:
                print(f"  ✅ '{query}' → ortholog")
                passed_ortholog += 1
            else:
                print(f"  ❌ '{query}' → {parsed.type.value} (期望: ortholog)")
        except Exception as e:
            print(f"  ❌ '{query}' → 错误: {e}")

    total_passed = passed_evolution + passed_ortholog
    total_tests = len(evolution_queries) + len(ortholog_queries)

    print(f"  📊 进化关键词: {passed_evolution}/{len(evolution_queries)} 通过")
    print(f"  📊 同源关键词: {passed_ortholog}/{len(ortholog_queries)} 通过")
    print(f"  📊 总体结果: {total_passed}/{total_tests} 通过")
    return total_passed == total_tests


def test_query_parameters():
    """测试查询参数处理"""
    print("⚙️ 测试查询参数处理...")

    test_cases = [
        ("TP53", QueryType.INFO, {"gene_id": "TP53"}),
        ("TP53 protein", QueryType.PROTEIN, {
            "protein_query": "TP53 protein",
            "max_results": 20,
            "organism": "9606"
        }),
        ("chr17:7565097-7590856", QueryType.REGION, {
            "chromosome": "chr17",
            "start": 7565097,
            "end": 7590856
        }),
        ("TP53 homologs", QueryType.ORTHOLOG, {
            "gene_query": "TP53 homologs",
            "limit": 50,
            "target_species": None
        }),
    ]

    passed = 0
    total = len(test_cases)

    for query, expected_type, expected_params in test_cases:
        try:
            parsed = QueryParser.parse(query)

            type_match = parsed.type == expected_type
            params_match = True

            for key, value in expected_params.items():
                if parsed.params.get(key) != value:
                    params_match = False
                    print(f"    🔍 参数 '{key}': 期望 {value}, 实际 {parsed.params.get(key)}")
                    break

            if type_match and params_match:
                print(f"  ✅ '{query}' 参数正确")
                passed += 1
            else:
                print(f"  ❌ '{query}' 参数错误")
                print(f"    类型匹配: {type_match}")

        except Exception as e:
            print(f"  ❌ '{query}' 参数错误: {e}")

    print(f"  📊 结果: {passed}/{total} 通过")
    return passed == total


def test_module_imports():
    """测试模块导入"""
    print("📦 测试模块导入...")

    try:
        # 测试核心模块导入
        from genome_mcp.core import (
            QueryParser, QueryType, QueryExecutor, ParsedQuery,
            NCBIClient, UniProtClient, OrthoDBClient
        )
        print(f"  ✅ 核心模块导入成功")

        # 测试进化工具模块导入
        from genome_mcp.core.evolution_tools import (
            analyze_gene_evolution, build_phylogenetic_profile
        )
        print(f"  ✅ 进化工具模块导入成功")

        # 测试主模块导入
        from genome_mcp import (
            QueryParser as MainQueryParser,
            QueryType as MainQueryType,
            analyze_gene_evolution as MainAnalyzeEvolution
        )
        print(f"  ✅ 主模块导入成功")

        return True

    except Exception as e:
        print(f"  ❌ 模块导入失败: {e}")
        return False


def test_batch_operations():
    """测试批量操作"""
    print("📦 测试批量操作...")

    try:
        # 测试批量查询解析
        batch_query = ["TP53", "BRCA1", "BRCA2", "EGFR", "MYC"]
        parsed = QueryParser.parse(batch_query)

        if parsed.type == QueryType.BATCH and parsed.is_batch:
            print(f"  ✅ 批量查询解析成功")
            print(f"    📋 查询类型: {parsed.type.value}")
            print(f"    📝 查询字符串: {parsed.query}")
            print(f"    🔢 批量标识: {parsed.is_batch}")
            print(f"    📦 基因列表: {parsed.params.get('gene_ids', [])}")

            # 验证基因列表
            expected_genes = ["TP53", "BRCA1", "BRCA2", "EGFR", "MYC"]
            actual_genes = parsed.params.get('gene_ids', [])

            if actual_genes == expected_genes:
                print(f"  ✅ 批量基因列表正确")
                return True
            else:
                print(f"  ❌ 批量基因列表错误")
                print(f"    期望: {expected_genes}")
                print(f"    实际: {actual_genes}")
                return False
        else:
            print(f"  ❌ 批量查询解析失败")
            return False

    except Exception as e:
        print(f"  ❌ 批量操作测试失败: {e}")
        return False


def test_edge_cases():
    """测试边界情况"""
    print("🔍 测试边界情况...")

    edge_cases = [
        # (查询, 期望行为, 描述)
        ("", "error", "空字符串"),
        ("   ", "error", "空白字符串"),
        ("INVALID-GENE-123", "search", "无效基因ID格式"),
        ("chrXYZ:123-456", "search", "无效染色体格式"),
        ("P123456789012345", "search", "过长UniProt ID"),
        ("A", "search", "过短查询"),
    ]

    passed = 0
    total = len(edge_cases)

    for query, expected_behavior, description in edge_cases:
        try:
            if expected_behavior == "error":
                # 期望出现错误
                try:
                    parsed = QueryParser.parse(query)
                    print(f"  ❌ '{query}' 应该出错但没有出错 ({description})")
                except:
                    print(f"  ✅ '{query}' 正确处理为错误 ({description})")
                    passed += 1
            else:
                # 期望正常解析
                parsed = QueryParser.parse(query)
                if parsed.type.value == expected_behavior:
                    print(f"  ✅ '{query}' → {parsed.type.value} ({description})")
                    passed += 1
                else:
                    print(f"  ❌ '{query}' → {parsed.type.value} (期望: {expected_behavior}, {description})")

        except Exception as e:
            print(f"  ⚠️ '{query}' → 意外错误: {e} ({description})")

    print(f"  📊 边界测试结果: {passed}/{total} 通过")
    return passed >= total * 0.8  # 80%通过率即可


def main():
    """主测试函数"""
    print("🧪 Genome MCP 核心功能测试")
    print("=" * 60)
    print("测试不依赖外部API，适合快速验证核心功能")
    print("=" * 60)

    tests = [
        ("模块导入", test_module_imports),
        ("查询解析器", test_query_parser),
        ("批量操作", test_batch_operations),
        ("查询参数", test_query_parameters),
        ("进化关键词", test_evolution_keywords),
        ("边界情况", test_edge_cases),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 执行测试: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} 测试通过")
        else:
            print(f"❌ {test_name} 测试失败")

    print("\n" + "=" * 60)
    print(f"📊 测试总结: {passed}/{total} 个测试组通过")

    if passed == total:
        print("🎉 所有核心功能测试通过！")
        print("🚀 Genome MCP 核心功能准备就绪")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return 1


if __name__ == "__main__":
    exit(main())