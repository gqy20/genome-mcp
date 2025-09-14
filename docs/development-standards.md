# 基因组数据代理MCP系统 - 开发规范

## 1. 项目结构规范

### 1.1 目录结构
```
genome_mcp/
├── src/genome_mcp/              # 源代码包目录
│   ├── __init__.py             # 版本信息和核心导出
│   ├── cli.py                  # 命令行接口 (300-400行)
│   ├── config/                 # 配置管理模块
│   │   ├── __init__.py
│   │   ├── settings.py         # 基础配置 (200-300行)
│   │   ├── env.py              # 环境变量管理 (100-200行)
│   │   └── validation.py       # 配置验证 (150-250行)
│   ├── servers/                # MCP服务器实现
│   │   ├── __init__.py
│   │   ├── base.py            # 基础服务器类 (200-300行)
│   │   ├── ncbi/              # NCBI相关服务器
│   │   │   ├── __init__.py
│   │   │   ├── gene.py        # NCBI基因服务器 (300-400行)
│   │   │   ├── publication.py # NCBI文献服务器 (300-400行)
│   │   │   └── clinvar.py     # NCBI临床变异数据库 (300-400行)
│   │   ├── ensembl/           # Ensembl相关服务器
│   │   │   ├── __init__.py
│   │   │   ├── gene.py        # Ensembl基因服务器 (300-400行)
│   │   │   ├── sequence.py    # Ensembl序列服务器 (300-400行)
│   │   │   └── coordinate.py  # 坐标转换服务器 (200-300行)
│   │   ├── variation/         # 变异数据服务器
│   │   │   ├── __init__.py
│   │   │   ├── dbsnp.py       # dbSNP服务器 (300-400行)
│   │   │   └── clinvar.py     # ClinVar服务器 (300-400行)
│   │   └── functional/        # 功能基因组学服务器
│   │       ├── __init__.py
│   │       ├── go.py          # Gene Ontology服务器 (300-400行)
│   │       └── kegg.py        # KEGG通路服务器 (300-400行)
│   ├── clients/                # MCP客户端实现
│   │   ├── __init__.py
│   │   ├── base.py            # 基础客户端类 (200-300行)
│   │   ├── orchestrator.py    # 查询编排器 (400-500行)
│   │   └── validator.py       # 数据验证客户端 (300-400行)
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── http.py            # HTTP客户端工具 (200-300行)
│   │   ├── cache.py           # 缓存工具 (200-300行)
│   │   ├── parsers.py         # 数据解析器 (400-500行)
│   │   ├── validators.py      # 数据验证器 (300-400行)
│   │   └── helpers.py         # 通用辅助函数 (200-300行)
│   ├── core/                   # 核心功能模块
│   │   ├── __init__.py
│   │   ├── models.py          # 数据模型 (400-500行)
│   │   ├── exceptions.py      # 异常定义 (150-250行)
│   │   ├── cache.py           # 缓存管理 (300-400行)
│   │   └── monitoring.py       # 监控和日志 (300-400行)
│   └── types/                  # 类型定义
│       ├── __init__.py
│       ├── gene.py            # 基因相关类型 (200-300行)
│       ├── variant.py         # 变异相关类型 (200-300行)
│       └── common.py          # 通用类型定义 (150-250行)
├── tests/                      # 测试代码
│   ├── unit/                  # 单元测试
│   │   ├── test_servers/
│   │   ├── test_clients/
│   │   ├── test_utils/
│   │   └── test_core/
│   ├── integration/           # 集成测试
│   ├── performance/           # 性能测试
│   └── fixtures/              # 测试数据和夹具
├── docs/                       # 文档目录
├── examples/                   # 示例代码
├── scripts/                    # 构建和部署脚本
├── pyproject.toml             # 项目配置和依赖管理
├── README.md                  # 项目说明
├── CHANGELOG.md               # 版本变更记录
└── LICENSE                    # 开源许可证
```

