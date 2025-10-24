# Genome MCP

NCBI基因组数据服务器，通过MCP协议提供智能基因信息查询和搜索功能。

[![PyPI version](https://img.shields.io/pypi/v/genome-mcp.svg)](https://pypi.org/project/genome-mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/genome-mcp.svg)](https://pypi.org/project/genome-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 特性

- **智能查询解析**: 支持自然语言和结构化查询
- **批量数据获取**: 优化的批量查询，减少API调用
- **语义搜索**: 理解查询意图的智能搜索
- **多传输模式**: 支持STDIO、HTTP、SSE传输
- **异步处理**: 高性能异步架构
- **完整文档**: 详细的API文档和使用示例

## 安装

```bash
pip install genome-mcp
```

或使用 uv:

```bash
uv add genome-mcp
```

## 🛠️ MCP 接入配置

### Claude Desktop

编辑配置文件：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

或使用 uv 运行:

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

### Continue.dev

在 VS Code 的 Continue.dev 扩展配置中:

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "python",
      "args": ["-m", "genome_mcp"]
    }
  }
}
```

### Cursor (VS Code 扩展)

在 Cursor 设置中添加:

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "python",
      "args": ["-m", "genome_mcp"],
      "env": {
        "GENOME_MCP_LOG_LEVEL": "info"
      }
    }
  }
}
```

### Cline (Claude for VS Code)

在 Cline 设置文件中:

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "python",
      "args": ["-m", "genome_mcp"],
      "timeout": 30000
    }
  }
}
```

### 其他支持 MCP 的客户端

1. **Windsurf**: 使用与 Claude Desktop 相同的配置格式
2. **OpenHands**: 在 config.json 中添加服务器配置
3. **Custom MCP Client**: 参考下面的 Python 示例

### 自定义 MCP 客户端

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

## 🔧 API 功能

### 可用工具

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

### 使用示例

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

asyncio.run(main())
```

## 📋 JSON 响应格式

### get_data 响应示例

```json
{
  "success": true,
  "data": {
    "gene_info": {
      "uid": "7157",
      "name": "TP53",
      "description": "tumor protein p53",
      "status": "Gene",
      "chromosome": "17",
      "maplocation": "17p13.1",
      "genomicinfo": [
        {
          "chraccver": "GRCh38.p13",
          "chrstart": 7565097,
          "chrstop": 7590856
        }
      ]
    }
  },
  "query_info": {
    "query": "TP53",
    "query_type": "gene",
    "database": "gene"
  }
}
```

### smart_search 响应示例

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "uid": "7157",
        "name": "TP53",
        "description": "tumor protein p53"
      }
    ],
    "total_count": 1,
    "query_understanding": {
      "intent": "gene_search",
      "key_terms": ["tumor", "suppressor", "genes", "cancer"]
    }
  }
}
```

## 💻 命令行使用

```bash
# 启动 MCP 服务器 (stdio 模式)
python -m genome_mcp

# 或使用 uv
uv run -m genome_mcp

# HTTP 服务器模式
python -m genome_mcp --port 8080

# SSE 服务器模式
python -m genome_mcp --mode sse --port 8080

# 查看帮助
python -m genome_mcp --help

# 测试示例
python examples/mcp-client-example.py
```

传输模式：
- **stdio**: 标准输入输出，用于MCP客户端集成
- **http**: HTTP API服务器，用于Web集成
- **sse**: Server-Sent Events，用于实时数据流

## 🔍 MCP 协议调试

### 初始化请求

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": {"listChanged": true}
    },
    "clientInfo": {"name": "debug-client", "version": "1.0.0"}
  }
}
```

### 服务器响应

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {"listChanged": false}
    },
    "serverInfo": {
      "name": "Genome MCP",
      "version": "0.2.0"
    }
  }
}
```

### 工具调用示例

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_data",
    "arguments": {
      "query": "TP53",
      "query_type": "auto"
    }
  }
}
```

## 📁 配置文件

项目中包含以下配置文件模板：

- `examples/claude-desktop-config.json` - Claude Desktop 配置
- `mcp-config.json` - 通用 MCP 配置
- `examples/mcp-client-example.py` - 完整的 Python MCP 客户端示例
- `examples/usage_examples.py` - API 使用示例
- `examples/fastmcp_example.py` - FastMCP 框架示例

## 🔧 故障排除

### 常见问题

1. **导入错误**: 确保已安装依赖
   ```bash
   pip install aiohttp fastmcp
   ```

2. **网络错误**: 检查到 NCBI 的网络连接
   ```bash
   curl -I "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
   ```

3. **MCP 协议错误**: 确保使用正确的 JSON-RPC 2.0 格式
   - 消息必须以换行符结尾
   - 必须包含 `jsonrpc: "2.0"` 字段

4. **权限错误**: 确保有权限执行 Python 脚本

### 调试模式

启用详细日志:
```bash
GENOME_MCP_LOG_LEVEL=debug python -m genome_mcp
```

测试API功能:
```bash
python examples/mcp-client-example.py
```

### 性能优化

- 使用批量查询减少API调用
- 启用缓存机制
- 调整超时设置
- 使用适当的传输模式

## 📚 依赖

- `aiohttp>=3.8.0` - HTTP 客户端
- `fastmcp>=2.0.0` - MCP 协议支持
- Python >= 3.10

## 🏗️ 开发

```bash
git clone https://github.com/gqy20/genome-mcp
cd genome-mcp
pip install -e ".[dev]"
make test
make lint
```

### 开发命令

```bash
make install    # 安装开发依赖
make format     # 格式化代码
make lint       # 代码质量检查
make test       # 运行测试
make check      # 完整检查
make build      # 构建包
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

- 📖 [文档](https://github.com/gqy20/genome-mcp#readme)
- 🐛 [问题反馈](https://github.com/gqy20/genome-mcp/issues)
- 💬 [讨论](https://github.com/gqy20/genome-mcp/discussions)

---

**Genome MCP** - 让基因组数据访问更简单、更智能！