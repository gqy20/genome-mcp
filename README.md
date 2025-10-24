# Genome MCP

NCBI基因组数据服务器，通过MCP协议提供基因信息查询和搜索功能。

## 安装

```bash
pip install genome-mcp
```

## MCP 接入配置

### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) 或 `AppData\Roaming\Claude\claude_desktop_config.json` (Windows):

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

## API 功能

### 可用工具

1. **get_gene_info** - 获取基因详细信息
   - 输入: `gene_id` (字符串) - 基因符号或ID
   - 输出: 包含基因信息的字典

2. **search_genes** - 搜索基因
   - 输入: `query` (字符串) - 搜索关键词
   - 输入: `max_results` (整数, 可选) - 最大结果数, 默认10
   - 输出: 基因ID列表

### JSON 响应格式

#### get_gene_info 响应示例

```json
{
  "gene_id": "TP53",
  "uid": "7157",
  "summary": {
    "uid": "7157",
    "name": "TP53",
    "description": "tumor protein p53",
    "status": "Gene",
    "otherinfo": [
      "This gene encodes tumor protein p53, which responds to diverse cellular stresses"
    ],
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
}
```

#### search_genes 响应示例

```json
[
  "7157",
  "7158",
  "7159"
]
```

## 直接 API 使用

```python
import asyncio
from genome_mcp import get_gene_info, search_genes

async def main():
    # 获取基因信息
    gene_info = await get_gene_info("TP53")
    print("Gene info:", gene_info)

    # 搜索基因
    search_results = await search_genes("cancer")
    print("Search results:", search_results)

asyncio.run(main())
```

## 命令行使用

```bash
# 启动 MCP 服务器 (stdio 模式)
python -m genome_mcp

# 或使用 uv
uv run -m genome_mcp

# 快速测试
python examples/mcp-client-example.py

# 基础功能测试
python test_mcp.py
```

## MCP 协议调试

### 调试消息示例

初始化请求:
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

服务器响应:
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

工具列表请求:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

工具调用示例:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_gene_info",
    "arguments": {
      "gene_id": "TP53"
    }
  }
}
```

## 配置文件示例

项目中包含以下配置文件模板:

- `examples/claude-desktop-config.json` - Claude Desktop 配置
- `mcp-config.json` - 通用 MCP 配置
- `examples/mcp-client-example.py` - 完整的 Python MCP 客户端示例

## 故障排除

### 常见问题

1. **导入错误**: 确保已安装依赖 `aiohttp` 和 `fastmcp`
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

检查服务器状态:
```bash
python -c "from genome_mcp import mcp; print('MCP server initialized')"
```

测试API功能:
```bash
python examples/mcp-client-example.py
```

## 依赖

- `aiohttp>=3.8.0` - HTTP 客户端
- `fastmcp>=2.0.0` - MCP 协议支持
- Python >= 3.10

## 开发

```bash
git clone https://github.com/gqy20/genome-mcp
cd genome-mcp
pip install -e .
pytest
```

MIT License