### 1.2 文件命名规范
- **服务器模块**：按功能模块命名 (如 `ncbi/gene.py`)
- **工具文件**：`{功能}.py` (如 `parsers.py`)
- **测试文件**：`test_{模块}.py` (如 `test_ncbi_gene.py`)
- **配置文件**：使用pyproject.toml统一管理配置

### 1.3 文件大小限制
- **硬性限制**：每个Python文件不得超过700行
- **建议大小**：推荐200-500行，便于维护和理解
- **拆分策略**：超过限制时按功能或逻辑拆分为多个文件

### 1.4 模块职责分离
- **单一职责**：每个模块只负责一个明确的功能
- **依赖清晰**：避免循环依赖，保持清晰的依赖关系
- **接口抽象**：定义清晰的接口，便于测试和扩展
- **配置分离**：将配置项和实现逻辑分离

## 2. 代码规范

### 2.1 Python编码规范
- **PEP 8**：严格遵循PEP 8编码规范
- **类型提示**：所有函数必须使用类型提示
- **文档字符串**：所有公共函数和类必须有详细的docstring
- **变量命名**：使用描述性的变量名，避免单字母变量

### 2.2 代码结构模板
```python
"""
基因组MCP服务器模块

该模块实现了对{数据源}的MCP服务器封装，提供以下功能：
- {功能1描述}
- {功能2描述}
"""

from typing import Dict, List, Optional, Any
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class {ServerName}Server:
    """{数据源}MCP服务器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化服务器
        
        Args:
            config: 服务器配置字典
        """
        self.config = config
        self.server = Server(f"{config['name']}-server")
        self._setup_tools()
    
    def _setup_tools(self):
        """设置服务器工具"""
        self.server.list_tools()
        # 注册工具实现
    
    async def {tool_name}_handler(self, params: Dict[str, Any]) -> List[TextContent]:
        """
        {工具功能描述}
        
        Args:
            params: 工具参数字典
            
        Returns:
            返回结果列表
            
        Raises:
            {异常类型}: {异常描述}
        """
        try:
            # 实现工具逻辑
            result = {}
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in {tool_name}: {str(e)}")
            raise
```

### 2.3 错误处理规范
```python
# 统一异常处理
class GenomicsMCPError(Exception):
    """基因组MCP系统基础异常"""
    pass

class APIError(GenomicsMCPError):
    """API调用异常"""
    pass

class DataValidationError(GenomicsMCPError):
    """数据验证异常"""
    pass

# 异常处理装饰器
def handle_errors(func):
    """错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            logger.error(f"API Error: {str(e)}")
            raise
        except DataValidationError as e:
            logger.warning(f"Validation Error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}")
            raise GenomicsMCPError(f"Unexpected error: {str(e)}")
    return wrapper
```

## 3. MCP服务器开发规范

### 3.1 服务器设计原则
- **原子性**：每个工具执行单一、明确的操作
- **幂等性**：相同输入产生相同输出
- **可组合性**：工具之间可以灵活组合使用
- **容错性**：优雅处理各种异常情况

### 3.2 工具接口规范
```python
# 工具接口定义标准
class ToolInterface:
    """MCP工具接口标准"""
    
    @property
    def name(self) -> str:
        """工具名称"""
        return self.__class__.__name__.lower()
    
    @property
    def description(self) -> str:
        """工具描述"""
        return self.__doc__ or ""
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        """输入参数Schema"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def execute(self, params: Dict[str, Any]) -> List[TextContent]:
        """执行工具"""
        raise NotImplementedError
```

### 3.3 数据传输规范
```python
# 统一数据传输格式
class DataFormat:
    """数据格式标准"""
    
    # 基因信息格式
    GENE_INFO = {
        "gene_id": str,
        "gene_symbol": str,
        "species": str,
        "chromosome": str,
        "start_position": int,
        "end_position": int,
        "strand": str,
        "description": str,
        "data_source": str,
        "confidence_score": float
    }
    
    # 变异信息格式
    VARIANT_INFO = {
        "variant_id": str,
        "rsid": str,
        "chromosome": str,
        "position": int,
        "ref_allele": str,
        "alt_allele": str,
        "clinical_significance": str,
        "data_source": str,
        "confidence_score": float
    }
```

