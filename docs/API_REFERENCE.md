# API 参考文档

## 概述

Genome MCP 提供了完整的编程接口，包括服务器类、配置管理和工具函数。本文档详细描述了所有可用的 API。

## 核心类

### BaseMCPServer

所有 MCP 服务器的抽象基类。

#### 类定义

```python
class BaseMCPServer(ABC):
    def __init__(self, config: Optional[GenomeMCPConfig] = None)
    async def start() -> None
    async def stop() -> None
    async def health_check() -> Dict[str, Any]
    async def execute_request(operation: str, params: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]
    async def execute_batch(requests: List[Dict[str, Any]], use_cache: bool = True) -> List[Dict[str, Any]]
    async def execute_stream(operation: str, params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]
```

#### 方法说明

- `start()`: 启动服务器
- `stop()`: 停止服务器
- `health_check()`: 执行健康检查，返回服务器状态信息
- `execute_request()`: 执行单个请求
- `execute_batch()`: 执行批量请求
- `execute_stream()`: 执行流式请求

#### 抽象方法

子类必须实现以下方法：

```python
@abstractmethod
def _define_capabilities(self) -> ServerCapabilities:
    """定义服务器能力"""
    pass

@abstractmethod
def _get_base_url(self) -> str:
    """获取基础 URL"""
    pass

@abstractmethod
async def _execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行具体操作"""
    pass
```

### NCBIGeneServer

NCBI Gene 数据库服务器实现。

#### 类定义

```python
class NCBIGeneServer(BaseMCPServer):
    async def _get_gene_info(params: Dict[str, Any]) -> Dict[str, Any]
    async def _search_genes(params: Dict[str, Any]) -> Dict[str, Any]
    async def _get_gene_summary(params: Dict[str, Any]) -> Dict[str, Any]
    async def _get_gene_homologs(params: Dict[str, Any]) -> Dict[str, Any]
    async def _batch_gene_info(params: Dict[str, Any]) -> Dict[str, Any]
    async def _search_by_region(params: Dict[str, Any]) -> Dict[str, Any]
    async def _get_gene_expression(params: Dict[str, Any]) -> Dict[str, Any]
    async def _get_gene_pathways(params: Dict[str, Any]) -> Dict[str, Any]
```

#### 支持的操作

1. **get_gene_info**: 获取基因详细信息
   - 参数: `gene_id` (必需), `species` (可选, 默认: "human"), `include_summary` (可选)
   - 返回: 基因信息字典

2. **search_genes**: 搜索基因
   - 参数: `term` (必需), `species` (可选), `max_results` (可选), `offset` (可选)
   - 返回: 搜索结果列表

3. **get_gene_summary**: 获取基因摘要
   - 参数: `gene_id` (必需), `species` (可选)
   - 返回: 基因摘要文本

4. **get_gene_homologs**: 获取基因同源体
   - 参数: `gene_id` (必需), `species` (可选), `target_species` (可选)
   - 返回: 同源体信息列表

5. **batch_gene_info**: 批量获取基因信息
   - 参数: `gene_ids` (必需, 列表), `species` (可选)
   - 返回: 批量结果

6. **search_by_region**: 基因组区域搜索
   - 参数: `chromosome` (必需), `start` (必需), `end` (必需), `species` (可选)
   - 返回: 区域内基因列表

7. **get_gene_expression**: 获取基因表达数据（占位符）
   - 参数: `gene_id` (必需), `species` (可选)
   - 返回: 表达数据占位符

8. **get_gene_pathways**: 获取基因通路数据（占位符）
   - 参数: `gene_id` (必需), `species` (可选)
   - 返回: 通路数据占位符

### GenomeMCPCLI

命令行接口类。

#### 类定义

```python
class GenomeMCPCLI:
    def __init__(self)
    async def initialize(config_file: Optional[str] = None)
    async def execute_command(args: argparse.Namespace) -> Dict[str, Any]
    def format_output(result: Dict[str, Any], format_type: str = "json") -> str
```

