#!/usr/bin/env python3
"""
查询执行器模块 - 统一处理所有查询的执行

协调各种API客户端执行不同类型的查询
"""

import asyncio
from typing import Any

from .clients import KEGGClient, NCBIClient, UniProtClient
from .ensembl_client import EnsemblClient
from .query_parser import ParsedQuery, QueryType


class QueryExecutor:
    """查询执行器 - 统一处理所有查询"""

    def __init__(self):
        self.ncbi_client = NCBIClient()
        self.uniprot_client = UniProtClient()
        self.ensembl_client = EnsemblClient()
        self.kegg_client = KEGGClient()

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
        elif parsed_query.type == QueryType.ORTHOLOG:
            return await self._execute_ortholog(params)
        elif parsed_query.type == QueryType.EVOLUTION:
            return await self._execute_evolution(params)
        elif parsed_query.type == QueryType.PATHWAY_ENRICHMENT:
            return await self._execute_pathway_enrichment(params)
        else:
            raise ValueError(f"Unsupported query type: {parsed_query.type}")

    async def _execute_info(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行信息查询"""
        gene_id = params["gene_id"]

        # 检查缓存
        cached = self.ncbi_client.get_cached_gene(gene_id)
        if cached:
            return {"gene_id": gene_id, "source": "cache", "data": cached}

        # 搜索基因
        async with self.ncbi_client as client:
            search_result = await client.search(gene_id, max_results=1)

            if not search_result["results"]:
                return {"gene_id": gene_id, "error": "Gene not found"}

            # 获取详细信息
            details = await client.fetch_details(search_result["results"])
            if details:
                uid = search_result["results"][0]
                gene_data = details.get(uid, {})
                return {"gene_id": gene_id, "source": "ncbi", "data": gene_data}
            else:
                return {"gene_id": gene_id, "error": "Failed to fetch details"}

    async def _execute_search(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行搜索查询"""
        term = params["term"]
        max_results = params.get("max_results", 20)

        async with self.ncbi_client as client:
            search_result = await client.search(term, max_results=max_results)

            if search_result["results"]:
                # 获取前几个基因的详细信息
                details = await client.fetch_details(search_result["results"][:10])
                processed_results = []

                for uid in search_result["results"]:
                    if uid in details:
                        gene_data = details[uid]
                        processed_results.append(
                            {
                                "uid": uid,
                                "summary": gene_data.get("summary", ""),
                                "name": gene_data.get("name", ""),
                                "chromosome": gene_data.get("chromosome", ""),
                                "map_location": gene_data.get("maplocation", ""),
                                "description": gene_data.get("description", ""),
                            }
                        )

                return {
                    "term": term,
                    "total_count": search_result["count"],
                    "results": processed_results,
                }
            else:
                return {"term": term, "total_count": 0, "results": []}

    async def _execute_region(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行区域查询"""
        chromosome = params["chromosome"]
        start = params["start"]
        end = params["end"]

        async with self.ncbi_client as client:
            result = await client.search_region(chromosome, start, end)
            return result

    async def _execute_batch(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行批量查询"""
        gene_ids = params["gene_ids"]

        results = {}

        # 检查缓存
        cached_genes = {}
        uncached_genes = []

        for gene_id in gene_ids:
            cached = self.ncbi_client.get_cached_gene(gene_id.strip())
            if cached:
                cached_genes[gene_id] = {
                    "gene_id": gene_id,
                    "source": "cache",
                    "data": cached,
                }
            else:
                uncached_genes.append(gene_id)

        # 批量查询未缓存的基因
        if uncached_genes:
            async with self.ncbi_client as client:
                # 并发搜索所有基因
                search_tasks = [
                    client.search(gene_id, max_results=1) for gene_id in uncached_genes
                ]
                search_results = await asyncio.gather(*search_tasks)

                # 收集所有有效的UID
                all_uids = []
                gene_to_uid = {}

                for i, gene_id in enumerate(uncached_genes):
                    search_result = search_results[i]
                    if search_result["results"]:
                        uid = search_result["results"][0]
                        all_uids.append(uid)
                        gene_to_uid[uid] = gene_id

                # 批量获取详细信息
                if all_uids:
                    details = await client.fetch_details(all_uids)

                    for uid, gene_id in gene_to_uid.items():
                        if uid in details:
                            results[gene_id] = {
                                "gene_id": gene_id,
                                "source": "ncbi",
                                "data": details[uid],
                            }
                        else:
                            results[gene_id] = {
                                "gene_id": gene_id,
                                "error": "Failed to fetch details",
                            }
                else:
                    for gene_id in uncached_genes:
                        results[gene_id] = {
                            "gene_id": gene_id,
                            "error": "Gene not found",
                        }

        # 合并缓存和查询结果
        all_results = {**cached_genes, **results}

        return {
            "batch_size": len(gene_ids),
            "successful": len([r for r in all_results.values() if "error" not in r]),
            "from_cache": len(cached_genes),
            "results": all_results,
        }

    async def _execute_protein(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行蛋白质查询"""
        protein_query = params["protein_query"]
        max_results = params.get("max_results", 20)
        organism = params.get("organism", "9606")

        async with self.uniprot_client as client:
            result = await client.search_proteins(
                protein_query, max_results=max_results, organism=organism
            )
            return result

    async def _execute_gene_protein(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行基因-蛋白质整合查询"""
        gene_query = params["gene_query"]
        max_results = params.get("max_results", 20)
        organism = params.get("organism", "9606")

        # 并发查询NCBI和UniProt
        async with (
            self.ncbi_client as ncbi_client,
            self.uniprot_client as uniprot_client,
        ):
            # NCBI基因查询
            ncbi_task = ncbi_client.search(gene_query, max_results=1)
            # UniProt蛋白质查询
            uniprot_task = uniprot_client.search_by_gene_exact(
                gene_query, organism, max_results
            )

            ncbi_result, uniprot_result = await asyncio.gather(ncbi_task, uniprot_task)

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
                    "organism": organism,
                },
            }

            return integrated_result

    async def _execute_ortholog(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行同源基因查询 - 使用Ensembl API"""
        gene_query = params["gene_query"]
        limit = params.get("limit", 50)
        target_species = params.get("target_species")

        try:
            # 处理目标物种参数
            target_species_list = None
            if target_species:
                if isinstance(target_species, str):
                    target_species_list = [target_species]
                elif isinstance(target_species, list):
                    target_species_list = target_species

            # 使用EnsemblClient查询
            async with self.ensembl_client as client:
                result = await client.search_orthologs(
                    gene_symbol=gene_query,
                    target_species=target_species_list,
                    limit=limit,
                )

            return {
                "query_type": "ortholog",
                "gene_query": gene_query,
                "result": result,
                "species_targeted": target_species is not None,
                "data_source": "Ensembl REST API",
                "success": result.get("success", False),
            }

        except Exception as e:
            return {
                "error": f"同源基因查询失败: {str(e)}",
                "query_type": "ortholog",
                "gene_query": gene_query,
                "suggestions": ["检查基因符号是否正确", "稍后重试", "检查网络连接"],
            }

    async def _execute_evolution(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行进化分析查询 - 使用Ensembl API"""
        evolution_query = params["evolution_query"]
        analysis_type = params.get("analysis_type", "comprehensive")

        try:
            # 使用EnsemblClient获取物种信息
            async with self.ensembl_client as client:
                # 获取支持物种列表
                species_result = await client.get_species_list()

                # 基于查询内容进行智能分析
                analysis_result = {
                    "query": evolution_query,
                    "analysis_type": analysis_type,
                    "available_species": species_result.get("species", [])[
                        :10
                    ],  # 前10个物种
                    "recommendations": self._generate_evolution_recommendations(
                        evolution_query
                    ),
                    "data_source": "Ensembl REST API",
                }

            return {
                "query_type": "evolution",
                "evolution_query": evolution_query,
                "result": analysis_result,
                "data_source": "Ensembl REST API",
            }

        except Exception as e:
            return {
                "error": f"进化分析查询失败: {str(e)}",
                "query_type": "evolution",
                "evolution_query": evolution_query,
                "suggestions": ["检查查询参数是否正确", "稍后重试", "检查网络连接"],
            }

    def _generate_evolution_recommendations(self, query: str) -> list[str]:
        """生成进化分析建议"""
        query_lower = query.lower()
        recommendations = []

        if "mammal" in query_lower or "vertebrate" in query_lower:
            recommendations.append(
                "Consider using level: Vertebrata for mammalian comparisons"
            )
        if "insect" in query_lower or "arthropod" in query_lower:
            recommendations.append(
                "Consider using level: Arthropoda for insect studies"
            )
        if "plant" in query_lower or "green plant" in query_lower:
            recommendations.append(
                "Consider using level: Viridiplantae for plant evolution"
            )
        if "fungi" in query_lower or "yeast" in query_lower:
            recommendations.append("Consider using level: Fungi for fungal comparisons")

        if not recommendations:
            recommendations.append(
                "Use level: Eukaryota for broad eukaryotic comparisons"
            )
            recommendations.append("Use level: Metazoa for animal-specific studies")

        return recommendations

    async def _execute_pathway_enrichment(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
        """执行通路富集分析查询"""
        from ..analysis.kegg_analysis import KEGGEnrichment
        from ..utils.validation import validate_parameters

        try:
            # 验证参数
            validated_params = validate_parameters(params)

            # 创建KEGG分析器
            async with KEGGEnrichment() as analyzer:
                # 执行通路富集分析
                result = await analyzer.analyze_pathways(
                    gene_list=validated_params["gene_list"],
                    organism=validated_params["organism"],
                    pvalue_threshold=validated_params["pvalue_threshold"],
                    min_gene_count=validated_params["min_gene_count"],
                )

            return {"query_type": "pathway_enrichment", "result": result}

        except Exception as e:
            return {
                "query_type": "pathway_enrichment",
                "error": f"Pathway enrichment analysis failed: {str(e)}",
                "params": params,
            }
