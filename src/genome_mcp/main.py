#!/usr/bin/env python3
"""
Genome MCP - 优化版本：3个极简工具覆盖所有功能

Linus风格：统一接口，智能解析，高效批量查询
"""

import asyncio
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

import aiohttp
from fastmcp import FastMCP

mcp = FastMCP("Genome MCP", version="0.2.0")

NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# 常用基因缓存（减少API调用）
COMMON_GENES_CACHE = {
    "TP53": {"name": "Tumor protein p53", "chromosome": "17p13.1"},
    "BRCA1": {"name": "BRCA1 DNA repair associated", "chromosome": "17q21.31"},
    "BRCA2": {"name": "BRCA2 DNA repair associated", "chromosome": "13q13.1"},
    "EGFR": {"name": "Epidermal growth factor receptor", "chromosome": "7p11.2"},
    "MYC": {"name": "MYC proto oncogene", "chromosome": "8q24.21"},
}


class QueryType(Enum):
    """查询类型枚举"""

    INFO = "info"  # 基因信息查询
    SEARCH = "search"  # 关键词搜索
    REGION = "region"  # 基因组区域搜索
    BATCH = "batch"  # 批量查询
    UNKNOWN = "unknown"  # 未知类型


@dataclass
class ParsedQuery:
    """解析后的查询对象"""

    type: QueryType
    query: str
    params: dict[str, Any]
    is_batch: bool = False


class NCBIClient:
    """NCBI API客户端 - 统一处理所有API调用"""

    def __init__(self):
        self.session = None
        self.cache = COMMON_GENES_CACHE.copy()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search(self, term: str, max_results: int = 20) -> dict[str, Any]:
        """搜索基因"""
        url = f"{NCBI_BASE_URL}/esearch.fcgi"
        params = {"db": "gene", "term": term, "retmax": max_results, "retmode": "json"}

        async with self.session.get(url, params=params) as response:
            data = await response.json()

        return {
            "term": term,
            "count": data.get("esearchresult", {}).get("count", 0),
            "results": data.get("esearchresult", {}).get("idlist", []),
        }

    async def fetch_details(self, uids: list[str]) -> dict[str, Any]:
        """批量获取详细信息"""
        if not uids:
            return {}

        url = f"{NCBI_BASE_URL}/esummary.fcgi"
        params = {"db": "gene", "id": ",".join(uids), "retmode": "json"}

        async with self.session.get(url, params=params) as response:
            data = await response.json()

        return data.get("result", {})

    async def search_region(
        self, chromosome: str, start: int, end: int
    ) -> dict[str, Any]:
        """按区域搜索基因"""
        # 转换染色体格式
        if chromosome.startswith("chr"):
            chromosome = chromosome[3:]

        search_term = f"{chromosome}[chr] AND {start}:{end}[chrpos]"

        return await self.search(search_term, max_results=100)

    def get_cached_gene(self, gene_id: str) -> dict[str, Any] | None:
        """获取缓存的基因信息"""
        return self.cache.get(gene_id)