#### 使用示例

```python
# 创建 CLI 实例
cli = GenomeMCPCLI()

# 初始化
await cli.initialize()

# 执行命令
result = await cli.execute_command(args)

# 格式化输出
output = cli.format_output(result, "pretty")
print(output)
```

## 数据类

### ServerCapabilities

服务器能力描述。

```python
@dataclass
class ServerCapabilities:
    name: str                              # 服务器名称
    version: str                           # 版本号
    description: str                       # 描述
    supports_batch: bool = True           # 支持批量操作
    supports_streaming: bool = False       # 支持流式操作
    max_batch_size: int = 100             # 最大批量大小
    rate_limit_requests: int = 60         # 速率限制请求数
    rate_limit_window: int = 60           # 速率限制窗口（秒）
    operations: List[str] = field(default_factory=list)  # 支持的操作
    data_formats: List[str] = field(default_factory=lambda: ["json"])  # 数据格式
    requires_auth: bool = False           # 需要认证
    auth_methods: List[str] = field(default_factory=list)  # 认证方法
```

### ServerStats

服务器统计信息。

```python
@dataclass
class ServerStats:
    requests_total: int = 0              # 总请求数
    requests_success: int = 0            # 成功请求数
    requests_failed: int = 0             # 失败请求数
    avg_response_time: float = 0.0       # 平均响应时间
    cache_hits: int = 0                  # 缓存命中次数
    cache_misses: int = 0                # 缓存未命中次数
    rate_limit_hits: int = 0              # 速率限制命中次数
    concurrent_requests: int = 0         # 当前并发请求数
    bytes_sent: int = 0                  # 发送字节数
    bytes_received: int = 0              # 接收字节数
```

## 配置管理

### GenomeMCPConfig

主配置类。

```python
@dataclass
class GenomeMCPConfig:
    api: APIConfig                         # API 配置
    data_sources: DataSourcesConfig       # 数据源配置
    cache: CacheConfig                    # 缓存配置
    logging: LoggingConfig                # 日志配置
    enable_caching: bool = True           # 启用缓存
    enable_ncbi: bool = True              # 启用 NCBI 服务器
```

### APIConfig

API 配置。

```python
@dataclass
class APIConfig:
    timeout: float = 30.0                 # 请求超时
    retry_attempts: int = 3               # 重试次数
    user_agent: str = "Genome-MCP/1.0.0"  # 用户代理
```

### DataSourcesConfig

数据源配置。

```python
@dataclass
class DataSourcesConfig:
    ncbi: NCBIConfig                       # NCBI 配置
    # 其他数据源配置...

@dataclass
class NCBIConfig:
    base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    max_batch_size: int = 100
    rate_limit: int = 10
```

## 异常类

### 异常层次结构

```
GenomeMCPError (基础异常)
├── ConfigurationError (配置错误)
├── APIError (API 错误)
│   ├── NetworkError (网络错误)
│   ├── TimeoutError (超时错误)
│   ├── AuthenticationError (认证错误)
│   └── RateLimitError (速率限制错误)
├── ValidationError (验证错误)
├── DataNotFoundError (数据未找到错误)
└── ServerError (服务器错误)
```

### 异常使用示例

```python
try:
    result = await server.execute_request("get_gene_info", {"gene_id": "TP53"})
except ValidationError as e:
    print(f"参数验证错误: {e}")
except DataNotFoundError as e:
    print(f"数据未找到: {e}")
except APIError as e:
    print(f"API 错误: {e}")
except GenomeMCPError as e:
    print(f"Genome MCP 错误: {e}")
```

## 工具函数

### HTTP 相关

```python
async def fetch_with_retry(
    url: str,
    method: str = "GET",
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 30.0,
    **kwargs
) -> Dict[str, Any]
```

带重试机制的 HTTP 请求函数。

### 缓存相关

