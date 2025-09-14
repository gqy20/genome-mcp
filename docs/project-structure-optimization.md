# 基因组数据代理MCP系统 - 项目结构优化设计

## 1. 当前项目结构分析

当前项目结构基本合理，但需要进一步细化以确保每个文件不超过700行：

```
genome-mcp/
├── src/genome_mcp/
│   ├── __init__.py
│   ├── cli.py              # 命令行接口
│   ├── config.py           # 配置管理
│   ├── servers/            # MCP服务器实现
│   │   ├── __init__.py
│   │   ├── ncbi.py          # NCBI服务器
│   │   ├── ensembl.py       # Ensembl服务器
│   │   ├── variation.py     # 变异数据服务器
│   │   └── validation.py    # 数据验证服务器
│   ├── clients/            # MCP客户端实现
│   ├── utils/              # 工具函数
│   └── core/               # 核心功能模块
├── tests/
├── docs/
└── pyproject.toml
```

## 2. 优化后的项目结构

为了确保每个文件不超过700行，我建议进一步细分模块：

```
genome-mcp/
├── src/genome_mcp/
│   ├── __init__.py                    # 版本信息和核心导出
│   ├── cli.py                         # 命令行接口 (300-400行)
│   ├── config/                        # 配置管理模块
│   │   ├── __init__.py
│   │   ├── settings.py               # 基础配置 (200-300行)
│   │   ├── env.py                   # 环境变量管理 (100-200行)
│   │   └── validation.py            # 配置验证 (150-250行)
│   ├── servers/                      # MCP服务器实现
│   │   ├── __init__.py
│   │   ├── base.py                  # 基础服务器类 (200-300行)
│   │   ├── ncbi/                    # NCBI相关服务器
│   │   │   ├── __init__.py
│   │   │   ├── gene.py              # NCBI基因服务器 (300-400行)
│   │   │   ├── publication.py       # NCBI文献服务器 (300-400行)
│   │   │   └── clinvar.py           # NCBI临床变异数据库 (300-400行)
│   │   ├── ensembl/                 # Ensembl相关服务器
│   │   │   ├── __init__.py
│   │   │   ├── gene.py              # Ensembl基因服务器 (300-400行)
│   │   │   ├── sequence.py          # Ensembl序列服务器 (300-400行)
│   │   │   └── coordinate.py        # 坐标转换服务器 (200-300行)
│   │   ├── variation/               # 变异数据服务器
│   │   │   ├── __init__.py
│   │   │   ├── dbsnp.py             # dbSNP服务器 (300-400行)
│   │   │   └── clinvar.py           # ClinVar服务器 (300-400行)
│   │   └── functional/              # 功能基因组学服务器
│   │       ├── __init__.py
│   │       ├── go.py                # Gene Ontology服务器 (300-400行)
│   │       └── kegg.py              # KEGG通路服务器 (300-400行)
│   ├── clients/                      # MCP客户端实现
│   │   ├── __init__.py
│   │   ├── base.py                  # 基础客户端类 (200-300行)
│   │   ├── orchestrator.py          # 查询编排器 (400-500行)
│   │   └── validator.py             # 数据验证客户端 (300-400行)
│   ├── utils/                        # 工具函数
│   │   ├── __init__.py
│   │   ├── http.py                  # HTTP客户端工具 (200-300行)
│   │   ├── cache.py                 # 缓存工具 (200-300行)
│   │   ├── parsers.py               # 数据解析器 (400-500行)
│   │   ├── validators.py            # 数据验证器 (300-400行)
│   │   └── helpers.py               # 通用辅助函数 (200-300行)
│   ├── core/                         # 核心功能模块
│   │   ├── __init__.py
│   │   ├── models.py                # 数据模型 (400-500行)
│   │   ├── exceptions.py            # 异常定义 (150-250行)
│   │   ├── cache.py                 # 缓存管理 (300-400行)
│   │   └── monitoring.py             # 监控和日志 (300-400行)
│   └── types/                        # 类型定义
│       ├── __init__.py
│       ├── gene.py                  # 基因相关类型 (200-300行)
│       ├── variant.py               # 变异相关类型 (200-300行)
│       └── common.py                # 通用类型定义 (150-250行)
├── tests/                            # 测试代码
│   ├── unit/                        # 单元测试
│   │   ├── test_servers/
│   │   │   ├── test_ncbi/
│   │   │   ├── test_ensembl/
│   │   │   └── test_variation/
│   │   ├── test_clients/
│   │   ├── test_utils/
│   │   └── test_core/
│   ├── integration/                 # 集成测试
│   │   ├── test_mcp_protocol/
│   │   ├── test_data_flow/
│   │   └── test_end_to_end/
│   └── fixtures/                    # 测试数据和夹具
│       ├── mock_responses/
│       └── test_data/
├── docs/                             # 文档
├── examples/                         # 示例代码
├── scripts/                          # 构建和部署脚本
│   ├── build.py
│   ├── publish.py
│   └── setup.py
├── pyproject.toml                   # 项目配置
├── .pre-commit-config.yaml           # pre-commit配置
├── .gitignore
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## 3. 模块职责说明

### 3.1 配置模块 (config/)
- **settings.py**: 基础配置项，包括服务器地址、超时设置等
- **env.py**: 环境变量读取和验证
- **validation.py**: 配置项验证逻辑

### 3.2 服务器模块 (servers/)
- **base.py**: 抽象基类，定义通用服务器接口
- **ncbi/**: NCBI相关服务器，按功能细分
- **ensembl/**: Ensembl相关服务器，按功能细分
- **variation/**: 变异数据服务器，按数据源细分
- **functional/**: 功能基因组学服务器，按数据库细分

### 3.3 客户端模块 (clients/)
- **base.py**: 抽象基类，定义通用客户端接口
- **orchestrator.py**: 查询编排和结果整合
- **validator.py**: 数据验证和冲突解决

### 3.4 工具模块 (utils/)
- **http.py**: HTTP客户端封装，包含重试、缓存等
- **cache.py**: 缓存工具，支持多级缓存
- **parsers.py**: 各种数据格式的解析器
- **validators.py**: 数据验证逻辑
- **helpers.py**: 通用辅助函数

### 3.5 核心模块 (core/)
- **models.py**: 核心数据模型定义
- **exceptions.py**: 自定义异常类
- **cache.py**: 缓存管理和策略
- **monitoring.py**: 监控、日志和指标收集

### 3.6 类型模块 (types/)
- **gene.py**: 基因相关的类型定义
- **variant.py**: 变异相关的类型定义
- **common.py**: 通用类型定义

## 4. 文件大小控制策略

### 4.1 代码拆分原则
1. **单一职责**: 每个文件只负责一个明确的功能
2. **合理分层**: 按照功能层次组织代码
3. **依赖管理**: 避免循环依赖，保持清晰的依赖关系
4. **接口设计**: 定义清晰的接口，便于测试和扩展

### 4.2 大文件处理方案
如果某个模块可能超过700行，采用以下策略：

1. **水平拆分**: 按功能拆分成多个文件
2. **垂直拆分**: 将实现和接口分离
3. **抽象提取**: 将通用逻辑提取到基类或工具模块
4. **配置分离**: 将配置项和实现分离

### 4.3 示例：NCBI服务器拆分
```python
# 原始设计（可能超过700行）
# servers/ncbi.py - 包含所有NCBI相关功能

