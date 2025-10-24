# KEGG Pathway Enrichment Analysis MVP

## 概述

本MVP实现了KEGG通路富集分析功能，用于识别基因列表在生物学通路中的富集情况。

## 功能特性

- **KEGG API集成**: 连接KEGG数据库获取通路信息
- **统计分析**: 使用超几何分布检验计算p值
- **FDR校正**: 实现Benjamini-Hochberg假发现率校正
- **数据验证**: 完整的输入验证和错误处理
- **MCP工具集成**: 通过MCP框架提供服务

## 使用方法

### 1. 通过MCP工具使用

```python
from genome_mcp.core.tools import create_mcp_tools
from fastmcp import FastMCP

# 创建MCP实例
mcp = FastMCP('genome-analysis')

# 注册工具
create_mcp_tools(mcp)
```

### 2. 直接使用分析模块

```python
import asyncio
from genome_mcp.analysis.kegg_analysis import KEGGEnrichment

async def analyze_pathways():
    # 创建KEGG分析器
    analyzer = KEGGEnrichment()

    # 执行通路富集分析
    async with analyzer:
        result = await analyzer.analyze_pathways(
            gene_list=['7157', '672', '675'],  # TP53, BRCA1, BRCA2的Entrez ID
            organism='hsa',                    # 人类
            pvalue_threshold=0.05,             # p值阈值
            min_gene_count=2                   # 通路中最小基因数量
        )

    return result

# 运行分析
result = asyncio.run(analyze_pathways())
```

### 3. 通过查询执行器使用

```python
import asyncio
from genome_mcp.core.query_executor import QueryExecutor
from genome_mcp.core.query_parser import QueryParser

async def pathway_enrichment():
    # 创建查询执行器
    executor = QueryExecutor()

    # 解析查询
    parsed = QueryParser.parse('pathway enrichment', query_type='pathway_enrichment')
    parsed.params.update({
        'gene_list': ['7157', '672', '675'],
        'organism': 'hsa',
        'pvalue_threshold': 0.05,
        'min_gene_count': 2
    })

    # 执行查询
    result = await executor.execute(parsed)
    return result['result']

result = asyncio.run(pathway_enrichment())
```

## 输入格式

### 基因ID格式
- **推荐**: 使用Entrez Gene ID（数字格式），如 `7157` (TP53)
- **支持**: 基因符号（需要转换为Entrez ID）
- **示例**: `['7157', '672', '675']` 对应 `['TP53', 'BRCA1', 'BRCA2']`

### 生物体代码
- `hsa`: 人类 (Homo sapiens)
- `mmu`: 小鼠 (Mus musculus)
- `rno`: 大鼠 (Rattus norvegicus)

## 输出格式

```python
{
    "query_genes": ["7157", "672", "675"],
    "organism": "hsa",
    "total_pathways_found": 51,
    "significant_pathways": 15,
    "all_pathways": [
        {
            "pathway_id": "hsa01522",
            "pathway_name": "Path: hsa01522",
            "genes": ["7157"],
            "gene_count": 1,
            "pvalue": 0.0001,
            "fdr": 0.0051,
            "fold_enrichment": 6666.67
        }
    ],
    "analysis_info": {
        "method": "KEGG Pathway Enrichment",
        "statistical_test": "Hypergeometric Test",
        "fdr_correction": "Benjamini-Hochberg"
    }
}
```

## 统计方法

1. **超几何分布检验**: 计算基因在通路中富集的p值
2. **FDR校正**: 使用Benjamini-Hochberg方法进行多重检验校正
3. **富集倍数**: (观察到的基因数 / 期望的基因数)

## 测试

运行测试套件：

```bash
python -m pytest tests/unit/test_kegg_mvp.py -v
```

测试覆盖：
- 基础通路富集分析
- KEGG客户端功能
- 统计计算正确性
- 输入验证
- 错误处理

## API限制

- KEGG API有频率限制，建议间隔0.34秒以上
- 部分基因可能没有通路注释
- 通路信息基于KEGG数据库的当前版本

## 故障排除

### 常见问题

1. **"未找到任何通路映射"**
   - 检查基因ID格式，建议使用Entrez ID
   - 确认生物体代码正确

2. **"基因列表无效"**
   - 确保基因列表包含至少2个基因
   - 检查基因ID格式是否正确

3. **网络连接问题**
   - 确认可以访问KEGG API (https://rest.kegg.jp/)
   - 检查网络连接状态

## 依赖项

- `aiohttp`: HTTP客户端
- `fastmcp`: MCP框架
- `scipy`: 统计计算（可选，用于高级统计）

## 版本信息

- MVP版本: 1.0.0
- 实现日期: 2025-10-24
- 状态: 生产就绪