```python
def generate_cache_key(prefix: str, **kwargs) -> str:
    """生成缓存键"""

def log_execution_time(operation: str):
    """执行时间日志装饰器"""
```

### 验证相关

```python
def validate_url(url: str) -> bool:
    """验证 URL 格式"""

def sanitize_url(url: str) -> str:
    """清理 URL 中的敏感信息"""
```

## 使用示例

### 基本使用

```python
import asyncio
from servers.ncbi.gene import NCBIGeneServer
from configuration import GenomeMCPConfig

async def main():
    # 创建配置
    config = GenomeMCPConfig()
    
    # 创建服务器实例
    server = NCBIGeneServer(config)
    
    async with server:
        # 获取基因信息
        result = await server.execute_request(
            "get_gene_info",
            {"gene_id": "TP53", "species": "human"}
        )
        print(f"基因名称: {result['info']['name']}")
        
        # 搜索基因
        search_result = await server.execute_request(
            "search_genes",
            {"term": "BRCA", "max_results": 5}
        )
        print(f"找到 {search_result['total_count']} 个相关基因")
        
        # 批量获取基因信息
        batch_result = await server.execute_request(
            "batch_gene_info",
            {"gene_ids": ["TP53", "BRCA1", "EGFR"]}
        )
        print(f"成功获取 {batch_result['successful']} 个基因信息")

if __name__ == "__main__":
    asyncio.run(main())
```

### 高级使用

```python
import asyncio
from servers.ncbi.gene import NCBIGeneServer
from configuration import GenomeMCPConfig

async def advanced_example():
    config = GenomeMCPConfig()
    server = NCBIGeneServer(config)
    
    async with server:
        try:
            # 并发执行多个请求
            tasks = [
                server.execute_request("get_gene_info", {"gene_id": "TP53"}),
                server.execute_request("get_gene_info", {"gene_id": "BRCA1"}),
                server.execute_request("search_genes", {"term": "cancer", "max_results": 10})
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"请求 {i} 失败: {result}")
                else:
                    print(f"请求 {i} 成功: {result.get('gene_id', 'N/A')}")
            
            # 获取服务器统计信息
            stats = server.get_stats()
            print(f"总请求数: {stats['stats']['requests_total']}")
            print(f"成功率: {stats['stats']['requests_success']/stats['stats']['requests_total']:.1%}")
            
        except Exception as e:
            print(f"执行出错: {e}")

if __name__ == "__main__":
    asyncio.run(advanced_example())
```

## 性能考虑

### 批量操作

使用批量操作可以显著提高性能：

```python
# 不推荐：逐个请求
for gene_id in gene_ids:
    result = await server.execute_request("get_gene_info", {"gene_id": gene_id})

# 推荐：批量请求
batch_requests = [
    {"operation": "get_gene_info", "params": {"gene_id": gene_id}}
    for gene_id in gene_ids
]
results = await server.execute_batch(batch_requests)
```

### 缓存利用

合理利用缓存可以减少 API 调用：

```python
# 第一次请求会调用 API
result1 = await server.execute_request("get_gene_info", {"gene_id": "TP53"})

# 第二次请求会从缓存获取
result2 = await server.execute_request("get_gene_info", {"gene_id": "TP53"})

# 强制不使用缓存
result3 = await server.execute_request("get_gene_info", {"gene_id": "TP53"}, use_cache=False)
```

## 错误处理最佳实践

```python
async def robust_gene_search(server, term: str, max_retries: int = 3):
    """健壮的基因搜索函数"""
    
    for attempt in range(max_retries):
        try:
            result = await server.execute_request(
                "search_genes",
                {"term": term, "max_results": 10}
            )
            return result
            
        except RateLimitError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            raise
            
        except NetworkError:
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            raise
            
        except (ValidationError, DataNotFoundError) as e:
            # 这些错误不需要重试
            raise
    
    raise Exception(f"搜索失败，已重试 {max_retries} 次")
```

---

*API 参考文档由 Genome MCP 项目自动生成*