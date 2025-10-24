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
UNIPROT_BASE_URL = "https://rest.uniprot.org/uniprotkb"

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
    PROTEIN = "protein"  # 蛋白质信息查询
    GENE_PROTEIN = "gene_protein"  # 基因-蛋白质整合查询
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


class UniProtClient:
    """UniProt API客户端 - 处理蛋白质数据查询"""

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_proteins(
        self,
        query: str,
        max_results: int = 20,
        fields: str = "accession,id,protein_name,gene_names,organism_name,sequence,length,go_terms,keywords",
        organism: str = "9606"  # Human by default
    ) -> dict[str, Any]:
        """搜索蛋白质"""
        url = f"{UNIPROT_BASE_URL}/search"
        params = {
            "query": f"{query} AND organism_id:{organism}",
            "fields": fields,
            "size": max_results,
            "format": "json"
        }

        async with self.session.get(url, params=params) as response:
            data = await response.json()

        results = data.get("results", [])
        processed_results = []

        for protein in results:
            processed_results.append({
                "accession": protein.get("primaryAccession"),
                "id": protein.get("uniProtkbId"),
                "protein_name": protein.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", ""),
                "gene_names": [gene.get("geneName", {}).get("value", "") for gene in protein.get("genes", [])],
                "organism": protein.get("organism", {}).get("scientificName", ""),
                "sequence": protein.get("sequence", {}).get("value", ""),
                "length": protein.get("sequence", {}).get("length", 0),
                "go_terms": self._extract_go_terms(protein.get("uniProtKBCrossReferences", [])),
                "keywords": [keyword.get("name", "") for keyword in protein.get("keywords", [])],
                "function": self._extract_function(protein.get("comments", [])),
                "diseases": self._extract_diseases(protein.get("diseases", [])),
                "features": self._extract_features(protein.get("features", []))
            })

        return {
            "query": query,
            "count": len(processed_results),
            "results": processed_results
        }

    async def get_protein_by_accession(
        self,
        accession: str,
        fields: str = "accession,id,protein_name,gene_names,organism_name,sequence,length,go_terms,keywords,diseases,comments,features"
    ) -> dict[str, Any]:
        """通过访问号获取蛋白质详细信息"""
        url = f"{UNIPROT_BASE_URL}/{accession}"
        params = {"fields": fields, "format": "json"}

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return {"error": f"Protein not found: {accession}"}
            data = await response.json()

        # 处理返回数据
        return {
            "accession": data.get("primaryAccession"),
            "id": data.get("uniProtkbId"),
            "protein_name": data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", ""),
            "gene_names": [gene.get("geneName", {}).get("value", "") for gene in data.get("genes", [])],
            "organism": data.get("organism", {}).get("scientificName", ""),
            "sequence": data.get("sequence", {}).get("value", ""),
            "length": data.get("sequence", {}).get("length", 0),
            "mass": data.get("sequence", {}).get("mass", 0),
            "go_terms": self._extract_go_terms(data.get("uniProtKBCrossReferences", [])),
            "keywords": [keyword.get("name", "") for keyword in data.get("keywords", [])],
            "function": self._extract_function(data.get("comments", [])),
            "diseases": self._extract_diseases(data.get("diseases", [])),
            "features": self._extract_features(data.get("features", [])),
            "subcellular_location": self._extract_subcellular_location(data.get("comments", [])),
            "interaction_partners": self._extract_interactions(data.get("uniProtKBCrossReferences", []))
        }

    async def search_by_gene_exact(
        self,
        gene_symbol: str,
        organism: str = "9606",
        max_results: int = 10
    ) -> dict[str, Any]:
        """通过精确基因符号搜索蛋白质"""
        query = f"gene_exact:{gene_symbol} AND organism_id:{organism}"
        return await self.search_proteins(query, max_results)

    def _extract_go_terms(self, cross_references: list) -> dict[str, list]:
        """提取GO术语"""
        go_terms = {"biological_process": [], "molecular_function": [], "cellular_component": []}

        for ref in cross_references:
            if ref.get("database") == "GO":
                go_id = ref.get("id", "")
                term = ref.get("properties", [{}])[0].get("value", "") if ref.get("properties") else ""
                aspect = ref.get("properties", [{}])[1].get("value", "") if len(ref.get("properties", [])) > 1 else ""

                if aspect == "P":
                    go_terms["biological_process"].append({"id": go_id, "term": term})
                elif aspect == "F":
                    go_terms["molecular_function"].append({"id": go_id, "term": term})
                elif aspect == "C":
                    go_terms["cellular_component"].append({"id": go_id, "term": term})

        return go_terms

    def _extract_function(self, comments: list) -> str:
        """提取功能描述"""
        for comment in comments:
            if comment.get("commentType") == "FUNCTION":
                return comment.get("texts", [{}])[0].get("value", "") if comment.get("texts") else ""
        return ""

    def _extract_diseases(self, diseases: list) -> list:
        """提取疾病信息"""
        disease_list = []
        for disease in diseases:
            disease_info = {
                "name": disease.get("diseaseName", ""),
                "acronym": disease.get("acronym", ""),
                "description": disease.get("description", "")
            }
            disease_list.append(disease_info)
        return disease_list

    def _extract_features(self, features: list) -> list:
        """提取特征信息（结构域、位点等）"""
        feature_list = []
        for feature in features:
            if feature.get("type") in ["DOMAIN", "REGION", "MOTIF", "BINDING", "ACT_SITE"]:
                feature_info = {
                    "type": feature.get("type", ""),
                    "description": feature.get("description", ""),
                    "location": feature.get("location", {})
                }
                feature_list.append(feature_info)
        return feature_list

    def _extract_subcellular_location(self, comments: list) -> list:
        """提取亚细胞定位"""
        locations = []
        for comment in comments:
            if comment.get("commentType") == "SUBCELLULAR LOCATION":
                for location in comment.get("subcellularLocations", []):
                    loc = location.get("location", {}).get("value", "")
                    if loc:
                        locations.append(loc)
        return locations

    def _extract_interactions(self, cross_references: list) -> list:
        """提取蛋白质相互作用"""
        interactions = []
        for ref in cross_references:
            if ref.get("database") == "IntAct":
                interactions.append({
                    "database": "IntAct",
                    "id": ref.get("id", "")
                })
        return interactions


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
        elif query_type == "protein":
            return QueryParser._parse_protein(query)
        elif query_type == "gene_protein":
            return QueryParser._parse_gene_protein(query)
        else:
            return QueryParser._parse_auto(query)

    @staticmethod
    def _parse_auto(query: str) -> ParsedQuery:
        """自动识别查询类型"""

        # UniProt 访问号模式 (如 P04637)
        if re.match(r"^[A-Z0-9]{6,10}$", query) and not re.match(r"^[A-Z]{2,}\d+$", query):
            return QueryParser._parse_protein(query)

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

        # 蛋白质相关关键词检测
        protein_keywords = ["protein", "sequence", "domain", "enzyme", "kinase", "receptor"]
        if any(keyword in query.lower() for keyword in protein_keywords):
            return QueryParser._parse_protein(query)

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

    @staticmethod
    def _parse_protein(query: str) -> ParsedQuery:
        """解析蛋白质查询"""
        return ParsedQuery(
            type=QueryType.PROTEIN,
            query=query,
            params={
                "protein_query": query,
                "max_results": 20,
                "organism": "9606"  # Default to human
            }
        )

    @staticmethod
    def _parse_gene_protein(query: str) -> ParsedQuery:
        """解析基因-蛋白质整合查询"""
        return ParsedQuery(
            type=QueryType.GENE_PROTEIN,
            query=query,
            params={
                "gene_query": query,
                "max_results": 20,
                "organism": "9606"  # Default to human
            }
        )


