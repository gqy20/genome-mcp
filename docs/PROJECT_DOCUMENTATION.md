# Genome MCP 项目文档

## 项目概述

Genome MCP 是一个基于 Model Context Protocol (MCP) 的基因组数据代理系统，旨在为 AI 工具提供标准化的基因组数据访问接口。该系统采用模块化设计，支持多种基因组数据源，并提供了完整的命令行界面。

## 项目结构

```
genome_mcp/
├── cli.py                           # 命令行接口
├── test_*.py                        # 测试文件
├── src/                             # 源代码目录
│   ├── servers/                     # 服务器实现
│   │   ├── base.py                  # 基础服务器类
│   │   ├── ncbi/                    # NCBI 服务器
│   │   │   └── gene.py             # NCBI Gene 服务器
│   │   └── __init__.py
│   ├── configuration.py             # 配置管理
│   ├── http_utils/                  # HTTP 工具
│   │   ├── __init__.py
│   │   ├── client.py               # HTTP 客户端
│   │   └── rate_limiter.py         # 速率限制器
│   ├── data/                        # 数据处理
│   │   ├── __init__.py
│   │   ├── parsers.py              # 数据解析器
│   │   └── validators.py           # 数据验证器
│   ├── core/                        # 核心工具
│   │   ├── __init__.py
│   │   ├── cache.py                # 缓存工具
│   │   ├── logging.py              # 日志工具
│   │   └── utils.py                # 通用工具
│   └── exceptions.py                # 异常定义
├── tests/                           # 测试目录
├── docs/                            # 文档目录
├── examples/                        # 示例代码
└── scripts/                         # 脚本文件
```

## 核心功能

### 1. 基础服务器架构 (BaseMCPServer)

`BaseMCPServer` 是所有 MCP 服务器的抽象基类，提供了：

- **异步请求处理**: 支持单次、批量和流式请求
- **内置缓存**: 基于 TTL 的内存缓存机制
- **速率限制**: 可配置的请求速率限制
- **错误处理**: 完整的异常处理和错误恢复
- **统计监控**: 详细的请求统计和性能监控
- **生命周期管理**: 服务器的启动、停止和健康检查

### 2. NCBI Gene 服务器 (NCBIGeneServer)

实现了对 NCBI Gene 数据库的完整访问：

- **基因信息检索**: 获取基因的详细信息
- **基因搜索**: 基于关键词的基因搜索
- **基因摘要**: 获取基因的功能描述
- **基因同源体**: 跨物种的基因同源性分析
- **批量操作**: 支持多个基因的批量查询
- **基因组区域搜索**: 基于染色体位置的基因搜索

### 3. 命令行接口 (CLI)

提供用户友好的命令行工具：

- **多格式输出**: 支持 JSON 和可读的 pretty 格式
- **完整的参数验证**: 严格的参数检查和错误提示
- **批量操作支持**: 支持批量处理多个请求
- **服务器管理**: 服务器信息查看和健康检查

## 使用方法

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

#### 1. 查看帮助

```bash
python cli.py --help
python cli.py ncbi-gene --help
python cli.py ncbi-gene get_gene_info --help
```

#### 2. 获取基因信息

```bash
# 获取 TP53 基因信息
python cli.py --format pretty ncbi-gene get_gene_info --gene-id TP53 --species human

# JSON 格式输出
python cli.py --format json ncbi-gene get_gene_info --gene-id BRCA1 --species human
```

#### 3. 搜索基因

```bash
# 搜索包含 "BRCA" 的基因
python cli.py --format pretty ncbi-gene search_genes --term "BRCA" --max-results 10

# 指定物种和结果数量
python cli.py --format json ncbi-gene search_genes --term "cancer" --species human --max-results 5
```

#### 4. 批量获取基因信息

```bash
# 批量获取多个基因信息
python cli.py --batch --format pretty ncbi-gene batch_gene_info --gene-ids "TP53,BRCA1,EGFR"

# JSON 格式批量输出
python cli.py --batch --format json ncbi-gene batch_gene_info --gene-ids "TP53,BRCA1,EGFR"
```

#### 5. 基因组区域搜索

```bash
# 搜索指定染色体区域的基因
python cli.py --format pretty ncbi-gene search_by_region --chromosome 17 --start 43044295 --end 43125483
```

