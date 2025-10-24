# 生物信息学API调研报告

## 📋 调研概述

本文档记录了对各大生物信息学数据库和API的深度调研结果，旨在为Genome MCP项目扩展提供可靠的数据源选择。

调研日期：2025年10月24日
调研方法：实际API连通性测试、功能性验证、数据格式分析

---

## 🟢 **可用API（推荐集成）**

### 1. KEGG API
**状态**: ✅ 完全可用
**基础URL**: `https://rest.kegg.jp/`
**数据格式**: 纯文本/制表符分隔
**使用限制**: 无明确限制，建议适度使用

#### 主要端点：
- `GET /list/pathway` - 获取通路列表
- `GET /link/pathway/[gene_list]` - 基因-通路关联
- `GET /find/[database]/[keyword]` - 关键词搜索

#### 测试结果：
```bash
# 测试成功
curl "https://rest.kegg.jp/list/pathway" | head -5
# 返回：map01100	Metabolic pathways
```

#### 推荐工具：
- KEGG通路富集分析
- 基因-通路映射查询
- 代谢网络分析

### 2. STRING数据库API
**状态**: ✅ 完全可用
**基础URL**: `https://string-db.org/api/`
**数据格式**: JSON
**使用限制**: 建议提供邮箱标识

#### 主要端点：
- `GET /json/network` - 蛋白质互作网络
- `GET /json/functional_annotation` - 功能注释
- `GET /json/interaction_partners` - 互作伙伴

#### 测试结果：
```bash
# 测试成功
curl "https://string-db.org/api/json/network?identifiers=TP53&species=9606"
# 返回：JSON格式的互作网络数据
```

#### 推荐工具：
- 蛋白质互作网络构建
- 功能富集分析
- 网络拓扑分析

### 3. UniProt REST API
**状态**: ✅ 完全可用
**基础URL**: `https://rest.uniprot.org/uniprotkb/`
**数据格式**: JSON/FASTA/XML
**使用限制**: 无明确限制

#### 主要端点：
- `GET /[accession]` - 蛋白质详细信息
- `GET /[accession].fasta` - FASTA序列
- `GET /search` - 高级搜索

#### 测试结果：
```bash
# 测试成功
curl "https://rest.uniprot.org/uniprotkb/P04637" -H "Accept: application/json"
# 返回：完整的蛋白质信息JSON
```

#### 推荐工具：
- 蛋白质功能注释
- 序列分析工具
- 跨物种同源蛋白查询

### 4. Ensembl REST API
**状态**: ✅ 完全可用
**基础URL**: `https://rest.ensembl.org/`
**数据格式**: JSON
**使用限制**: 每小时55,000请求

#### 主要端点：
- `GET /lookup/id/[gene_id]` - 基因信息查询
- `GET /homology/id/[gene_id]` - 同源基因分析
- `GET /overlap/region/[species]/[region]` - 区域重叠分析

#### 测试结果：
```bash
# 测试成功
curl "https://rest.ensembl.org/lookup/id/ENSG00000141510?content-type=application/json"
# 返回：TP53基因的详细信息
```

#### 推荐工具：
- 跨物种比较基因组学
- 基因结构分析
- 变异注释

### 5. EBI工具API
**状态**: ✅ 部分可用
**基础URL**: `https://www.ebi.ac.uk/Tools/services/rest/`
**数据格式**: XML/JSON
**使用限制**: 需要邮箱地址

#### 主要工具：
- `emboss_needle` - 序列比对
- `emboss_water` - 局部比对
- `clustalo` - 多序列比对

#### 测试结果：
```bash
# 部分测试成功
curl "https://www.ebi.ac.uk/Tools/services/rest/emboss_needle"
# 返回：工具描述XML
```

#### 推荐工具：
- 序列比对分析
- 系统发育分析
- 进化距离计算

---

## 🟡 **部分可用API（需要额外配置）**

### 1. Reactome ContentService
**状态**: ⚠️ 端点需要调整
**基础URL**: `https://reactome.org/ContentService/`
**数据格式**: JSON
**问题**: API端点与文档不符，需要进一步研究

