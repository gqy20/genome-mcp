#!/usr/bin/env python3
"""
API客户端模块 - 包含所有外部API的客户端实现

NCBI, UniProt, KEGG API客户端
OrthoDB客户端已删除，将被Ensembl客户端替代
"""

import asyncio
from typing import Any

import aiohttp


class NCBIClient:
    """NCBI API客户端 - 统一处理所有API调用"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self):
        self.session = None
        self.cache = {
            "TP53": {"name": "Tumor protein p53", "chromosome": "17p13.1"},
            "BRCA1": {"name": "BRCA1 DNA repair associated", "chromosome": "17q21.31"},
            "BRCA2": {"name": "BRCA2 DNA repair associated", "chromosome": "13q13.1"},
            "EGFR": {
                "name": "Epidermal growth factor receptor",
                "chromosome": "7p11.2",
            },
            "MYC": {"name": "MYC proto oncogene", "chromosome": "8q24.21"},
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_cached_gene(self, gene_id: str) -> dict[str, Any] | None:
        """获取缓存的基因信息"""
        return self.cache.get(gene_id)

    async def search(self, term: str, max_results: int = 20) -> dict[str, Any]:
        """搜索基因"""
        url = f"{self.BASE_URL}/esearch.fcgi"
        params = {"db": "gene", "term": term, "retmax": max_results, "retmode": "json"}

        async with self.session.get(url, params=params) as response:
            data = await response.json()

        return {
            "term": term,
            "count": int(data.get("esearchresult", {}).get("count", 0)),
            "results": data.get("esearchresult", {}).get("idlist", []),
        }

    async def fetch_details(self, uids: list[str]) -> dict[str, Any]:
        """批量获取详细信息"""
        if not uids:
            return {}

        url = f"{self.BASE_URL}/esummary.fcgi"
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

        # 构建搜索查询
        query = f"{chromosome}[chr] AND {start}:{end}[chrpos]"

        search_result = await self.search(query, max_results=100)

        if search_result["results"]:
            details = await self.fetch_details(search_result["results"])
            return {
                "chromosome": chromosome,
                "start": start,
                "end": end,
                "genes_found": len(search_result["results"]),
                "gene_ids": search_result["results"],
                "gene_details": details,
            }
        else:
            return {
                "chromosome": chromosome,
                "start": start,
                "end": end,
                "genes_found": 0,
                "gene_ids": [],
                "gene_details": {},
            }


class UniProtClient:
    """UniProt API客户端 - 处理蛋白质数据查询"""

    BASE_URL = "https://rest.uniprot.org/uniprotkb"

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
        fields: str = "accession,id,protein_name,gene_names,organism_name,sequence,length",
        organism: str = "9606",  # Human by default
    ) -> dict[str, Any]:
        """搜索蛋白质"""
        try:
            url = f"{self.BASE_URL}/search"
            params = {
                "query": f"{query} AND organism_id:{organism}",
                "fields": fields,
                "size": max_results,
                "format": "json",
            }

            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return {
                        "error": f"UniProt search failed: HTTP {response.status}",
                        "query": query,
                        "organism": organism,
                        "suggestions": [
                            "检查查询参数是否正确",
                            "确认生物体ID是否有效",
                            "稍后重试",
                        ],
                    }

                data = await response.json()

            results = data.get("results", [])
            processed_results = []

            for protein in results:
                processed_results.append(
                    {
                        "accession": protein.get("primaryAccession"),
                        "id": protein.get("uniProtkbId"),
                        "protein_name": protein.get("proteinDescription", {})
                        .get("recommendedName", {})
                        .get("fullName", {})
                        .get("value", ""),
                        "gene_names": [
                            gene.get("geneName", {}).get("value", "")
                            for gene in protein.get("genes", [])
                        ],
                        "organism": protein.get("organism", {}).get(
                            "scientificName", ""
                        ),
                        "sequence": protein.get("sequence", {}).get("value", ""),
                        "length": protein.get("sequence", {}).get("length", 0),
                        "go_terms": self._extract_go_terms(
                            protein.get("uniProtKBCrossReferences", [])
                        ),
                        "keywords": [
                            keyword.get("name", "")
                            for keyword in protein.get("keywords", [])
                        ],
                        "function": self._extract_function(protein.get("comments", [])),
                        "diseases": self._extract_diseases(protein.get("diseases", [])),
                        "features": self._extract_features(protein.get("features", [])),
                    }
                )

            return {
                "query": query,
                "count": len(processed_results),
                "results": processed_results,
            }

        except Exception as e:
            return {
                "error": f"UniProt search error: {str(e)}",
                "query": query,
                "organism": organism,
                "suggestions": ["检查网络连接", "稍后重试", "简化查询条件"],
            }

    async def get_protein_by_accession(
        self,
        accession: str,
        fields: str = "accession,protein_name,gene_names,organism_name,sequence,length",
    ) -> dict[str, Any]:
        """通过访问号获取蛋白质详细信息"""
        url = f"{self.BASE_URL}/{accession}"
        params = {"fields": fields, "format": "json"}

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                return {"error": f"Protein not found: {accession}"}
            data = await response.json()

        # 处理返回数据
        return {
            "accession": data.get("primaryAccession"),
            "id": data.get("uniProtkbId"),
            "protein_name": data.get("proteinDescription", {})
            .get("recommendedName", {})
            .get("fullName", {})
            .get("value", ""),
            "gene_names": [
                gene.get("geneName", {}).get("value", "")
                for gene in data.get("genes", [])
            ],
            "organism": data.get("organism", {}).get("scientificName", ""),
            "sequence": data.get("sequence", {}).get("value", ""),
            "length": data.get("sequence", {}).get("length", 0),
            "mass": data.get("sequence", {}).get("mass", 0),
            "go_terms": self._extract_go_terms(
                data.get("uniProtKBCrossReferences", [])
            ),
            "keywords": [
                keyword.get("name", "") for keyword in data.get("keywords", [])
            ],
            "function": self._extract_function(data.get("comments", [])),
            "diseases": self._extract_diseases(data.get("diseases", [])),
            "features": self._extract_features(data.get("features", [])),
            "subcellular_location": self._extract_subcellular_location(
                data.get("comments", [])
            ),
            "interaction_partners": self._extract_interactions(
                data.get("uniProtKBCrossReferences", [])
            ),
        }

    async def search_by_gene_exact(
        self, gene_symbol: str, organism: str = "9606", max_results: int = 10
    ) -> dict[str, Any]:
        """通过精确基因符号搜索蛋白质"""
        query = f"gene_exact:{gene_symbol} AND organism_id:{organism}"
        return await self.search_proteins(query, max_results)

    def _extract_go_terms(self, cross_references: list) -> list:
        """提取GO术语"""
        go_terms = []
        for ref in cross_references:
            if ref.get("database") == "GO":
                go_terms.append(
                    {
                        "id": ref.get("id", ""),
                        "name": (
                            ref.get("properties", [{}])[0].get("value", "")
                            if ref.get("properties")
                            else ""
                        ),
                    }
                )
        return go_terms

    def _extract_function(self, comments: list) -> str:
        """提取功能描述"""
        for comment in comments:
            if comment.get("commentType") == "FUNCTION":
                return (
                    comment.get("texts", [{}])[0].get("value", "")
                    if comment.get("texts")
                    else ""
                )
        return ""

    def _extract_diseases(self, diseases: list) -> list:
        """提取疾病信息"""
        disease_list = []
        for disease in diseases:
            disease_list.append(
                {
                    "name": disease.get("diseaseName", ""),
                    "description": disease.get("description", ""),
                }
            )
        return disease_list

    def _extract_features(self, features: list) -> list:
        """提取结构域和功能特征"""
        feature_list = []
        for feature in features:
            if feature.get("type") in ["DOMAIN", "REGION", "MOTIF"]:
                feature_list.append(
                    {
                        "type": feature.get("type", ""),
                        "description": feature.get("description", ""),
                        "location": feature.get("location", {}),
                    }
                )
        return feature_list

    def _extract_subcellular_location(self, comments: list) -> list:
        """提取亚细胞定位"""
        locations = []
        for comment in comments:
            if comment.get("commentType") == "SUBCELLULAR LOCATION":
                for location in comment.get("subcellularLocations", []):
                    locations.append(
                        {
                            "location": location.get("location", {}).get("value", ""),
                            "topology": location.get("topology", {}).get("value", ""),
                        }
                    )
        return locations

    def _extract_interactions(self, cross_references: list) -> list:
        """提取蛋白质相互作用"""
        interactions = []
        for ref in cross_references:
            if ref.get("database") == "IntAct":
                interactions.append({"database": "IntAct", "id": ref.get("id", "")})
        return interactions


class KEGGClient:
    """KEGG API客户端 - 通路分析功能"""

    BASE_URL = "https://rest.kegg.jp/"

    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_pathway_list(self, organism: str = "hsa") -> dict[str, Any]:
        """获取生物体通路列表"""
        url = f"{self.BASE_URL}list/pathway/{organism}"

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {
                        "error": f"Pathway list fetch failed: HTTP {response.status}",
                        "suggestions": [
                            "检查生物体代码是否正确（如 hsa, mmu, rno）",
                            "稍后重试",
                            "检查网络连接",
                        ],
                    }

                text = await response.text(encoding="utf-8")
                pathways = {}

                for line in text.strip().split("\n"):
                    if line and "\t" in line:
                        pathway_id, pathway_name = line.split("\t", 1)
                        pathways[pathway_id] = pathway_name

                return {
                    "organism": organism,
                    "pathway_count": len(pathways),
                    "pathways": pathways,
                }
        except asyncio.TimeoutError:
            return {
                "error": "KEGG API 请求超时",
                "suggestions": ["稍后重试", "检查网络连接速度", "减少查询数据量"],
            }
        except Exception as e:
            return {
                "error": f"Pathway list fetch error: {str(e)}",
                "suggestions": ["检查网络连接", "稍后重试", "联系技术支持"],
            }

    async def get_gene_pathway_mapping(
        self, gene_list: list[str], organism: str
    ) -> dict[str, Any]:
        """获取基因-通路映射关系"""
        if not gene_list:
            return {"error": "基因列表为空", "organism": organism}

        gene_str = "+".join(gene_list)
        url = f"{self.BASE_URL}link/pathway/{organism}:{gene_str}"

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {
                        "error": f"Gene-pathway mapping fetch failed: HTTP {response.status}",
                        "organism": organism,
                        "gene_list": gene_list,
                        "suggestions": [
                            "检查基因ID格式是否正确",
                            "确认生物体代码是否支持",
                            "稍后重试",
                        ],
                    }

                text = await response.text(encoding="utf-8")
                gene_pathways = {}

                for line in text.strip().split("\n"):
                    if line and "\t" in line:
                        gene_id, pathway_id = line.split("\t", 1)

                        # 标准化基因ID
                        gene_id = self._normalize_gene_id(gene_id)

                        if gene_id not in gene_pathways:
                            gene_pathways[gene_id] = []
                        gene_pathways[gene_id].append(pathway_id)

                return {
                    "organism": organism,
                    "gene_count": len(gene_pathways),
                    "gene_pathways": gene_pathways,
                }
        except asyncio.TimeoutError:
            return {
                "error": "KEGG基因-通路映射请求超时",
                "organism": organism,
                "gene_list": gene_list,
                "suggestions": ["减少基因列表长度", "稍后重试", "检查网络连接"],
            }
        except Exception as e:
            return {
                "error": f"Gene-pathway mapping fetch error: {str(e)}",
                "organism": organism,
                "gene_list": gene_list,
                "suggestions": ["检查基因ID格式", "检查网络连接", "稍后重试"],
            }

    async def get_pathway_info(self, pathway_id: str) -> dict[str, Any]:
        """获取通路详细信息"""
        url = f"{self.BASE_URL}get/{pathway_id}"

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {
                        "error": f"Pathway info fetch failed: HTTP {response.status}"
                    }

                text = await response.text()
                return {"pathway_id": pathway_id, "data": text}
        except Exception as e:
            return {"error": f"Pathway info fetch error: {str(e)}"}

    def _normalize_gene_id(self, gene_id: str) -> str:
        """标准化基因ID格式"""
        # KEGG返回的基因ID格式可能是 organism:gene_id
        if ":" in gene_id:
            return gene_id.split(":", 1)[1]
        return gene_id