#### 6. 获取基因同源体

```bash
# 获取 TP53 基因的同源体
python cli.py --format pretty ncbi-gene get_gene_homologs --gene-id TP53 --target-species mouse
```

#### 7. 服务器管理和健康检查

```bash
# 查看服务器信息
python cli.py --format pretty ncbi-gene server_info

# 健康检查
python cli.py --format pretty ncbi-gene health_check
```

## 配置选项

### 环境变量

- `GENOME_MCP_CONFIG_PATH`: 配置文件路径
- `GENOME_MCP_LOG_LEVEL`: 日志级别 (DEBUG, INFO, WARNING, ERROR)
- `GENOME_MCP_CACHE_TTL`: 缓存存活时间（秒）
- `GENOME_MCP_CACHE_SIZE`: 缓存最大大小

### 配置文件

创建 `config.yaml` 文件：

```yaml
api:
  timeout: 30.0
  retry_attempts: 3
  user_agent: "Genome-MCP/1.0.0"

data_sources:
  ncbi:
    base_url: "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    max_batch_size: 100
    rate_limit: 10

cache:
  enabled: true
  ttl: 3600
  max_size: 1000

logging:
  level: "INFO"
  format: "json"
```

## 开发指南

### 添加新的数据源服务器

1. **继承 BaseMCPServer**:

```python
from servers.base import BaseMCPServer, ServerCapabilities

class NewDataSourceServer(BaseMCPServer):
    def _define_capabilities(self) -> ServerCapabilities:
        return ServerCapabilities(
            name="NewDataSourceServer",
            version="1.0.0",
            description="New data source MCP server",
            operations=["get_data", "search_data"],
            supports_batch=True
        )
    
    def _get_base_url(self) -> str:
        return self.config.data_sources.new_source.base_url
    
    async def _execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # 实现具体的操作逻辑
        pass
```

2. **更新配置**: 在 `configuration.py` 中添加新的数据源配置

3. **更新 CLI**: 在 `cli.py` 中添加新的服务器选项

4. **编写测试**: 创建相应的测试文件

### 扩展 CLI 功能

1. **添加新的操作**:

```python
# 在 create_parser() 函数中添加新的子命令
new_operation_parser = subparsers.add_parser(
    "new_operation",
    help="新的操作描述"
)
new_operation_parser.add_argument(
    "--param", "-p",
    required=True,
    help="操作参数"
)
```

2. **实现操作逻辑**:

```python
elif operation == "new_operation":
    return await self._new_operation(params)
```

## 测试

### 运行测试

```bash
# 运行基础服务器测试
python test_base_server.py

# 运行 NCBI 服务器测试
python test_ncbi_gene_server.py

# 运行 CLI 测试
python test_cli.py

# 运行单元测试
python -m pytest tests/
```

### 测试覆盖率

```bash
# 生成测试覆盖率报告
python -m pytest --cov=src tests/ --cov-report=html
```

## 性能优化

### 缓存策略

- **内存缓存**: 使用 TTL 策略自动清理过期缓存
- **批量处理**: 支持批量请求以减少网络开销
- **速率限制**: 防止 API 限速和过度请求

### 网络优化

- **连接池**: 复用 HTTP 连接
- **超时设置**: 合理的请求超时配置
- **重试机制**: 指数退避的重试策略

## 错误处理

### 异常类型

- `GenomeMCPError`: 基础异常类
- `APIError`: API 调用错误
- `ValidationError`: 参数验证错误
- `DataNotFoundError`: 数据未找到错误
- `NetworkError`: 网络连接错误
- `RateLimitError`: 速率限制错误

### 错误恢复

- **自动重试**: 网络错误和临时性错误的自动重试
- **优雅降级**: 部分功能失败时的降级处理
- **详细日志**: 完整的错误日志和调试信息

## 部署

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

CMD ["python", "cli.py", "--help"]
```

### 系统要求

- Python 3.11+
- 内存: 最少 512MB
- 网络: 访问 NCBI API 的网络连接

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支
3. 编写测试用例
4. 确保测试通过
5. 提交 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 文档: [项目文档]

---

*本文档由 Genome MCP 项目自动生成*