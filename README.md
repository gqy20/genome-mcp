# Genome MCP 🧬

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/genome-mcp.svg)](https://badge.fury.io/py/genome-mcp)

高性能的模型上下文协议（MCP）服务器，用于基因组数据访问，使AI工具能够通过自然语言查询NCBI基因数据库。

## 功能特性

- **🤖 MCP集成**：通过模型上下文协议实现无缝AI工具集成
- **🧬 NCBI基因访问**：查询基因信息、搜索基因、批量操作
- **⚡ 异步架构**：使用aiohttp的高性能异步/等待架构
- **🛡️ 速率限制**：内置请求优化和缓存机制
- **🔒 类型安全**：完整的Pydantic模型和类型提示
- **🖥️ 命令行界面**：直接的数据库查询命令行工具
- **📦 现代Python**：使用uv进行快速的依赖管理

## 快速开始

### 安装

```bash
# 使用uv（推荐）
uv add genome-mcp

# 使用pip
pip install genome-mcp
```

### 命令行使用

```bash
# 查询基因信息
genome-mcp query 7157 --species human  # TP53基因

# 搜索基因
genome-mcp search "癌症" --species human

# 批量查询多个基因
genome-mcp batch 7157,7158,7159 --species human

# 启动MCP服务器
genome-mcp server
```

### Python API

```python
import asyncio
from genome_mcp.servers.ncbi.gene import NCBIGeneServer

async def main():
    server = NCBIGeneServer()
    result = await server.execute_request("get_gene_info", {"gene_id": "7157"})
    print(f"基因: {result['data']['name']}")

asyncio.run(main())
```

## AI工具集成

### Cherry Studio / Cursor 部署

1. **使用uvx安装Genome MCP**（推荐）：
   ```bash
   # 如果还未安装uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # 测试安装
   uvx genome-mcp --help
   ```

2. **在AI工具中配置MCP服务器**：

   **Cherry Studio：**
   - 打开设置 → MCP服务器
   - 添加新服务器，命令为：`uvx genome-mcp server`
   - 或使用下面的配置文件

   **Cursor：**
   - 在项目根目录创建 `.cursor/mcp.json`：
   ```json
   {
     "mcpServers": {
       "genome-mcp": {
         "command": "uvx",
         "args": ["genome-mcp", "server"],
         "env": {}
       }
     }
   }
   ```

### MCP配置

在项目根目录创建 `mcp.json`：

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "uvx",
      "args": ["genome-mcp", "server", "--server-name", "ncbi-gene"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    }
  }
}
```

## 配置

### 环境变量

```bash
export NCBI_API_KEY="你的_ncbi_api密钥"    # 可选：提高速率限制
export NCBI_EMAIL="你的邮箱@example.com"  # 某些操作需要
```

### 高级配置

创建 `~/.genome_mcp/config.json`：

```json
{
  "servers": {
    "ncbi_gene": {
      "rate_limit": {
        "requests_per_second": 3,
        "burst_limit": 10
      },
      "cache": {
        "enabled": true,
        "ttl": 3600
      }
    }
  }
}
```

## 开发

```bash
# 克隆仓库
git clone https://github.com/your-org/genome-mcp.git
cd genome-mcp

# 设置开发环境
uv sync --dev

# 运行测试
uv run pytest

# 代码质量检查
uv run black src/ tests/
uv run isort src/ tests/
uv run mypy src/
```

## API参考

| 命令 | 描述 | 示例 |
|---------|-------------|---------|
| `query <id>` | 根据ID获取基因 | `genome-mcp query 7157` |
| `search <term>` | 搜索基因 | `genome-mcp search 癌症` |
| `batch <ids>` | 批量查询 | `genome-mcp batch 7157,7158` |
| `server` | 启动MCP服务器 | `genome-mcp server` |

## 支持

- **问题反馈**：[GitHub Issues](https://github.com/your-org/genome-mcp/issues)
- **文档**： [API参考](docs/API_REFERENCE.md)
- **PyPI**： [genome-mcp](https://pypi.org/project/genome-mcp/)

## 许可证

MIT许可证 - 详见 [LICENSE](LICENSE) 文件