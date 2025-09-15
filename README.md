# Genome MCP - 基因组数据模型上下文协议服务器

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Publish](https://github.com/gqy20/genome-mcp/workflows/Publish/badge.svg)](https://github.com/gqy20/genome-mcp/actions/workflows/publish.yml)
[![Code Quality](https://github.com/gqy20/genome-mcp/workflows/Quality/badge.svg)](https://github.com/gqy20/genome-mcp/actions/workflows/quality.yml)
[![PyPI version](https://badge.fury.io/py/genome-mcp.svg)](https://badge.fury.io/py/genome-mcp)

一个基于模型上下文协议（MCP）的基因组数据服务器，通过标准化API接口提供对基因组数据库的统一访问。采用异步架构构建，专为AI工具集成而设计，使用FastMCP框架实现。

## 功能特性

- **MCP服务器架构**：基于模型上下文协议构建，实现AI工具无缝集成
- **NCBI数据库集成**：通过EUtils API完全访问NCBI Gene数据库
- **异步高性能**：采用高性能的async/await架构
- **限流与缓存**：内置请求优化和响应缓存机制
- **类型安全**：完整的类型提示和Pydantic模型
- **FastMCP框架**：基于FastMCP实现标准化的MCP协议
- **现代Python**：使用uv进行依赖管理和现代打包

## 安装

### 使用uv（推荐）

```bash
# 使用uv安装
uv add genome-mcp

# 或直接运行无需安装
uv run genome-mcp --help
```

### 使用pip

```bash
pip install genome-mcp
```

## 快速开始

### 作为MCP服务器运行

```bash
# 作为stdio MCP服务器运行（适用于AI工具如Claude Desktop）
genome-mcp --transport stdio

# 作为SSE服务器运行（适用于Web应用）
genome-mcp --transport sse --host localhost --port 8080

# 作为Streamable HTTP服务器运行（适用于API集成）
genome-mcp --transport streamable-http --host localhost --port 8080
```

### Python API

```python
import asyncio
from genome_mcp.main import get_gene_info, search_genes

async def main():
    # 获取基因信息
    gene_info = await get_gene_info("7157")  # TP53
    print(f"基因: {gene_info['info']['name']}")
    print(f"描述: {gene_info['info']['description']}")
    
    # 搜索基因
    search_results = await search_genes("cancer", species="human")
    print(f"找到 {len(search_results['results'])} 个基因")

if __name__ == "__main__":
    asyncio.run(main())
```

## 配置MCP集成

### 传输模式选择

Genome MCP支持三种传输模式，每种模式适用于不同的使用场景：

1. **STDIO模式**：标准输入输出模式，适用于AI工具如Claude Desktop
2. **SSE模式**：Server-Sent Events模式，适用于Web应用，访问地址：`http://localhost:8080/sse`
3. **Streamable HTTP模式**：流式HTTP模式，适用于API集成，访问地址：`http://localhost:8080/mcp`

### 配置方式

根据您的使用场景选择相应的配置方式：

#### 方式一：STDIO模式（推荐用于AI工具）

适用于Claude Desktop、Cherry Studio等AI工具。

**Claude Desktop配置：**
```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "uvx",
      "args": ["genome-mcp"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    }
  }
}
```

**Cherry Studio配置：**
```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "uvx",
      "args": ["genome-mcp", "stdio"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    }
  }
}
```

**手动运行：**
```bash
genome-mcp --transport stdio
```

#### 方式二：SSE模式（推荐用于Web应用）

适用于Web应用和浏览器端集成。

**Claude Desktop配置：**
```json
{
  "mcpServers": {
    "genome-mcp-sse": {
      "command": "uvx",
      "args": ["genome-mcp", "--transport", "sse", "--host", "localhost", "--port", "8080"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    }
  }
}
```

**Cherry Studio配置：**
```json
{
  "mcpServers": {
    "genome-mcp-sse": {
      "command": "uvx",
      "args": ["genome-mcp", "--transport", "sse", "--host", "localhost", "--port", "8080"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    }
  }
}
```

**手动运行：**
```bash
genome-mcp --transport sse --host localhost --port 8080
```

**Web访问：**
```
http://localhost:8080/sse
```

#### 方式三：Streamable HTTP模式（推荐用于API集成）

适用于API集成和微服务架构。

**Claude Desktop配置：**
```json
{
  "mcpServers": {
    "genome-mcp-http": {
      "command": "uvx",
      "args": ["genome-mcp", "--transport", "streamable-http", "--host", "localhost", "--port", "8080"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    }
  }
}
```

**Cherry Studio配置：**
```json
{
  "mcpServers": {
    "genome-mcp-http": {
      "command": "uvx",
      "args": ["genome-mcp", "--transport", "streamable-http", "--host", "localhost", "--port", "8080"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    }
  }
}
```

**手动运行：**
```bash
genome-mcp --transport streamable-http --host localhost --port 8080
```

**API访问：**
```
http://localhost:8080/mcp
```

### 完整配置示例

如果您需要同时使用多种传输模式，可以使用以下完整配置：

```json
{
  "mcpServers": {
    "genome-mcp": {
      "command": "uvx",
      "args": ["genome-mcp"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    },
    "genome-mcp-sse": {
      "command": "uvx",
      "args": ["genome-mcp", "--transport", "sse", "--host", "localhost", "--port", "8080"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    },
    "genome-mcp-http": {
      "command": "uvx",
      "args": ["genome-mcp", "--transport", "streamable-http", "--host", "localhost", "--port", "8080"],
      "env": {
        "NCBI_API_KEY": "${NCBI_API_KEY}",
        "NCBI_EMAIL": "${NCBI_EMAIL}"
      }
    }
  }
}
```

### 环境变量

```bash
# NCBI API密钥（可选但推荐，以获得更高的请求限制）
export NCBI_API_KEY="your_ncbi_api_key"

# NCBI API邮箱（某些操作必需）
export NCBI_EMAIL="your_email@example.com"
```

### 项目配置

项目包含一个综合配置文件（`project_config.json`），定义了：

- 服务器设置和功能
- 限流和缓存配置
- 日志和监控设置
- 开发和部署选项

### 配置文件

在 `~/.genome_mcp/config.json` 创建配置文件：

```json
{
  "servers": {
    "ncbi_gene": {
      "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
      "rate_limit": {
        "requests_per_second": 3,
        "burst_limit": 10
      },
      "cache": {
        "enabled": true,
        "ttl": 3600
      }
    }
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

## 开发

### 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/gqy20/genome-mcp.git
cd genome-mcp

# 使用uv安装
uv sync --dev

# 安装pre-commit钩子
uv run pre-commit install
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行覆盖率测试
uv run pytest --cov=src --cov-report=html

# 运行特定测试文件
uv run pytest tests/test_ncbi_gene_server.py
```

### 代码质量

```bash
# 格式化代码
uv run black src/ tests/

# 排序导入
uv run isort src/ tests/

# 类型检查
uv run mypy src/

# 代码检查
uv run ruff check src/ tests/
```

## 项目结构

```
genome-mcp/
  main.py                  # FastMCP服务器入口点
  src/                     # 源代码
    servers/               # MCP服务器实现
      base.py            # 基础MCP服务器类
      ncbi/              # NCBI服务器实现
        gene.py         # NCBI Gene服务器
    configuration.py       # 配置管理
    http_utils/            # HTTP工具
    data/                  # 数据处理
    core/                  # 核心工具
    exceptions.py          # 异常定义
  tests/                   # 测试代码
  docs/                    # 文档
  examples/               # 示例代码
  .github/                # GitHub Actions工作流
  project_config.json      # 项目配置
```

## 架构

### FastMCP服务器架构

- **FastMCP框架**：基于FastMCP框架实现MCP协议
- **NCBIGeneServer**：NCBI Gene数据库访问实现
- **MCP工具**：将基因组数据函数暴露为MCP工具
- **异步设计**：完全的async/await支持以获得高性能
- **限流**：使用令牌桶算法的内置请求限流
- **缓存**：可选的响应缓存以提高性能
- **错误处理**：全面的错误处理和日志记录

### 核心组件

- **main.py**：带有工具装饰器的FastMCP服务器入口点
- **NCBIGeneServer**：NCBI Gene数据库访问实现
- **MCP传输**：支持stdio、SSE和Streamable HTTP传输
- **请求执行**：支持单个和批量请求
- **配置管理**：基于JSON的配置系统

## 贡献

我们欢迎贡献！详情请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目采用MIT许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 引用

如果您在研究中使用Genome MCP，请引用：

```bibtex
@software{genome_mcp,
  title={Genome MCP: Model Context Protocol Server for Genomic Data},
  author={gqy20},
  year={2025},
  url={https://github.com/gqy20/genome-mcp}
}
```

## 支持

- **文档**：[https://github.com/gqy20/genome-mcp#readme](https://github.com/gqy20/genome-mcp#readme)
- **问题**：[https://github.com/gqy20/genome-mcp/issues](https://github.com/gqy20/genome-mcp/issues)
- **讨论**：[https://github.com/gqy20/genome-mcp/discussions](https://github.com/gqy20/genome-mcp/discussions)

## 致谢

- [NCBI](https://www.ncbi.nlm.nih.gov/) 提供全面的基因组数据库
- [Model Context Protocol](https://modelcontextprotocol.io/) 实现AI工具集成
- [FastMCP](https://github.com/gofastmcp/fastmcp) 提供MCP框架实现
- [uv](https://github.com/astral-sh/uv) 提供现代Python包管理