#### 调研发现：
- 直接查询实体ID返回404
- 需要使用特定的查询语法
- 可能需要API密钥或特殊权限

### 2. QuickGO API
**状态**: ⚠️ 返回HTML而非JSON
**基础URL**: `https://www.ebi.ac.uk/QuickGO/api/`
**数据格式**: HTML (期望JSON)
**问题**: API可能已重构或需要特殊参数

#### 调研发现：
- 端点连通但返回HTML页面
- 可能需要不同的API版本或端点
- 建议查找官方最新文档

---

## 🔴 **不可用/有问题API（不推荐）**

### 1. BioGRID API
**状态**: ❌ 连接超时
**基础URL**: `https://webservice.biodiversitydata.se/`
**问题**: API端点可能已迁移或不存在

#### 调研发现：
- 多次尝试均连接超时
- 可能需要VPN或特殊网络配置
- 不建议在生产环境中使用

### 2. RCSB PDB搜索API
**状态**: ❌ 端点返回404
**基础URL**: `https://search.rcsb.org/rcsbsearch/v1/`
**问题**: API端点可能已更新

#### 调研发现：
- 搜索查询返回404错误
- 建议查找最新的API文档
- 可能有新的API版本

---

## 📊 **API性能对比**

| 数据库 | 响应速度 | 数据质量 | 文档质量 | 推荐指数 |
|--------|----------|----------|----------|----------|
| KEGG | 快 | 高 | 好 | ⭐⭐⭐⭐⭐ |
| STRING | 快 | 高 | 优秀 | ⭐⭐⭐⭐⭐ |
| UniProt | 中等 | 优秀 | 优秀 | ⭐⭐⭐⭐⭐ |
| Ensembl | 快 | 高 | 优秀 | ⭐⭐⭐⭐⭐ |
| EBI Tools | 中等 | 高 | 好 | ⭐⭐⭐⭐ |
| Reactome | - | - | - | ⭐⭐ |
| QuickGO | - | - | - | ⭐⭐ |
| BioGRID | - | - | - | ⭐ |
| RCSB PDB | - | - | - | ⭐ |

---

## 🛠️ **推荐的MCP工具扩展方案**

基于调研结果，建议按以下优先级实现新工具：

### 第一优先级（立即可实现）：

1. **KEGG通路分析工具**
   ```python
   @mcp.tool()
   async def kegg_pathway_enrichment(gene_list: list[str], organism: str = "hsa"):
       """KEGG通路富集分析"""
   ```

2. **STRING互作网络工具**
   ```python
   @mcp.tool()
   async def string_interaction_network(genes: list[str], species: int = 9606):
       """构建蛋白质互作网络"""
   ```

3. **Ensembl比较基因组学工具**
   ```python
   @mcp.tool()
   async def ensembl_homology_analysis(gene_id: str, target_species: list[str]):
       """同源基因分析"""
   ```

### 第二优先级（需要额外研究）：

4. **UniProt高级查询工具**
5. **EBI序列分析工具集成**

---

## 📝 **实现建议**

### 技术要点：
1. **异步处理**: 所有API调用都应使用异步模式
2. **错误处理**: 实现完善的超时和重试机制
3. **缓存策略**: 对于频繁查询的数据实现本地缓存
4. **速率限制**: 遵守各API的使用限制和最佳实践
5. **数据标准化**: 统一不同数据源的返回格式

### 配置管理：
```python
# 建议的API配置
API_CONFIG = {
    "kegg": {
        "base_url": "https://rest.kegg.jp/",
        "timeout": 30,
        "rate_limit": None
    },
    "string": {
        "base_url": "https://string-db.org/api/",
        "timeout": 30,
        "rate_limit": "requests_per_hour"
    },
    # ... 其他配置
}
```

---

## 🔄 **持续监控**

建议定期重新测试这些API的可用性，因为：
- API端点可能发生变化
- 使用政策可能更新
- 新的数据库和服务可能出现
- 现有服务可能升级或停用

---

*最后更新：2025年10月24日*
*调研工具：curl命令行测试*
*调研环境：Linux网络环境*