class QueryParser:
    """智能查询解析器 - 自动识别查询意图"""

    @staticmethod
    def parse(query: str | list[str], query_type: str = "auto") -> ParsedQuery:
        """解析查询意图"""

        # 处理批量查询
        if isinstance(query, list):
            return QueryParser._parse_batch(query)

        query = str(query).strip()

        # 指定类型查询
        if query_type != "auto":
            return QueryParser._parse_by_type(query, query_type)

        # 自动识别查询类型
        return QueryParser._parse_auto(query)

    @staticmethod
    def _parse_batch(gene_ids: list[str]) -> ParsedQuery:
        """解析批量查询"""
        return ParsedQuery(
            type=QueryType.BATCH,
            query=",".join(gene_ids),
            params={"gene_ids": gene_ids},
            is_batch=True,
        )

    @staticmethod
    def _parse_by_type(query: str, query_type: str) -> ParsedQuery:
        """按指定类型解析"""
        if query_type == "info":
            return QueryParser._parse_gene_info(query)
        elif query_type == "region":
            return QueryParser._parse_region(query)
        elif query_type == "search":
            return QueryParser._parse_search(query)
        else:
            return QueryParser._parse_auto(query)

    @staticmethod
    def _parse_auto(query: str) -> ParsedQuery:
        """自动识别查询类型"""

        # 基因ID模式
        if re.match(r"^[A-Z]{2,}\d+$", query):
            return QueryParser._parse_gene_info(query)

        # 区域格式
        if re.match(r"^(?:chr)?[XY\d]+[:\[]\d+-\d+", query.replace(" ", "")):
            return QueryParser._parse_region(query)

        # 批量ID格式
        if "," in query and all(
            re.match(r"^[A-Z]{2,}\d+$", id.strip()) for id in query.split(",")
        ):
            return QueryParser._parse_batch([id.strip() for id in query.split(",")])

        # 默认为搜索
        return QueryParser._parse_search(query)

    @staticmethod
    def _parse_gene_info(query: str) -> ParsedQuery:
        """解析基因信息查询"""
        gene_id = query.strip()
        return ParsedQuery(
            type=QueryType.INFO, query=gene_id, params={"gene_id": gene_id}
        )

    @staticmethod
    def _parse_search(query: str) -> ParsedQuery:
        """解析搜索查询"""
        return ParsedQuery(
            type=QueryType.SEARCH,
            query=query,
            params={"term": query, "max_results": 20},
        )

    @staticmethod
    def _parse_region(query: str) -> ParsedQuery:
        """解析区域查询"""
        # 标准化区域格式
        query = query.replace(" ", "")

        patterns = [
            r"(?:chr)?(\d+|[XY]):(\d+)-(\d+)",
            r"(?:chr)?(\d+|[XY])\[(\d+)-(\d+)\]",
        ]

        for pattern in patterns:
            match = re.match(pattern, query)
            if match:
                chromosome, start, end = match.groups()
                chromosome = (
                    f"chr{chromosome}"
                    if not chromosome.startswith("chr")
                    else chromosome
                )
                return ParsedQuery(
                    type=QueryType.REGION,
                    query=f"{chromosome}:{start}-{end}",
                    params={
                        "chromosome": chromosome,
                        "start": int(start),
                        "end": int(end),
                    },
                )

        raise ValueError(f"Invalid region format: {query}")