class QueryExecutor:
    """查询执行器 - 统一处理所有查询"""

    def __init__(self):
        self.ncbi_client = NCBIClient()
        self.uniprot_client = UniProtClient()

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
        elif parsed_query.type == QueryType.PROTEIN:
            return await self._execute_protein(params)
        elif parsed_query.type == QueryType.GENE_PROTEIN:
            return await self._execute_gene_protein(params)
        else:
            raise ValueError(f"Unsupported query type: {parsed_query.type}")

    async def _execute_info(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行信息查询"""
        gene_id = params["gene_id"]

        # 检查缓存
        cached = self.ncbi_client.get_cached_gene(gene_id)
        if cached:
            return {"gene_id": gene_id, "source": "cache", "data": cached}

        # 从NCBI获取
        async with self.ncbi_client as client:
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

        async with self.ncbi_client as client:
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

        async with self.ncbi_client as client:
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

        async with self.ncbi_client as client:
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

    async def _execute_protein(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行蛋白质查询"""
        protein_query = params["protein_query"]
        max_results = params.get("max_results", 20)
        organism = params.get("organism", "9606")

        async with self.uniprot_client as client:
            # 检查是否是UniProt访问号
            if re.match(r"^[A-Z][0-9A-Z]{5}[0-9]$", protein_query):
                # 直接获取蛋白质详细信息
                result = await client.get_protein_by_accession(protein_query)
                return {
                    "protein_query": protein_query,
                    "source": "uniprot_direct",
                    "data": result
                }
            else:
                # 搜索蛋白质
                result = await client.search_proteins(
                    protein_query,
                    max_results=max_results,
                    organism=organism
                )
                return {
                    "protein_query": protein_query,
                    "source": "uniprot_search",
                    "data": result
                }

    async def _execute_gene_protein(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行基因-蛋白质整合查询"""
        gene_query = params["gene_query"]
        max_results = params.get("max_results", 20)
        organism = params.get("organism", "9606")

        # 并发查询NCBI和UniProt
        async with self.ncbi_client as ncbi_client, self.uniprot_client as uniprot_client:
            # NCBI基因查询
            ncbi_task = ncbi_client.search(gene_query, max_results=1)
            # UniProt蛋白质查询
            uniprot_task = uniprot_client.search_by_gene_exact(
                gene_query, organism, max_results
            )

            ncbi_result, uniprot_result = await asyncio.gather(
                ncbi_task, uniprot_task
            )

            # 获取基因详细信息
            gene_data = None
            if ncbi_result["results"]:
                gene_details = await ncbi_client.fetch_details(ncbi_result["results"])
                if gene_details:
                    uid = ncbi_result["results"][0]
                    gene_data = gene_details.get(uid, {})

            # 整合数据
            integrated_result = {
                "gene_query": gene_query,
                "source": "integrated",
                "gene_data": gene_data,
                "protein_data": uniprot_result,
                "integration_info": {
                    "gene_found": gene_data is not None,
                    "protein_count": len(uniprot_result.get("results", [])),
                    "organism": organism
                }
            }

            return integrated_result


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
    - "P04637" → 蛋白质详细信息查询
    - "cancer" → 基因搜索
    - "protein kinase" → 蛋白质功能搜索
    - "chr17:7565097-7590856" → 区域搜索
    - "TP53, BRCA1" → 批量基因信息
    - "breast cancer genes" → 智能搜索

    Args:
        query: 查询内容（可以是基因ID、蛋白质ID、搜索词、区域、ID列表）
        query_type: 查询类型（auto/info/search/region/protein/gene_protein）
        data_type: 数据类型（gene/protein/gene_protein）
        format: 返回格式（simple/detailed/raw）
        species: 物种（默认：human，支持9606/human/mouse/rat等）
        max_results: 最大结果数（默认：20）

    Returns:
        查询结果字典，包含基因和/或蛋白质信息

    Examples:
        # 基因信息查询
        get_data("TP53")

        # 蛋白质查询
        get_data("P04637", data_type="protein")

        # 基因-蛋白质整合查询
        get_data("TP53", data_type="gene_protein")

        # 蛋白质功能搜索
        get_data("tumor suppressor", data_type="protein")
    """
    try:
        # 根据data_type参数调整查询类型
        if data_type == "protein" and query_type == "auto":
            query_type = "protein"
        elif data_type == "gene_protein" and query_type == "auto":
            query_type = "gene_protein"
        elif data_type == "gene" and query_type == "auto":
            query_type = "auto"  # 保持原有的自动识别

        # 解析查询意图
        parsed = QueryParser.parse(query, query_type)

        # 添加物种信息到参数中
        organism_mapping = {
            "human": "9606",
            "mouse": "10090",
            "rat": "10116",
            "zebrafish": "7955",
            "fruitfly": "7227",
            "worm": "6239"
        }
        if "organism" not in parsed.params:
            organism_code = organism_mapping.get(species.lower(), "9606")
            parsed.params["organism"] = organism_code

        # 执行查询
        result = await _query_executor.execute(parsed, max_results=max_results)

        # 格式化结果
        if format == "simple":
            return _format_simple_result(result)
        elif format == "detailed":
            return result
        else:
            return result

    except Exception as e:
        return {"error": str(e), "query": query, "data_type": data_type}


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

    source = result.get("source", "")

    # 基因查询结果
    if source in ["ncbi", "cache"]:
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
                    "data_type": "gene"
                }

    # 蛋白质查询结果
    elif source in ["uniprot_direct", "uniprot_search"]:
        data = result.get("data", {})
        if isinstance(data, dict) and "results" in data:
            # 搜索结果
            proteins = data["results"]
            if proteins:
                protein = proteins[0]  # 取第一个结果
                return {
                    "protein_id": protein.get("accession"),
                    "name": protein.get("protein_name"),
                    "gene_names": protein.get("gene_names", []),
                    "organism": protein.get("organism"),
                    "length": protein.get("length"),
                    "function": protein.get("function", "")[:200] + "..." if protein.get("function") else "",
                    "data_type": "protein",
                    "results_count": len(proteins)
                }
        elif isinstance(data, dict) and "accession" in data:
            # 单个蛋白质详细信息
            return {
                "protein_id": data.get("accession"),
                "name": data.get("protein_name"),
                "gene_names": data.get("gene_names", []),
                "organism": data.get("organism"),
                "length": data.get("length"),
                "function": data.get("function", "")[:200] + "..." if data.get("function") else "",
                "data_type": "protein"
            }

    # 基因-蛋白质整合查询结果
    elif source == "integrated":
        gene_data = result.get("gene_data", {})
        protein_data = result.get("protein_data", {})
        integration_info = result.get("integration_info", {})

        formatted_result = {
            "data_type": "gene_protein",
            "integration_info": integration_info
        }

        # 添加基因信息
        if gene_data:
            formatted_result["gene"] = {
                "uid": gene_data.get("uid"),
                "name": gene_data.get("name"),
                "description": gene_data.get("description"),
                "chromosome": gene_data.get("chromosome")
            }

        # 添加蛋白质信息
        if protein_data and protein_data.get("results"):
            proteins = protein_data["results"]
            if proteins:
                protein = proteins[0]
                formatted_result["protein"] = {
                    "accession": protein.get("accession"),
                    "name": protein.get("protein_name"),
                    "length": protein.get("length"),
                    "function": protein.get("function", "")[:200] + "..." if protein.get("function") else ""
                }

        return formatted_result

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
