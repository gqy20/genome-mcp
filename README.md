# Genome MCP

🧬 智能基因组数据服务器 - 通过MCP协议提供高质量的基因信息查询、同源基因分析和进化研究功能。

[![PyPI version](https://img.shields.io/pypi/v/genome-mcp.svg)](https://pypi.org/project/genome-mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/genome-mcp.svg)](https://pypi.org/project/genome-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-42%2F42-passing-brightgreen.svg)](https://github.com/your-repo/genome-mcp)

## 1. 🚀 核心特性

- **🧬 基因信息查询**: 基于NCBI Gene数据库的准确基因信息
- **🔄 同源基因分析**: 基于Ensembl API的跨物种同源基因查询（253+ TP53同源基因）
- **🧬 进化分析**: 系统发育关系构建和保守性分析
- **🔍 语义搜索**: 理解查询意图的智能搜索功能
- **📊 批量处理**: 优化的并发查询，支持大规模数据分析
- **🌐 多传输模式**: 支持STDIO、HTTP、SSE传输协议
- **⚡ 异步架构**: 高性能异步处理架构
- **🔬 科学可靠**: 基于权威数据库，无模拟数据，完全科学可信

## 2. 安装

推荐使用现代化的 [uv](https://github.com/astral-sh/uv) 包管理器以获得更快的安装速度：

```bash
# 使用uvx直接运行（推荐）
uvx genome-mcp

# 或添加到项目
uv add genome-mcp
```

传统方式安装：

```bash
pip install genome-mcp
```

## 3. 🛠️ MCP 接入配置

### 3.1 Claude Desktop

编辑配置文件：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

推荐使用 uvx 运行:

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "uvx",
      "args": ["genome-mcp"],
      "env": {}
    }
  }
}
```

或使用传统方式:

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "python",
      "args": ["-m", "genome_mcp"],
      "env": {}
    }
  }
}
```

或使用 uv run:

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "uv",
      "args": ["run", "-m", "genome_mcp"],
      "env": {}
    }
  }
}
```

### 3.2 Continue.dev

在 VS Code 的 Continue.dev 扩展配置中:

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "uvx",
      "args": ["genome-mcp"]
    }
  }
}
```

### 3.3 Cursor (VS Code 扩展)

在 Cursor 设置中添加:

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "uvx",
      "args": ["genome-mcp"],
      "env": {
        "GENOME_MCP_LOG_LEVEL": "info"
      }
    }
  }
}
```

### 3.4 Cline (Claude for VS Code)

在 Cline 设置文件中:

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "uvx",
      "args": ["genome-mcp"],
      "timeout": 30000
    }
  }
}
```

### 3.5 其他支持 MCP 的客户端

1. **Windsurf**: 使用与 Claude Desktop 相同的配置格式
2. **OpenHands**: 在 config.json 中添加服务器配置
3. **Custom MCP Client**: 参考下面的 Python 示例

### 3.6 自定义 MCP 客户端

使用 stdio 传输:

```python
import subprocess
import json

# 启动 MCP 服务器
process = subprocess.Popen(
    ["python", "-m", "genome_mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# 发送初始化消息
init_message = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
}

process.stdin.write(json.dumps(init_message) + "\n")
response = process.stdout.readline()
print("Server response:", response)
```

## 4. 🔧 API 功能

### 4.1 可用工具

1. **get_data** - 智能数据获取
   - 支持基因符号、ID、区域搜索、同源基因查询
   - 自动类型识别和查询优化
   - 批量查询支持

2. **advanced_query** - 高级批量查询
   - 复杂查询条件组合
   - 批量处理优化
   - 自定义输出格式

3. **smart_search** - 语义搜索
   - 自然语言查询理解
   - 智能结果排序
   - 上下文感知搜索

4. **kegg_pathway_enrichment_tool** - KEGG通路富集分析 🆕
   - 基因列表在KEGG通路中的富集分析
   - 超几何分布检验计算统计显著性
   - FDR多重检验校正
   - 支持人类、小鼠、大鼠等多种模式生物

### 4.2 使用示例

```python
import asyncio
from genome_mcp import get_data, advanced_query, smart_search

async def main():
    # 获取基因信息
    gene_info = await get_data("TP53")
    print("Gene info:", gene_info)

    # 区域搜索
    region_data = await get_data("chr17:7565097-7590856", query_type="region")
    print("Region data:", region_data)

    # 批量查询
    batch_results = await get_data(["TP53", "BRCA1", "EGFR"], query_type="gene")
    print("Batch results:", batch_results)

    # 语义搜索
    search_results = await smart_search("tumor suppressor genes involved in cancer")
    print("Search results:", search_results)

    # 高级查询
    advanced_results = await advanced_query(
        query="cancer genes",
        query_type="search",
        database="gene",
        max_results=20
    )
    print("Advanced results:", advanced_results)

    # KEGG通路富集分析
    kegg_results = await kegg_pathway_enrichment_tool(
        gene_list=["7157", "672", "675"],  # TP53, BRCA1, BRCA2的Entrez ID
        organism="hsa",
        pvalue_threshold=0.05,
        min_gene_count=2
    )
    print("KEGG enrichment results:", kegg_results)

asyncio.run(main())
```

## 5. 📋 响应格式

所有API响应都遵循统一的JSON格式，包含 `success`、`data` 和 `query_info` 字段。

示例响应：
```json
{
  "success": true,
  "data": {
    "gene_info": {
      "uid": "7157",
      "name": "TP53",
      "description": "tumor protein p53"
    }
  },
  "query_info": {
    "query": "TP53",
    "query_type": "gene"
  }
}
```

## 6. 💻 命令行使用

```bash
# 直接运行（推荐）
uvx genome-mcp

# 开发模式运行
uv run -m genome_mcp

# HTTP 服务器模式
uv run -m genome_mcp --port 8080

# 查看帮助
uv run -m genome_mcp --help
```


## 7. 📋 更新日志

详细的版本更新记录请查看 [CHANGELOG.md](CHANGELOG.md)

## 8. 📚 依赖

详细的依赖信息和版本要求请查看 [pyproject.toml](pyproject.toml)

**Python 版本要求**：>= 3.11

## 9. 🏗️ 开发

```bash
git clone https://github.com/gqy20/genome-mcp
cd genome-mcp
pip install -e ".[dev]"
make test
make lint
```

### 9.1 开发命令

```bash
make install    # 安装开发依赖
make format     # 格式化代码
make lint       # 代码质量检查
make test       # 运行测试
make check      # 完整检查
make build      # 构建包
```

## 10. 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

© 2025 [gqy20](https://github.com/gqy20)

## 11. 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 12. 📞 支持

- 📖 [文档](https://github.com/gqy20/genome-mcp#readme)
- 🧬 [Glama MCP服务器](https://glama.ai/mcp/servers/@gqy20/genome-mcp)
- 🐛 [问题反馈](https://github.com/gqy20/genome-mcp/issues)
- 💬 [讨论](https://github.com/gqy20/genome-mcp/discussions)

---

**Genome MCP** - 让基因组数据访问更简单、更智能！
