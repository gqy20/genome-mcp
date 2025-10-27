# Genome MCP 使用示例

## 📋 概述

Genome MCP v0.2.3 支持三种传输模式：STDIO、HTTP 和 SSE，适用于不同的使用场景。

## 🚀 启动模式

### 1. STDIO 模式（默认）

适用于本地 MCP 客户端，如 Claude Desktop。

```bash
# 基本启动
python -m genome_mcp

# 或使用 uv
uv run -m genome_mcp
```

**特点**：
- 🔒 仅本地访问
- 📝 标准 JSON-RPC 通信
- 🎯 Claude Desktop 推荐

### 2. HTTP 模式

适用于 Web 客户端和远程访问。

```bash
# 本地访问（127.0.0.1）
python -m genome_mcp --mode http --port 8080

# 外部访问（0.0.0.0）- 适用于 Docker 和云部署
python -m genome_mcp --mode http --port 8080 --host 0.0.0.0

# 简化写法（指定端口自动使用 HTTP 模式）
python -m genome_mcp --port 8080
```

**特点**：
- 🌐 支持远程访问
- 🔄 RESTful API
- 📊 便于调试和测试

### 3. SSE 模式

适用于实时通信场景。

```bash
python -m genome_mcp --mode sse --port 8080
```

**特点**：
- ⚡ 实时双向通信
- 📡 Server-Sent Events
- 🔄 自动重连支持

## 🔧 命令行参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--help` | `-h` | 显示帮助信息 | `--help` |
| `--version` | `-v` | 显示版本号 | `--version` |
| `--port` | `-p` | 指定端口号 | `--port 8080` |
| `--host` | | 指定绑定地址 | `--host 0.0.0.0` |
| `--mode` | `-m` | 传输模式 | `--mode http` |

## 🌐 网络配置

### 本地访问（默认）
```bash
python -m genome_mcp --port 8080
# 服务器地址: http://127.0.0.1:8080/mcp
```

### 外部访问
```bash
python -m genome_mcp --port 8080 --host 0.0.0.0
# 服务器地址: http://0.0.0.0:8080/mcp
# 允许局域网和外部访问
```

## 📝 使用示例

### Claude Desktop 配置

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

### Docker 部署

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install genome-mcp
EXPOSE 8080
CMD ["python", "-m", "genome_mcp", "--mode", "http", "--port", "8080", "--host", "0.0.0.0"]
```

### 云服务部署

```bash
# 启动服务器
python -m genome_mcp --mode http --port 8080 --host 0.0.0.0

# 配置反向代理（nginx）
server {
    listen 80;
    server_name your-domain.com;

    location /mcp {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🛠️ 客户端连接

### HTTP 客户端示例

```python
import aiohttp
import json

async def connect_mcp():
    url = "http://127.0.0.1:8080/mcp"

    async with aiohttp.ClientSession() as session:
        # 初始化
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }

        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json"
        }

        async with session.post(url, headers=headers, json=init_request) as response:
            session_id = response.headers.get('mcp-session-id')
            print(f"会话ID: {session_id}")

            # 使用 session_id 进行后续请求
            if session_id:
                headers["mcp-session-id"] = session_id

                # 获取工具列表
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }

                async with session.post(url, headers=headers, json=tools_request) as tools_response:
                    async for line in tools_response.content:
                        if line.startswith(b'data: '):
                            data = json.loads(line[6:].decode())
                            print("工具列表:", data)
                            break
```

## 🧬 可用工具

1. **get_data** - 智能数据获取（基因、蛋白质、区域、同源基因）
2. **advanced_query** - 高级批量查询
3. **smart_search** - 语义搜索
4. **analyze_gene_evolution_tool** - 基因进化分析
5. **build_phylogenetic_profile_tool** - 系统发育图谱构建
6. **kegg_pathway_enrichment_tool** - KEGG通路富集分析

## 📞 获取帮助

```bash
# 显示完整帮助
python -m genome_mcp --help

# 显示版本信息
python -m genome_mcp --version

# 查看工具列表
python -m genome_mcp --help | grep -A 20 "传输模式说明"
```

## 🔍 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 更换端口
   python -m genome_mcp --port 8081
   ```

2. **外部访问失败**
   ```bash
   # 检查防火墙设置
   sudo ufw allow 8080

   # 使用 0.0.0.0 绑定
   python -m genome_mcp --port 8080 --host 0.0.0.0
   ```

3. **Docker 部署问题**
   ```bash
   # 确保暴露端口
   docker run -p 8080:8080 genome-mcp

   # 健康检查
   curl http://localhost:8080/mcp
   ```

### 调试模式

```bash
# 启用详细日志
export GENOME_MCP_LOG_LEVEL=debug
python -m genome_mcp --port 8080
```

## 📚 更多信息

- 项目主页: https://github.com/your-repo/genome-mcp
- 文档: https://genome-mcp.readthedocs.io
- 问题反馈: https://github.com/your-repo/genome-mcp/issues
