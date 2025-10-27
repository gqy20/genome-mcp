#!/usr/bin/env python3
"""
Ensembl REST API客户端 - OrthoDB的完全替代品
专门针对Ensembl API优化，提供同源基因查询功能
"""

import json
from typing import Any

import aiohttp


class EnsemblClient:
    """Ensembl REST API客户端 - 专为基因组学分析优化"""

    def __init__(self):
        self.base_url = "https://rest.ensembl.org"
        self.session: aiohttp.ClientSession | None = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_orthologs(
        self,
        gene_symbol: str,
        target_species: list[str] = None,
        limit: int = 50,
        format_type: str = "full",
    ) -> dict[str, Any]:
        """
        搜索同源基因 - 核心功能，完全替代OrthoDB

        Args:
            gene_symbol: 基因符号 (如 TP53, BRCA1)
            target_species: 目标物种列表 (如 ["mus_musculus", "rattus_norvegicus"])
            limit: 返回结果数量限制
            format_type: 数据格式 ("full" 或 "condensed")

        Returns:
            包含同源基因信息的字典
        """
        if not self.session:
            raise RuntimeError("客户端未初始化，请使用 async with 语法")

        # 验证输入参数
        if not gene_symbol or not gene_symbol.strip():
            return self._create_gene_not_found_response(gene_symbol or "空字符串")

        try:
            # 构建Ensembl API查询 - 修复URL和参数
            url = f"{self.base_url}/homology/symbol/homo_sapiens/{gene_symbol}"
            headers = {"Content-Type": "application/json"}

            # 修复参数格式 - Ensembl API需要分号分隔的参数
            query_params = [f"format={format_type}", "type=orthologues"]

            # 注意：Ensembl API不支持target_species参数，需要在返回结果中过滤
            # 移除target_species参数，改为后处理过滤

            # 构建完整URL包含参数
            if query_params:
                url += "?" + ";".join(query_params)

            # 存储目标物种用于后续过滤
            self._target_species = target_species

            async with self.session.get(url, headers=headers) as response:
                if response.status == 400:
                    return self._create_gene_not_found_response(gene_symbol)
                elif response.status != 200:
                    return self._create_error_response(
                        gene_symbol, f"HTTP {response.status}"
                    )

                data = await response.json()
                return self._process_homology_data(data, gene_symbol, target_species)

        except aiohttp.ClientError as e:
            return self._create_error_response(gene_symbol, f"网络错误: {str(e)}")
        except json.JSONDecodeError as e:
            return self._create_error_response(gene_symbol, f"JSON解析错误: {str(e)}")
        except Exception as e:
            return self._create_error_response(gene_symbol, f"系统错误: {str(e)}")

    def _process_homology_data(
        self, data: dict[str, Any], gene_symbol: str, target_species: list[str]
    ) -> dict[str, Any]:
        """处理Ensembl同源基因数据"""
        orthologs = []

        # 获取存储的目标物种
        target_species = getattr(self, "_target_species", target_species)

        if (
            data.get("data")
            and isinstance(data["data"], list)
            and len(data["data"]) > 0
        ):
            homologies = data["data"][0].get("homologies", [])

            for homology in homologies:
                target = homology.get("target", {})

                # 如果指定了目标物种，进行过滤
                if target_species:
                    # 标准化物种名称格式进行比较
                    target_species_clean = set()
                    for species in target_species:
                        species_lower = species.lower()
                        if species_lower in ["human", "homo sapiens"]:
                            target_species_clean.add("homo_sapiens")
                        elif species_lower in ["mouse", "mus musculus"]:
                            target_species_clean.add("mus_musculus")
                        elif species_lower in ["rat", "rattus norvegicus"]:
                            target_species_clean.add("rattus_norvegicus")
                        elif species_lower in ["zebrafish", "danio rerio"]:
                            target_species_clean.add("danio_rerio")
                        else:
                            target_species_clean.add(species_lower.replace(" ", "_"))

                    ortholog_species = (
                        target.get("species", "").lower().replace(" ", "_")
                    )
                    if ortholog_species not in target_species_clean:
                        continue

                ortholog_record = {
                    "gene_id": target.get("id", "Unknown"),
                    "gene_symbol": target.get("symbol", "Unknown"),
                    "organism_name": target.get("species", "Unknown"),
                    "taxon_id": str(target.get("taxon_id", "Unknown")),
                    "protein_id": target.get("protein_id", "Unknown"),
                    "confidence": self._determine_confidence(homology),
                    "identity": homology.get("perc_id", 0),
                    "similarity": homology.get("perc_pos", 0),
                    "alignment_length": homology.get("alignment_length", 0),
                    "dnds_ratio": (
                        homology.get("dn_ds", {}).get("dnds_ratio", 0)
                        if homology.get("dn_ds")
                        else 0
                    ),
                    "description": f"Ensembl ortholog: {target.get('species', 'Unknown')} {target.get('symbol', 'Unknown')}",
                    "source_db": "Ensembl",
                    "method": "orthology",
                    "data_source": "Ensembl REST API",
                }

                orthologs.append(ortholog_record)

        return {
            "query_gene": gene_symbol,
            "target_species": target_species or ["all"],
            "orthologs": orthologs,
            "orthologs_count": len(orthologs),
            "data_source": "Ensembl REST API",
            "api_version": "v1",
            "query_timestamp": "2025-10-26",
            "success": len(orthologs) > 0,
        }

    def _determine_confidence(self, homology: dict[str, Any]) -> str:
        """确定同源基因的置信度"""
        if homology.get("is_high_confidence"):
            return "high"
        elif homology.get("target_species_tree_nw"):
            return "medium"
        else:
            return "low"

    def _create_gene_not_found_response(self, gene_symbol: str) -> dict[str, Any]:
        """创建基因不存在的专用错误响应"""
        return {
            "error": f"基因符号 '{gene_symbol}' 在Ensembl数据库中未找到",
            "query_gene": gene_symbol,
            "success": False,
            "data_source": "Ensembl REST API",
            "error_type": "gene_not_found",
            "suggestions": [
                f"检查 '{gene_symbol}' 的拼写是否正确",
                "尝试使用标准的基因符号格式（如 TP53, BRCA1）",
                "确认该基因在人类基因组中存在",
                "在Ensembl网站验证基因符号: https://www.ensembl.org/Homo_sapiens/Search",
            ],
            "help_resources": [
                {
                    "name": "HGNC基因命名委员会",
                    "url": "https://www.genenames.org/",
                    "description": "官方基因符号验证",
                },
                {
                    "name": "Ensembl基因搜索",
                    "url": f"https://www.ensembl.org/Homo_sapiens/Search?q={gene_symbol}",
                    "description": "直接搜索该基因",
                },
            ],
        }

    def _create_error_response(
        self, gene_symbol: str, error_msg: str
    ) -> dict[str, Any]:
        """创建错误响应"""
        return {
            "error": f"同源基因查询失败: {error_msg}",
            "query_gene": gene_symbol,
            "success": False,
            "data_source": "Ensembl REST API",
            "suggestions": [
                "检查基因符号是否正确",
                "检查网络连接",
                "稍后重试",
                "确认基因存在于Ensembl数据库中",
            ],
            "help_resources": [
                {
                    "name": "Ensembl REST API文档",
                    "url": "https://rest.ensembl.org/",
                    "description": "Ensembl API官方文档",
                },
                {
                    "name": "Ensembl基因搜索",
                    "url": "https://www.ensembl.org/Homo_sapiens/Search",
                    "description": "在Ensembl网站搜索基因",
                },
            ],
        }

    async def get_gene_info(
        self, gene_symbol: str, species: str = "homo_sapiens"
    ) -> dict[str, Any]:
        """获取基因基本信息"""
        if not self.session:
            raise RuntimeError("客户端未初始化，请使用 async with 语法")

        try:
            url = f"{self.base_url}/lookup/symbol/{species}/{gene_symbol}"
            headers = {"Content-Type": "application/json"}

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Gene not found: {gene_symbol} in {species}"}

        except Exception as e:
            return {"error": f"Gene lookup failed: {str(e)}"}

    async def get_species_list(self) -> dict[str, Any]:
        """获取支持的物种列表"""
        if not self.session:
            raise RuntimeError("客户端未初始化，请使用 async with 语法")

        try:
            url = f"{self.base_url}/info/species"
            headers = {"Content-Type": "application/json"}

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "error": f"Failed to get species list: HTTP {response.status}"
                    }

        except Exception as e:
            return {"error": f"Species lookup failed: {str(e)}"}

    async def batch_search_homologs(
        self, gene_symbols: list[str], target_species: list[str] = None
    ) -> dict[str, Any]:
        """批量搜索同源基因"""
        results = {}
        successful_queries = 0
        failed_queries = 0

        for gene_symbol in gene_symbols:
            result = await self.search_orthologs(gene_symbol, target_species)
            results[gene_symbol] = result

            if result.get("success", False):
                successful_queries += 1
            else:
                failed_queries += 1

        return {
            "batch_results": results,
            "summary": {
                "total_genes": len(gene_symbols),
                "successful_queries": successful_queries,
                "failed_queries": failed_queries,
                "success_rate": f"{(successful_queries / len(gene_symbols) * 100):.1f}%",
            },
            "data_source": "Ensembl REST API",
        }

    async def get_phylogenetic_profile(
        self, gene_symbols: list[str], species_set: list[str] = None
    ) -> dict[str, Any]:
        """构建系统发育图谱 - 替代OrthoDB的功能"""
        if species_set is None:
            # 默认常用模式生物
            species_set = [
                "homo_sapiens",
                "mus_musculus",
                "rattus_norvegicus",
                "danio_rerio",
                "drosophila_melanogaster",
                "caenorhabditis_elegans",
                "arabidopsis_thaliana",
                "saccharomyces_cerevisiae",
            ]

        # 批量查询同源基因
        batch_result = await self.batch_search_homologs(gene_symbols)

        # 构建存在/缺失矩阵
        presence_matrix = {}
        for gene_symbol, gene_result in batch_result["batch_results"].items():
            if gene_result.get("success", False):
                orthologs = gene_result.get("orthologs", [])
                present_species = set()

                for ortholog in orthologs:
                    species_name = (
                        ortholog.get("organism_name", "").lower().replace(" ", "_")
                    )
                    present_species.add(species_name)

                gene_row = {}
                for species in species_set:
                    species_key = species.lower().replace(" ", "_")
                    gene_row[species] = species_key in present_species

                presence_matrix[gene_symbol] = gene_row
            else:
                # 基因查询失败的情况
                gene_row = {}
                for species in species_set:
                    gene_row[species] = False
                presence_matrix[gene_symbol] = gene_row

        return {
            "gene_symbols": gene_symbols,
            "species_set": species_set,
            "presence_matrix": presence_matrix,
            "summary": {
                "total_genes": len(gene_symbols),
                "total_species": len(species_set),
                "successful_queries": batch_result["summary"]["successful_queries"],
                "failed_queries": batch_result["summary"]["failed_queries"],
            },
            "data_source": "Ensembl REST API",
            "timestamp": "2025-10-26",
        }
