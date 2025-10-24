# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Genome MCP 是一个NCBI基因组数据服务器，通过MCP协议提供智能基因信息查询和搜索功能。该项目采用模块化架构，支持多种数据源和查询类型。

## 常用开发命令

### 环境设置和安装
```bash
# 安装开发依赖
make install

# 安装git hooks
make hooks

# 清理临时文件
make clean
```

### 代码质量
```bash
# 格式化代码
make format

# 代码质量检查
make lint

# 完整代码检查（格式化+lint）
make check

# CI完整检查流程
make ci
```

### 测试
```bash
# 运行所有测试
make test

# 运行测试并生成覆盖率报告
make test-cov

# 运行特定测试文件
pytest tests/unit/test_core_functionality.py -v

# 运行特定测试函数
pytest tests/unit/test_core_functionality.py::test_gene_info_query -v
```

### 构建和发布
```bash
# 构建包
make build

# 启动MCP服务器（stdio模式）
python -m genome_mcp

# 启动HTTP服务器模式
python -m genome_mcp --port 8080

# 启动SSE服务器模式
python -m genome_mcp --mode sse --port 8080
```

## 项目架构

### 核心模块结构
```
src/genome_mcp/
├── __main__.py          # 主入口点
├── main.py              # MCP服务器实例创建
└── core/
    ├── __init__.py
    ├── tools.py         # MCP工具接口定义
    ├── query_parser.py  # 查询解析器
    ├── query_executor.py # 查询执行器
    ├── clients.py       # API客户端（NCBI、UniProt、OrthoDB）
    └── evolution_tools.py # 进化分析工具
```

### 设计模式
1. **MCP工具模式**: 所有功能通过MCP工具接口暴露，支持5个主要工具：
   - `get_data`: 智能数据获取（支持基因、蛋白质、区域、同源基因查询）
   - `advanced_query`: 高级批量查询
   - `smart_search`: 语义搜索
   - `analyze_gene_evolution_tool`: 基因进化分析
   - `build_phylogenetic_profile_tool`: 系统发育图谱构建

2. **查询执行模式**:
   - `QueryParser`: 解析用户查询意图
   - `QueryExecutor`: 协调多个API客户端执行查询
   - `NCBIClient`/`UniProtClient`/`OrthoDBClient`: 专门的数据源客户端

3. **数据类型支持**:
   - 基因信息查询（NCBI Gene）
   - 蛋白质信息查询（UniProt）
   - 同源基因查询（OrthoDB）
   - 进化分析（多数据源整合）

### 关键特性
- **智能查询解析**: 自动识别查询类型（基因符号、蛋白质ID、区域搜索等）
- **批量处理优化**: 支持并发查询和频率限制
- **多传输模式**: STDIO、HTTP、SSE
- **缓存机制**: 减少重复API调用
- **异步架构**: 高性能异步处理

## 开发指南

### 添加新的MCP工具
1. 在 `src/genome_mcp/core/tools.py` 中添加新的 `@mcp.tool()` 装饰器函数
2. 如需要新的查询类型，在 `src/genome_mcp/core/query_parser.py` 中添加解析逻辑
3. 如需要新的数据源，在 `src/genome_mcp/core/clients.py` 中添加客户端类
4. 在 `src/genome_mcp/core/query_executor.py` 中添加执行逻辑

### 添加新的数据源客户端
1. 继承基础的API客户端模式
2. 实现异步的查询方法
3. 在 `QueryExecutor` 中注册新的查询类型
4. 添加相应的测试用例

### 测试策略
- 单元测试：`tests/unit/` - 测试核心功能模块
- 集成测试：`tests/integration/` - 测试完整工作流程
- 使用pytest框架，支持异步测试
- 覆盖率报告通过 `make test-cov` 生成

## 配置和部署

### MCP客户端配置
项目支持多种MCP客户端：
- Claude Desktop: 推荐使用 `uvx genome-mcp`
- Continue.dev, Cursor, Cline: 均支持类似配置

### 环境变量
- `GENOME_MCP_LOG_LEVEL`: 控制日志级别（debug/info/warning/error）

### 数据库和API
- 主要依赖NCBI E-utilities API
- 集成UniProt REST API用于蛋白质数据
- 使用OrthoDB API进行同源基因查询
- 遵守各API的频率限制政策

## 故障排除

### 常见问题
1. **API限制**: NCBI API有频率限制，使用默认延迟设置
2. **网络连接**: 确保可以访问NCBI、UniProt等外部API
3. **依赖安装**: 使用 `make install` 安装完整开发依赖

### 调试技巧
- 设置 `GENOME_MCP_LOG_LEVEL=debug` 获取详细日志
- 使用 `python examples/mcp-client-example.py` 测试MCP功能
- 运行 `make test` 确保所有测试通过