# 优化设计（每个文件300-400行）
# servers/ncbi/__init__.py - 模块导出
# servers/ncbi/gene.py - 基因查询功能
# servers/ncbi/publication.py - 文献查询功能
# servers/ncbi/clinvar.py - 临床变异查询功能
```

## 5. 接口设计示例

### 5.1 服务器基类
```python
# servers/base.py (200-300行)
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging

class BaseMCPServer(ABC):
    """MCP服务器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化服务器"""
        pass
    
    @abstractmethod
    async def get_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """执行工具"""
        pass
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True
```

### 5.2 NCBI基因服务器
```python
# servers/ncbi/gene.py (300-400行)
from typing import Dict, Any, Optional
from Bio import Entrez
from ..base import BaseMCPServer
from ...utils.http import HTTPClient
from ...types.gene import GeneInfo

class NCBIGeneServer(BaseMCPServer):
    """NCBI基因服务器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.http_client = HTTPClient(config.get('timeout', 30))
    
    async def initialize(self) -> None:
        """初始化服务器"""
        Entrez.email = self.config.get('email', '')
        Entrez.api_key = self.config.get('api_key', '')
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return [
            {
                "name": "find_gene_id",
                "description": "根据基因符号查找Entrez Gene ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "species": {"type": "string", "default": "human"}
                    },
                    "required": ["symbol"]
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """执行工具"""
        if tool_name == "find_gene_id":
            return await self.find_gene_id(params['symbol'], params.get('species', 'human'))
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def find_gene_id(self, symbol: str, species: str = 'human') -> str:
        """查找基因ID"""
        # 实现逻辑
        pass
```

## 6. 依赖关系图

```
genome_mcp/
├── cli.py
├── config/
│   └── settings.py
├── servers/
│   ├── base.py
│   ├── ncbi/
│   │   ├── gene.py
│   │   └── publication.py
│   └── ensembl/
│       └── gene.py
├── clients/
│   ├── base.py
│   └── orchestrator.py
├── utils/
│   ├── http.py
│   └── cache.py
├── core/
│   ├── models.py
│   └── exceptions.py
└── types/
    └── gene.py

依赖关系:
cli.py -> config/, servers/, clients/
servers/* -> utils/, core/, types/
clients/* -> utils/, core/, types/
utils/ -> core/
```

## 7. 测试结构对应

```
tests/
├── unit/
│   ├── test_servers/
│   │   ├── test_ncbi/
│   │   │   ├── test_gene.py
│   │   │   └── test_publication.py
│   │   └── test_ensembl/
│   │       └── test_gene.py
│   ├── test_clients/
│   │   ├── test_orchestrator.py
│   │   └── test_validator.py
│   ├── test_utils/
│   │   ├── test_http.py
│   │   └── test_cache.py
│   └── test_core/
│       ├── test_models.py
│       └── test_cache.py
└── integration/
    ├── test_mcp_protocol/
    ├── test_data_flow/
    └── test_end_to_end/
```

## 8. 总结

这种项目结构设计具有以下优势：

1. **文件大小控制**: 每个文件都控制在700行以内
2. **职责明确**: 每个模块都有明确的职责
3. **易于维护**: 模块化设计便于维护和扩展
4. **测试友好**: 每个模块都有对应的测试
5. **依赖清晰**: 避免循环依赖，保持清晰的依赖关系
6. **可扩展性**: 新功能可以通过添加新模块实现

通过这种设计，可以确保代码的可维护性和可读性，同时满足每个文件不超过700行的要求。

---

**版本**：v1.0  
**创建日期**：2025-09-14  
**最后更新**：2025-09-14  
**状态**：项目结构优化设计