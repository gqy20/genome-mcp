# API快速参考

## 🟢 可用API快速参考

### KEGG API
```bash
# 基础URL
https://rest.kegg.jp/

# 常用端点
GET /list/pathway                    # 通路列表
GET /link/pathway/hsa:TP53          # 基因-通路关联
GET /find/genes/cancer              # 基因搜索
```

### STRING API
```bash
# 基础URL
https://string-db.org/api/

# 常用端点
GET /json/network?identifiers=TP53&species=9606
GET /json/functional_annotation?identifiers=TP53
GET /json/enrichment?identifiers=TP53&species=9606
```

### UniProt API
```bash
# 基础URL
https://rest.uniprot.org/uniprotkb/

# 常用端点
GET /P04637                         # 蛋白质信息
GET /P04637.fasta                   # FASTA序列
GET /search?query=organism_id:9606   # 高级搜索
```

### Ensembl API
```bash
# 基础URL
https://rest.ensembl.org/

# 常用端点
GET /lookup/id/ENSG00000141510
GET /homology/id/ENSG00000141510?type=orthologues
GET /overlap/region/human/17:7565097-7590856?feature=gene
```

---

## 🛠️ 推荐的MCP工具实现模板

```python
@mcp.tool()
async def kegg_pathway_analysis(
    gene_list: list[str],
    organism: str = "hsa"
) -> dict[str, Any]:
    """KEGG通路分析工具"""
    # 实现 KEGG API 调用
    pass

@mcp.tool()
async def string_network_analysis(
    proteins: list[str],
    species: int = 9606,
    confidence: float = 0.4
) -> dict[str, Any]:
    """STRING蛋白质互作网络分析"""
    # 实现 STRING API 调用
    pass

@mcp.tool()
async def ensembl_comparative_analysis(
    gene_id: str,
    target_species: list[str]
) -> dict[str, Any]:
    """Ensembl跨物种比较分析"""
    # 实现 Ensembl API 调用
    pass
```

---

## 📋 优先级建议

1. **立即实现**: KEGG, STRING, UniProt, Ensembl
2. **需要研究**: Reactome, QuickGO
3. **暂时避免**: BioGRID, RCSB PDB

---

*详细调研报告请参考：[bioinformatics_apis_research.md](./bioinformatics_apis_research.md)*
