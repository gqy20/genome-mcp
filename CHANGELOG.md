# 更新日志

## [0.2.1] - 2024-10-24

### 🧬 UniProt 集成 - 多组学数据查询扩展

基于Linus Torvalds设计理念的重大架构优化，实现**简洁、实用、高效**的基因组数据访问。

### ✨ 新特性

- **智能查询系统**: 3个智能工具替代原有8个工具
  - `get_data()` - 统一数据获取接口
  - `advanced_query()` - 高级批量查询
  - `smart_search()` - 智能语义搜索

- **自动意图识别**: 无需手动选择工具类型
  - `"TP53"` → 自动识别为基因信息查询
  - `"chr17:7565097-7590856"` → 自动识别为区域搜索
  - `["TP53", "BRCA1"]` → 自动识别为批量查询
  - `"breast cancer genes"` → 自动识别为语义搜索

- **批量API优化**: 性能提升90%+
  - 批量查询从N次API调用优化为1次调用
  - 智能缓存常用基因信息
  - 连接复用减少网络开销

- **自然语言理解**: 支持语义搜索
  - `"breast cancer genes on chromosome 17"`
  - `"TP53 protein interactions"`
  - `"DNA repair related genes"`

### 🔄 向后兼容性

保持所有原有函数接口，确保现有代码无需修改：

```python
# 原有接口继续可用
from genome_mcp import get_gene_info, search_genes, batch_gene_info

# 新接口更强大
from genome_mcp import get_data, advanced_query, smart_search
```

### 📊 性能提升

| 指标 | v0.1.5 | v0.2.0 | 改进 |
|------|--------|--------|------|
| 工具数量 | 8个 | 3个 | ⬇️ 62.5% |
| API调用次数 | N次 | 1次 (批量) | ⬇️ 90%+ |
| 查询识别 | 手动 | 自动 | ⚡ 智能化 |
| 学习成本 | 高 | 低 | ➡️ 简化 |

### 🏗️ 架构变更

#### 核心组件

- **QueryParser**: 智能查询解析器
- **QueryExecutor**: 统一查询执行器
- **NCBIClient**: 优化的NCBI API客户端

#### 工具映射

| 原有工具 | 新工具 | 说明 |
|---------|--------|------|
| `get_gene_info()` | `get_data("TP53", query_type="info")` | 基因信息查询 |
| `search_genes()` | `get_data("cancer", query_type="search")` | 基因搜索 |
| `batch_gene_info()` | `get_data(["TP53","BRCA1"], query_type="batch")` | 批量查询 |
| `search_by_region()` | `get_data("chr17:1-1000", query_type="region")` | 区域搜索 |
| `get_gene_homologs()` | `smart_search("TP53 homologs")` | 同源体搜索 |

### 🧪 测试验证

所有功能100%通过测试：

- ✅ 模块导入正常
- ✅ 查询解析器智能识别
- ✅ 核心功能正常工作
- ✅ 向后兼容性保持
- ✅ API调用成功（TP53、癌症搜索等）

### 📝 代码统计

- **总文件数**: 9个核心文件
- **主文件**: `src/genome_mcp/main.py` (615行)
- **版本**: v0.2.0
- **依赖**: aiohttp, fastmcp (简化依赖)

### 🎯 设计理念

体现Linus Torvalds设计哲学：

1. **简洁至上**: 减少不必要的复杂性
2. **实用主义**: 解决实际问题而非过度工程化
3. **性能优先**: 优化而非抽象
4. **用户友好**: 智能化而非强制用户学习

### 🧬 UniProt 数据库集成

- **多组学数据查询**: 集成 UniProt API，实现基因-蛋白质完整数据链
- **新增数据类型**: `protein` (蛋白质查询) 和 `gene_protein` (整合查询)
- **智能识别**: 自动识别 UniProt 访问号 (如 P04637) 和蛋白质功能关键词
- **并发查询**: 同时查询 NCBI 和 UniProt，提供全面信息
- **跨物种支持**: 支持人类、小鼠、大鼠等多种模式生物查询

#### 新增查询示例

```python
# 蛋白质查询
get_data("P04637", data_type="protein")

# 基因-蛋白质整合查询
get_data("TP53", data_type="gene_protein")

# 蛋白质功能搜索
get_data("tumor suppressor", data_type="protein")

# 跨物种查询
get_data("TP53", species="mouse")
```

#### API 能力扩展

| 功能 | NCBI | UniProt | 整合后 |
|------|------|---------|--------|
| 基因基本信息 | ✅ | ❌ | ✅ |
| 蛋白质序列 | ❌ | ✅ | ✅ |
| 功能注释 | ⚠️ | ✅ | ✅ |
| 疾病关联 | ⚠️ | ✅ | ✅ |
| 结构域信息 | ❌ | ✅ | ✅ |
| GO 术语 | ❌ | ✅ | ✅ |
| 基因组位置 | ✅ | ❌ | ✅ |

### 🔮 未来计划

- v0.2.1: 扩展基因缓存数据库，增加蛋白质缓存
- v0.2.2: 增强自然语言理解能力
- v0.3.0: 支持更多基因组数据库 (如 Ensembl, RefSeq)

---

## [0.1.5] - 2024-09-15

### 📋 初始版本

- 8个基础MCP工具
- NCBI Gene数据库访问
- 基本搜索和查询功能
- MCP协议支持

---

*注：本版本遵循语义化版本控制 (Semantic Versioning)*