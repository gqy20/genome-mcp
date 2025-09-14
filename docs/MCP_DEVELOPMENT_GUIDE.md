# MCP 开发与 PyPI 发布完整指南

## 📋 项目概述

本项目是一个基于 FastMCP 框架开发的学术文献搜索 MCP (Model Context Protocol) 服务器，支持搜索 Europe PMC、arXiv 等多个文献数据库，并已成功发布到 PyPI。

## 🏗️ 项目架构设计

### 1. 模块化架构

```
article-mcp/
├── main.py                 # 主入口文件 (MCP 服务器配置)
├── pyproject.toml          # 项目配置和依赖管理
├── setup.py               # 备用打包配置
├── src/                   # 核心服务模块
│   ├── europe_pmc.py      # Europe PMC API 服务
│   ├── reference_service.py    # 参考文献服务
│   ├── pubmed_search.py   # PubMed 搜索服务
│   ├── arxiv_search.py    # arXiv 搜索服务
│   ├── literature_relation_service.py  # 文献关联服务
│   └── similar_articles.py       # 相似文章服务
├── tool_modules/          # MCP 工具模块
│   ├── search_tools.py        # 搜索工具
│   ├── article_detail_tools.py # 文献详情工具
│   ├── reference_tools.py     # 参考文献工具
│   ├── relation_tools.py      # 关联文献工具
│   └── quality_tools.py       # 期刊质量工具
└── .github/workflows/     # CI/CD 配置
    └── publish.yml        # 自动发布到 PyPI
```

### 2. 核心设计模式

#### 服务层 (Service Layer)
- ** europe_pmc.py**: Europe PMC API 封装，支持异步和同步两种模式
- ** reference_service.py**: 参考文献获取服务，支持批量处理
- ** literature_relation_service.py**: 文献关联关系服务

#### 工具层 (Tool Layer)
- **模块化设计**: 每个工具模块负责特定功能
- **依赖注入**: 通过注册函数注入服务依赖
- **统一接口**: 所有工具都遵循相同的参数和返回格式

## 🔧 MCP 实现详解

### 1. 基础设置

#### 使用 FastMCP 框架

```python
# main.py:16-32
def create_mcp_server():
    """创建MCP服务器"""
    from fastmcp import FastMCP
    
    # 创建 MCP 服务器实例
    mcp = FastMCP("Article MCP Server", version="1.0.0")
    
    # 注册工具函数
    register_search_tools(mcp, europe_pmc_service, pubmed_service, logger)
    # ... 其他工具注册
    
    return mcp
```

#### 工具注册模式

```python
# tool_modules/search_tools.py:20-26
def register_search_tools(mcp, europe_pmc_service, pubmed_service, logger):
    """注册搜索工具函数"""
    # 注入依赖
    search_tools_deps['europe_pmc_service'] = europe_pmc_service
    search_tools_deps['pubmed_service'] = pubmed_service
    search_tools_deps['logger'] = logger
```

### 2. 工具函数实现

#### 工具装饰器使用

```python
# tool_modules/search_tools.py:27-34
@mcp.tool()
def search_europe_pmc(
    keyword: str,
    email: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """搜索 Europe PMC 文献数据库（高性能优化版本）"""
```

#### 参数验证和类型提示
- 使用类型提示确保参数类型安全
- 提供详细的文档字符串
- 支持可选参数和默认值

### 3. 传输模式支持

项目支持三种传输模式：

```python
# main.py:101-114
if transport == 'stdio':
    mcp.run(transport="stdio")  # 适用于桌面客户端
elif transport == 'sse':
    mcp.run(transport="sse", host=host, port=port)  # 适用于 Web 应用
elif transport == 'streamable-http':
    mcp.run(transport="streamable-http", host=host, port=port, path=path)  # 适用于 API 集成
```

## 📦 PyPI 发布配置

### 1. 双配置方案

项目同时支持 `pyproject.toml` 和 `setup.py` 两种配置：

#### pyproject.toml (推荐)