class QueryExecutor:
    """查询执行器 - 统一处理所有查询"""

    def __init__(self):
        self.client = NCBIClient()

    async def execute(self, parsed_query: ParsedQuery, **kwargs) -> dict[str, Any]:
        """执行解析后的查询"""

        # 合并参数
        params = {**parsed_query.params, **kwargs}

        if parsed_query.type == QueryType.INFO:
            return await self._execute_info(params)
        elif parsed_query.type == QueryType.SEARCH:
            return await self._execute_search(params)
        elif parsed_query.type == QueryType.REGION:
            return await self._execute_region(params)
        elif parsed_query.type == QueryType.BATCH:
            return await self._execute_batch(params)
        else:
            raise ValueError(f"Unsupported query type: {parsed_query.type}")

    async def _execute_info(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行信息查询"""
        gene_id = params["gene_id"]

        # 检查缓存
        cached = self.client.get_cached_gene(gene_id)
        if cached:
            return {"gene_id": gene_id, "source": "cache", "data": cached}

        # 从NCBI获取
        async with self.client as client:
            # 先搜索获取UID
            search_result = await client.search(gene_id, max_results=1)
            if not search_result["results"]:
                return {"error": "Gene not found", "gene_id": gene_id}

            # 获取详细信息
            details = await client.fetch_details(search_result["results"])
            gene_data = details.get(search_result["results"][0], {})

            return {
                "gene_id": gene_id,
                "uid": search_result["results"][0],
                "source": "ncbi",
                "data": gene_data,
            }

    async def _execute_search(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行搜索查询"""
        term = params["term"]
        max_results = params.get("max_results", 20)

        async with self.client as client:
            result = await client.search(term, max_results)

            return {
                "term": term,
                "count": int(result["count"]),
                "results": result["results"],
            }

    async def _execute_region(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行区域查询"""
        chromosome = params["chromosome"]
        start = params["start"]
        end = params["end"]

        async with self.client as client:
            result = await client.search_region(chromosome, start, end)

            return {
                "region": f"{chromosome}:{start}-{end}",
                "chromosome": chromosome,
                "start": start,
                "end": end,
                "count": int(result["count"]),
                "results": result["results"],
            }

    async def _execute_batch(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行批量查询"""
        gene_ids = params["gene_ids"]

        # 批量搜索UID
        search_terms = " OR ".join([f'"{gid}"[gid]]' for gid in gene_ids])

        async with self.client as client:
            search_result = await client.search(
                search_terms, max_results=len(gene_ids) * 2
            )

            if not search_result["results"]:
                return {"batch_size": len(gene_ids), "results": {}}

            # 批量获取详细信息
            details = await client.fetch_details(search_result["results"])

            # 整理结果
            results = {}
            for gene_id in gene_ids:
                # 查找对应的详细信息
                found = False
                for uid, data in details.items():
                    # 跳过非字典项（如统计信息）
                    if not isinstance(data, dict):
                        continue

                    gene_symbols = data.get("name", "")
                    if gene_symbols:
                        gene_symbols = str(gene_symbols).split(", ")
                        if isinstance(gene_symbols, str):
                            gene_symbols = [gene_symbols]

                        # 检查基因ID是否匹配
                        if gene_id in gene_symbols or uid in gene_ids:
                            results[gene_id] = {
                                "gene_id": gene_id,
                                "uid": uid,
                                "data": data,
                            }
                            found = True
                            break
                    # 也检查UID直接匹配
                    elif uid in search_result["results"]:
                        results[gene_id] = {
                            "gene_id": gene_id,
                            "uid": uid,
                            "data": data,
                        }
                        found = True
                        break

                if not found:
                    results[gene_id] = {"error": "Gene not found"}

            return {"batch_size": len(gene_ids), "results": results}


# 全局查询执行器实例
_query_executor = QueryExecutor()


# === MCP工具实现 ===


@mcp.tool()
async def get_data(
    query: str | list[str],
    query_type: str = "auto",
    data_type: str = "gene",
    format: str = "simple",
    species: str = "human",
    max_results: int = 20,
) -> dict[str, Any]:
    """
    智能数据获取接口 - 统一处理所有查询类型

    自动识别查询类型：
    - "TP53" → 基因信息查询
    - "cancer" → 基因搜索
    - "chr17:7565097-7590856" → 区域搜索
    - "TP53, BRCA1" → 批量基因信息
    - "breast cancer genes" → 智能搜索

    Args:
        query: 查询内容（可以是基因ID、搜索词、区域、ID列表）
        query_type: 查询类型（auto/info/search/region）
        data_type: 数据类型（gene/snp/protein）
        format: 返回格式（simple/detailed/raw）
        species: 物种（默认：human）
        max_results: 最大结果数（默认：20）

    Returns:
        查询结果字典
    """
    try:
        # 解析查询意图
        parsed = QueryParser.parse(query, query_type)

        # 执行查询
        result = await _query_executor.execute(parsed)

        # 格式化结果
        if format == "simple":
            return _format_simple_result(result)
        elif format == "detailed":
            return result
        else:
            return result

    except Exception as e:
        return {"error": str(e), "query": query}


@mcp.tool()
async def advanced_query(
    queries: list[dict[str, Any]],
    strategy: str = "parallel",
    delay: float = 0.35,
    max_concurrent: int = 3,
) -> dict[str, Any]:
    """
    高级批量查询接口 - 支持复杂的批量查询策略

    Args:
        queries: 查询列表
            [{"type": "info", "query": "TP53"},
             {"type": "search", "query": "cancer", "max_results": 10}]
        strategy: 执行策略（parallel/sequential）
        delay: 查询间隔（秒，遵守NCBI频率限制）
        max_concurrent: 最大并发数

    Returns:
        批量查询结果
    """
    results = {}

    if strategy == "parallel":
        # 并发查询（适用于独立查询）
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_query(index: int, query_dict: dict[str, Any]):
            async with semaphore:
                try:
                    parsed = QueryParser.parse_by_type(
                        query_dict["query"], query_dict.get("type", "auto")
                    )
                    result = await _query_executor.execute(parsed, **query_dict)
                    results[index] = result
                    await asyncio.sleep(delay)  # 遵守频率限制
                except Exception as e:
                    results[index] = {"error": str(e), "query": query_dict}

        await asyncio.gather(
            *[execute_single_query(i, q) for i, q in enumerate(queries)]
        )

    else:
        # 顺序查询（适用于依赖查询）
        for i, query_dict in enumerate(queries):
            try:
                parsed = QueryParser.parse_by_type(
                    query_dict["query"], query_dict.get("type", "auto")
                )
                result = await _query_executor.execute(parsed, **query_dict)
                results[i] = result
                await asyncio.sleep(delay)  # 遵守频率限制
            except Exception as e:
                results[i] = {"error": str(e), "query": query_dict}

    return {
        "strategy": strategy,
        "total_queries": len(queries),
        "successful": len([r for r in results.values() if "error" not in r]),
        "results": results,
    }


@mcp.tool()
async def smart_search(
    description: str,
    context: str = "genomics",
    filters: dict[str, Any] = None,
    max_results: int = 20,
) -> dict[str, Any]:
    """
    智能语义搜索 - 理解自然语言描述并执行相应查询

    语义理解示例：
    - "breast cancer genes on chromosome 17" → 查找17号染色体上的乳腺癌基因
    - "TP53 protein interactions" → 查找TP53蛋白相互作用
    - "tumor suppressor genes" → 查找肿瘤抑制基因
    - "genes related to DNA repair" → 查找DNA修复相关基因

    Args:
        description: 自然语言描述
        context: 搜索上下文（genomics/proteomics/pathway）
        filters: 过滤条件
        max_results: 最大结果数

    Returns:
        智能搜索结果
    """
    try:
        # 简单的语义理解
        query_terms = _understand_query(description, context)

        # 应用过滤器
        if filters:
            query_terms = _apply_filters(query_terms, filters)

        # 执行查询
        result = await _query_executor.execute(QueryParser._parse_search(query_terms))

        # 添加语义信息
        result.update(
            {
                "description": description,
                "interpreted_query": query_terms,
                "context": context,
                "filters": filters or {},
            }
        )

        return result

    except Exception as e:
        return {"error": str(e), "description": description, "interpreted_query": None}


# === 辅助函数 ===


def _format_simple_result(result: dict[str, Any]) -> dict[str, Any]:
    """格式化为简单结果"""
    if "error" in result:
        return result

    if result.get("batch_size"):
        # 批量查询结果
        successful = {k: v for k, v in result["results"].items() if "error" not in v}
        return {
            "batch_size": result["batch_size"],
            "successful_count": len(successful),
            "results": successful,
        }

    # 单个查询结果
    if "data" in result and result["data"] is not None:
        data = result["data"]
        if isinstance(data, dict):
            summary = data.get("summary", "")
            if summary and len(summary) > 200:
                summary = summary[:200] + "..."

            return {
                "gene_id": result.get("gene_id"),
                "uid": result.get("uid"),
                "name": data.get("name"),
                "description": data.get("description"),
                "chromosome": data.get("chromosome"),
                "summary": summary,
            }

    return result


def _understand_query(description: str, context: str) -> str:
    """简单的语义理解"""
    desc = description.lower()

    # 染色体特定查询
    if "chromosome" in desc:
        # 提取染色体信息
        chr_match = re.search(r"chromosome\s*(\d+|[xy])", desc)
        if chr_match:
            chr_num = chr_match.group(1).upper()
            if chr_num in ["X", "Y", "XY"]:
                return f"chr{chr_num}[chr] AND ({description})"
            return f"chr{chr_num}[chr] AND ({description})"

    # 疾病相关查询
    if any(word in desc for word in ["cancer", "tumor", "disease"]):
        return f"{description} AND neoplasia[mesh]"

    # 蛋白相关查询
    if any(word in desc for word in ["protein", "interaction", "pathway"]):
        return description

    # 默认返回原描述
    return description


def _apply_filters(query: str, filters: dict[str, Any]) -> str:
    """应用搜索过滤器"""
    if not filters:
        return query

    filter_parts = []

    # 物种过滤
    if "species" in filters:
        species = filters["species"].lower()
        if species != "human":
            filter_parts.append(f"{species}[organism]")

    # 基因类型过滤
    if "gene_type" in filters:
        gene_type = filters["gene_type"]
        if gene_type == "protein_coding":
            filter_parts.append("protein_coding[Properties]")

    # 合并过滤器
    if filter_parts:
        return f"{query} AND {' AND '.join(filter_parts)}"

    return query


def main():
    """主入口点"""

    mcp.run()


if __name__ == "__main__":
    main()
