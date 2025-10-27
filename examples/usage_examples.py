#!/usr/bin/env python3
"""
Genome MCP 现代化使用示例

本文件展示了如何使用现代化的 Genome MCP 系统的各种功能。
这个版本完全基于MCP架构，使用QueryParser和QueryExecutor。
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from genome_mcp.core import QueryExecutor, QueryParser


async def basic_gene_info_example():
    """基本基因信息查询示例"""
    print("🧬 基本基因信息查询示例")
    print("=" * 40)

    parser = QueryParser()
    executor = QueryExecutor()

    try:
        # 查询 TP53 基因信息
        parsed_query = parser.parse("TP53", query_type="info")
        result = await executor.execute(parsed_query)

        print(f"基因符号: {result.get('gene_symbol', 'N/A')}")
        print(f"基因ID: {result.get('gene_id', 'N/A')}")
        print(f"物种: {result.get('species', 'N/A')}")

        if "chromosome" in result:
            print(f"染色体位置: {result['chromosome']}")

        if "description" in result:
            print(f"描述: {result['description'][:200]}...")

        if "summary" in result:
            print(f"摘要: {result['summary'][:200]}...")

    except Exception as e:
        print(f"查询失败: {e}")


async def gene_search_example():
    """基因搜索示例"""
    print("\n🔍 基因搜索示例")
    print("=" * 40)

    parser = QueryParser()
    executor = QueryExecutor()

    try:
        # 搜索包含 "BRCA" 的基因
        parsed_query = parser.parse("BRCA", query_type="search")
        result = await executor.execute(parsed_query)

        print(f"搜索词: {result.get('term', 'N/A')}")
        print(f"总结果数: {result.get('total_count', 0)}")
        print(f"返回结果数: {len(result.get('results', []))}")

        print("\n前5个结果:")
        for i, gene in enumerate(result.get("results", [])[:5], 1):
            gene_id = gene.get("gene_id", "N/A")
            description = gene.get("description", "No description")
            print(f"{i}. {gene_id}: {description[:80]}...")

    except Exception as e:
        print(f"搜索失败: {e}")


async def batch_query_example():
    """批量查询示例"""
    print("\n📦 批量查询示例")
    print("=" * 40)

    parser = QueryParser()
    executor = QueryExecutor()

    try:
        # 批量查询多个基因
        gene_list = ["TP53", "BRCA1", "BRCA2", "EGFR"]
        parsed_query = parser.parse(gene_list, query_type="batch")
        result = await executor.execute(parsed_query)

        print(f"查询的基因数量: {result.get('batch_size', 0)}")
        print(f"成功查询: {len(result.get('results', []))}")

        print("\n查询结果:")
        for gene_data in result.get("results", []):
            gene_id = gene_data.get("gene_id", "N/A")
            description = gene_data.get("description", "No description")
            print(f"✅ {gene_id}: {description[:60]}...")

    except Exception as e:
        print(f"批量查询失败: {e}")


async def region_search_example():
    """基因组区域搜索示例"""
    print("\n🗺️ 基因组区域搜索示例")
    print("=" * 40)

    parser = QueryParser()
    executor = QueryExecutor()

    try:
        # 搜索特定基因组区域的基因
        region = "chr17:7565097-7590856"  # TP53 基因所在区域
        parsed_query = parser.parse(region, query_type="region")
        result = await executor.execute(parsed_query)

        print(f"搜索区域: {result.get('query', 'N/A')}")
        print(f"染色体: {result.get('chromosome', 'N/A')}")
        print(f"起始位置: {result.get('start', 'N/A')}")
        print(f"结束位置: {result.get('end', 'N/A')}")
        print(f"找到的基因数量: {len(result.get('genes_found', []))}")

        print("\n区域内的基因:")
        for gene in result.get("genes_found", []):
            gene_id = gene.get("gene_id", "N/A")
            name = gene.get("name", "N/A")
            print(f"🧬 {gene_id} ({name})")

    except Exception as e:
        print(f"区域搜索失败: {e}")


async def protein_query_example():
    """蛋白质查询示例"""
    print("\n🧪 蛋白质查询示例")
    print("=" * 40)

    parser = QueryParser()
    executor = QueryExecutor()

    try:
        # 查询蛋白质信息
        protein_id = "P04637"  # TP53 蛋白质
        parsed_query = parser.parse(protein_id, query_type="protein")
        result = await executor.execute(parsed_query)

        print(f"蛋白质ID: {result.get('protein_id', 'N/A')}")
        print(f"基因名称: {result.get('gene_name', 'N/A')}")
        print(f"蛋白质名称: {result.get('protein_name', 'N/A')}")

        if "sequence_length" in result:
            print(f"序列长度: {result['sequence_length']}")

        if "function" in result:
            print(f"功能: {result['function'][:150]}...")

    except Exception as e:
        print(f"蛋白质查询失败: {e}")


async def pathway_enrichment_example():
    """通路富集分析示例"""
    print("\n🧩 通路富集分析示例")
    print("=" * 40)

    parser = QueryParser()
    executor = QueryExecutor()

    try:
        # KEGG 通路富集分析
        gene_list = ["TP53", "BRCA1", "BRCA2", "EGFR", "MYC"]
        parsed_query = parser.parse(gene_list, query_type="pathway_enrichment")
        result = await executor.execute(parsed_query)

        print(f"分析的基因数量: {len(result.get('gene_list', []))}")
        print(f"识别的通路数量: {len(result.get('pathways', []))}")

        print("\n前5个显著通路:")
        for pathway in result.get("pathways", [])[:5]:
            pathway_id = pathway.get("pathway_id", "N/A")
            description = pathway.get("description", "N/A")
            p_value = pathway.get("p_value", "N/A")
            print(f"🔬 {pathway_id}: {description[:60]}... (p={p_value})")

    except Exception as e:
        print(f"通路富集分析失败: {e}")


async def evolution_analysis_example():
    """进化分析示例"""
    print("\n🧬 进化分析示例")
    print("=" * 40)

    parser = QueryParser()
    executor = QueryExecutor()

    try:
        # 基因进化分析
        gene_symbol = "TP53"

        parsed_query = parser.parse(gene_symbol, query_type="evolution")
        result = await executor.execute(parsed_query)

        print(f"目标基因: {result.get('gene_symbol', 'N/A')}")
        print(f"分析类型: {result.get('analysis_type', 'N/A')}")
        print(f"发现的同源基因数量: {len(result.get('homologs', []))}")

        print("\n部分同源基因:")
        for homolog in result.get("homologs", [])[:5]:
            species = homolog.get("species", "N/A")
            gene_id = homolog.get("gene_id", "N/A")
            identity = homolog.get("identity", "N/A")
            print(f"🧬 {species}: {gene_id} (相似度: {identity})")

    except Exception as e:
        print(f"进化分析失败: {e}")


async def smart_search_example():
    """智能语义搜索示例"""
    print("\n🤖 智能语义搜索示例")
    print("=" * 40)

    parser = QueryParser()
    executor = QueryExecutor()

    try:
        # 自然语言搜索
        search_queries = [
            "breast cancer genes on chromosome 17",
            "tumor suppressor genes",
            "DNA repair related genes",
        ]

        for query in search_queries:
            print(f"\n搜索: '{query}'")
            parsed_query = parser.parse(query, query_type="search")
            result = await executor.execute(parsed_query)

            count = result.get("total_count", 0)
            print(f"找到 {count} 个相关结果")

            # 显示前2个结果
            for gene in result.get("results", [])[:2]:
                gene_id = gene.get("gene_id", "N/A")
                description = gene.get("description", "N/A")
                print(f"  📍 {gene_id}: {description[:70]}...")

    except Exception as e:
        print(f"智能搜索失败: {e}")


async def main():
    """主函数：运行所有示例"""
    print("Genome MCP 现代化使用示例")
    print("=" * 50)
    print("本示例展示了如何使用 QueryParser + QueryExecutor 模式")
    print("来访问各种基因组数据功能。")
    print()

    # 运行所有示例
    examples = [
        basic_gene_info_example,
        gene_search_example,
        batch_query_example,
        region_search_example,
        protein_query_example,
        pathway_enrichment_example,
        evolution_analysis_example,
        smart_search_example,
    ]

    for example in examples:
        try:
            await example()
        except KeyboardInterrupt:
            print("\n用户中断示例")
            break
        except Exception as e:
            print(f"\n示例执行失败: {e}")
            continue

    print("\n" + "=" * 50)
    print("✅ 所有示例演示完成!")
    print("\n💡 使用提示:")
    print("1. 所有查询都通过 QueryParser.parse() 解析")
    print("2. 使用 QueryExecutor.execute() 执行查询")
    print(
        "3. 支持10种查询类型: info, search, region, batch, protein, gene_protein, ortholog, evolution, pathway_enrichment"
    )
    print("4. 自动查询类型识别: query_type='auto'")
    print("5. 推荐使用MCP客户端来访问这些功能")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序执行失败: {e}")
        sys.exit(1)