```toml
[project]
name = "article-mcp"
version = "0.1.0"
description = "Article MCP文献搜索服务器"
authors = [{name = "gqy20", email = "qingyu_ge@foxmail.com"}]
license = "MIT"
requires-python = ">=3.10"

[project.scripts]
article-mcp = "main:main"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

#### setup.py (备用)

```python
setup(
    name='article-mcp',
    version='0.2.0',
    py_modules=['main'],
    install_requires=[
        'fastmcp>=2.0.0',
        'requests>=2.25.0',
        # ... 其他依赖
    ],
    entry_points={
        'console_scripts': [
            'article-mcp=main:main',
        ],
    },
)
```

### 2. 自动化发布

使用 GitHub Actions 自动发布：

```yaml
# .github/workflows/publish.yml
name: Publish Python Package

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    
    - name: Install uv
      run: pip install uv
    
    - name: Build package
      run: |
        uv build
        uvx --from . article-mcp info
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        pip install twine
        twine upload dist/*
```

### 3. 版本管理

使用语义化版本控制：

- 主版本号 (Major): 破坏性变更
- 次版本号 (Minor): 新功能
- 修订号 (Patch): 错误修复

## 📊 Git 提交规范

### 1. 提交消息模式

从项目提交历史可以看出以下模式：

#### 功能开发
```
feat: 实现MVP 1-3，完成PMC ID提取和全文获取基础功能
feat: 整合PMC全文获取功能到get_article_details
feat: 创建统一文献关联服务，整合参考文献、相似文献和引用文献功能
```

#### 文档更新
```
docs: 添加下一步工作计划文档
Update README with uvx installation instructions
更新 README.md 和 QWEN.md：1. 更新 README.md 以更好地展示 PyPI 包的使用方式...
```

#### 重构和修复
```
refactor: 重构main.py，实现模块化拆分
fix: revert entry point to main:main
chore: update author email and prepare v0.1.0 release
```

### 2. 提交规范总结

#### 前缀规范
- **feat**: 新功能
- **fix**: 错误修复
- **docs**: 文档更新
- **style**: 代码格式化
- **refactor**: 重构
- **test**: 测试相关
- **chore**: 构建或辅助工具的变动

#### 中文提交特点
- 项目使用中文提交消息
- 详细的变更描述
- 编号列表形式（如 1. 2. 3.）

#### 版本发布
- 使用 `chore:` 前缀
- 明确标注版本号
- 包含发布准备信息

## 🚀 性能优化策略

### 1. 异步处理
- 使用 asyncio 实现并发请求
- 支持异步和同步两种模式
- 性能提升 6.2 倍

### 2. 缓存机制
- 24小时本地缓存
- 避免重复 API 请求
- 支持智能缓存失效

### 3. 批量处理
- 支持最多 20 个 DOI 同时处理
- 使用 Europe PMC 批量查询 API
- 减少网络请求次数

### 4. 错误处理
- 完整的异常处理机制
- 自动重试（3次，指数退避）
- 详细的错误日志记录

## 🔧 开发最佳实践

### 1. 模块化设计
- 按功能划分模块
- 清晰的依赖关系
- 可独立测试的服务层

### 2. 配置管理
- 使用环境变量
- 支持多种部署模式
- 灵活的参数配置

### 3. 文档完整性
- 详细的 README
- 工具函数文档字符串
- 使用示例和配置说明

### 4. 测试策略
- 基础功能测试
- 集成测试
- 性能基准测试

## 📋 部署配置

### 1. Claude Desktop 配置

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": ["article-mcp", "server"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 2. Cherry Studio 配置

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uvx",
      "args": ["article-mcp", "server", "--transport", "stdio"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 3. 本地开发配置

```json
{
  "mcpServers": {
    "article-mcp": {
      "command": "uv",
      "args": ["run", "main.py", "server"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## 🎯 关键成功要素

### 1. 选择合适的框架
- FastMCP 提供了良好的开发体验
- 支持多种传输模式
- 丰富的工具装饰器

### 2. 良好的项目结构
- 清晰的模块划分
- 合理的依赖关系
- 易于维护和扩展

### 3. 完善的文档
- 详细的安装说明
- 丰富的使用示例
- 多种配置方案

### 4. 自动化流程
- CI/CD 自动发布
- 版本管理自动化
- 代码质量检查

### 5. 性能优化
- 异步处理
- 缓存机制
- 批量处理

## 🔮 扩展建议

### 1. 功能扩展
- 支持更多文献数据库
- 添加个性化推荐
- 集成 AI 分析功能

### 2. 性能优化
- 分布式缓存
- 更智能的批量处理
- 预测性缓存

### 3. 开发体验
- 更好的错误处理
- 详细的性能监控
- 插件化架构

这个项目为 MCP 工具开发提供了一个很好的参考模板，包含了从项目结构设计到 PyPI 发布的完整流程。其他开发者可以基于这个模式开发自己的 MCP 工具。