## 4. 数据验证规范

### 4.1 输入验证
```python
from pydantic import BaseModel, validator
from typing import Optional

class GeneQuery(BaseModel):
    """基因查询参数验证"""
    gene_symbol: str
    species: str = "homo_sapiens"
    
    @validator('gene_symbol')
    def validate_gene_symbol(cls, v):
        if not v or not v.isalnum():
            raise ValueError("Gene symbol must be alphanumeric")
        return v.upper()
    
    @validator('species')
    def validate_species(cls, v):
        valid_species = ["homo_sapiens", "mus_musculus", "drosophila_melanogaster"]
        if v not in valid_species:
            raise ValueError(f"Species must be one of {valid_species}")
        return v
```

### 4.2 输出验证
```python
# 结果验证装饰器
def validate_output(schema: Dict[str, Any]):
    """输出验证装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # 验证输出格式
            if not isinstance(result, dict):
                raise DataValidationError("Output must be a dictionary")
            
            # 检查必需字段
            required_fields = schema.get('required', [])
            for field in required_fields:
                if field not in result:
                    raise DataValidationError(f"Missing required field: {field}")
            
            return result
        return wrapper
    return decorator
```

## 5. 测试规范

### 5.1 测试结构
```
tests/
├── unit/                     # 单元测试
│   ├── test_servers/
│   ├── test_tools/
│   └── test_utils/
├── integration/             # 集成测试
│   ├── test_mcp_protocol/
│   └── test_data_flow/
├── performance/              # 性能测试
│   └── test_response_time/
└── fixtures/                 # 测试数据
    ├── mock_responses/
    └── test_data/
```

### 5.2 测试用例规范
```python
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.servers.ncbi import NCBIServer

class TestNCBIServer:
    """NCBI服务器测试类"""
    
    @pytest.fixture
    def ncbi_server(self):
        """测试服务器fixture"""
        config = {"name": "test-ncbi", "api_key": "test_key"}
        return NCBIServer(config)
    
    @pytest.mark.asyncio
    async def test_get_gene_summary_success(self, ncbi_server):
        """测试获取基因摘要成功场景"""
        # 模拟API响应
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "uid": "7157",
                "name": "TP53",
                "description": "tumor protein p53"
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await ncbi_server.get_gene_summary("7157")
            
            assert result["uid"] == "7157"
            assert result["name"] == "TP53"
    
    @pytest.mark.asyncio
    async def test_get_gene_summary_invalid_id(self, ncbi_server):
        """测试无效基因ID处理"""
        with pytest.raises(APIError):
            await ncbi_server.get_gene_summary("invalid_id")
```

## 6. 配置管理规范

### 6.1 pyproject.toml配置
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "genome-mcp"
version = "1.0.0"
description = "Intelligent genomics data analysis tool based on Model Context Protocol"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.11"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
]
dependencies = [
    "mcp>=1.0.0",
    "biopython>=1.81",
    "pyensembl>=2.3.12",
    "mygene>=3.2.0",
    "myvariant>=1.0.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "aiohttp>=3.8.0",
    "pydantic>=2.0.0",
    "structlog>=23.0.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]

[project.scripts]
genome-mcp = "genome_mcp.cli:main"

[project.urls]
Homepage = "https://github.com/yourusername/genome-mcp"
Documentation = "https://genome-mcp.readthedocs.io"
Repository = "https://github.com/yourusername/genome-mcp"
"Bug Tracker" = "https://github.com/yourusername/genome-mcp/issues"

[tool.uv]
dev-dependencies = [
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=genome_mcp --cov-report=term-missing --cov-report=html"
```

### 6.2 环境变量规范
```bash
# 必需的环境变量
NCBI_API_KEY=your_ncbi_api_key
ENSEMBL_API_KEY=your_ensembl_api_key
LOG_LEVEL=INFO

# 可选的环境变量
CACHE_ENABLED=true
CACHE_TTL=3600
MAX_CONCURRENT_REQUESTS=10

# uv相关环境变量
UV_CACHE_DIR=/path/to/uv/cache
UV_PYTHON=3.11
```

## 7. 文档规范

### 7.1 代码文档
- **模块文档**：每个模块必须有详细的docstring
- **函数文档**：包含功能描述、参数说明、返回值、异常说明
- **类文档**：包含类功能描述、属性说明、使用示例

### 7.2 API文档
- **工具描述**：每个工具必须有清晰的功能描述
- **参数说明**：详细的参数类型、取值范围、默认值
- **返回格式**：标准化的返回数据结构
- **错误代码**：统一的错误码和错误信息

### 7.3 用户文档
- **快速开始**：5分钟快速上手指南
- **API参考**：详细的API使用说明
- **最佳实践**：常见问题和解决方案
- **示例代码**：典型使用场景的代码示例

## 8. 性能优化规范

### 8.1 并发处理
```python
import asyncio
from aiohttp import ClientSession
from typing import List, Dict

class ConcurrentAPIClient:
    """并发API客户端"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_multiple(self, urls: List[str]) -> List[Dict]:
        """并发获取多个URL"""
        async def fetch_single(url: str) -> Dict:
            async with self.semaphore:
                async with ClientSession() as session:
                    async with session.get(url) as response:
                        return await response.json()
        
        tasks = [fetch_single(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### 8.2 缓存策略
```python
from functools import wraps
import time
from typing import Any, Dict
import json

def cache_result(ttl: int = 3600):
    """结果缓存装饰器"""
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 检查缓存
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < ttl:
                    return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            return result
        
        return wrapper
    return decorator
```

## 9. 发布和部署规范

### 9.1 PyPI发布流程
```bash
# 1. 使用uv构建包
uv build

# 2. 检查包内容
uv run python -m twine check dist/*

# 3. 发布到TestPyPI（测试）
uv run python -m twine upload --repository testpypi dist/*

# 4. 发布到PyPI（生产）
uv run python -m twine upload dist/*
```

### 9.2 版本管理
```bash
# 使用uv进行版本管理
uv run bumpversion patch  # 补丁版本
uv run bumpversion minor  # 次要版本
uv run bumpversion major  # 主要版本

# 生成变更日志
uv run python -m towncrier build
```

### 9.3 GitHub Actions CI/CD
```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'
  release:
    types: [published]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up uv
      uses: astral-sh/setup-uv@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        uv sync --dev
    
    - name: Run tests
      run: |
        uv run pytest tests/ -v --cov=genome_mcp --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  publish:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags')
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up uv
      uses: astral-sh/setup-uv@v2
      with:
        python-version: '3.11'
    
    - name: Build package
      run: |
        uv build
    
    - name: Check package
      run: |
        uv run python -m twine check dist/*
    
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
```

## 10. 监控与日志规范

### 10.1 日志记录
```python
import logging
import structlog
from datetime import datetime

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# 日志记录示例
logger = structlog.get_logger()

async def log_api_call(func_name: str, params: Dict, result: Any, duration: float):
    """记录API调用日志"""
    logger.info(
        "api_call_completed",
        function=func_name,
        params=params,
        result_type=type(result).__name__,
        duration=duration,
        timestamp=datetime.now().isoformat()
    )
```

### 10.2 性能监控
```python
import time
from functools import wraps
from typing import Callable

def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 记录性能指标
            logger.info(
                "performance_metric",
                function=func.__name__,
                duration=duration,
                status="success"
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "performance_metric",
                function=func.__name__,
                duration=duration,
                status="error",
                error=str(e)
            )
            raise
    
    return wrapper
```

---

**版本**：v1.0  
**创建日期**：2025-09-14  
**最后更新**：2025-09-14  
**状态**：草稿