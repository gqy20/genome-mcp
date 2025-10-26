# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🧬 项目概述

**Genome MCP v0.2.1** 是一个智能基因组数据服务器，通过MCP协议提供高质量的基因信息查询、同源基因分析和进化研究功能。该项目采用模块化架构，完全基于权威数据库，无模拟数据，科学严谨可靠。

### 🎯 核心功能
- **🧬 基因信息查询**: 基于NCBI Gene数据库的准确基因信息
- **🔄 同源基因分析**: 基于Ensembl API的跨物种同源基因查询（253+ TP53同源基因）
- **🧬 进化分析**: 系统发育关系构建和保守性分析
- **🔍 语义搜索**: 理解查询意图的智能搜索功能
- **📊 批量处理**: 优化的并发查询，支持大规模数据分析
- **🔬 科学可靠**: 基于权威数据库，完全无模拟数据

## 🚀 现代化开发工作流（基于uv工具链）

### 🌟 环境设置和安装
```bash
# 🚀 推荐：使用uv进行完整环境管理
uv sync --dev                # 一键创建虚拟环境并安装所有依赖

# ✅ 完成！环境已准备就绪
# uv会自动管理虚拟环境，无需手动激活

# 🔧 传统方式（兼容性，不推荐）
make install                 # 需要手动管理虚拟环境
```

### 🔧 代码质量（uv优先）
```bash
# 🎯 现代化uv工作流（推荐）
uv run ruff format .         # 智能代码格式化
uv run ruff check .          # 快速代码质量检查
uv run ruff check --fix .    # 自动修复可修复的问题

# 📊 完整质量检查流程
uv run ruff format . && uv run ruff check . && uv run pytest

# 🔧 Makefile方式（兼容性）
make format                  # 传统格式化
make lint                    # 传统代码检查
make check                   # 完整检查
make ci                      # CI流程
```

### 🧪 测试（uv方式）
```bash
# 🚀 使用uv运行测试（推荐）
uv run pytest                # 运行所有测试
uv run pytest -v             # 详细输出
uv run pytest --cov=genome_mcp --cov-report=html  # 覆盖率报告

# 🎯 运行特定测试
uv run pytest tests/unit/test_core_functionality.py -v
uv run pytest tests/integration/ -v

# 🔧 Makefile方式（兼容性）
make test                    # 传统测试方式
make test-cov                # 传统覆盖率测试
```

### 📦 构建和发布（uv现代化）
```bash
# 🚀 现代化构建流程（推荐uv）
uv build                     # 构建wheel和source包
uv publish                   # 发布到PyPI（需要认证）

# 🎯 运行MCP服务器（uv方式）
uv run -m genome_mcp         # STDIO模式（推荐）
uv run -m genome_mcp --port 8080      # HTTP模式
uv run -m genome_mcp --mode sse --port 8080  # SSE模式

# 🌐 零安装运行（uvx方式）
uvx genome-mcp               # 直接运行，无需本地安装
uvx genome-mcp --port 8080   # HTTP模式

# 🔧 传统方式（兼容性）
python -m genome_mcp         # 传统启动方式
make build                   # Makefile构建
```

### 🔧 uv 高级开发和部署
```bash
# 📦 依赖管理
uv add requests              # 添加生产依赖
uv add --dev pytest          # 添加开发依赖
uv remove requests           # 移除依赖
uv sync                      # 重新同步所有依赖

# 🌍 环境检查
uv run python --version      # 查看Python版本
uv run pip list             # 查看已安装包
uv tree                      # 查看依赖树

# 🚀 快速开发和调试
uv run                       # 启动交互式shell
uv run script.py            # 运行Python脚本
uv run python -c "print('Hello')"  # 快速执行Python代码
```

> **💡 uv优势总结**：
> - 🚀 **极速安装**：比pip快10-100倍的依赖解析
> - 🔒 **可靠性**：原子性操作，避免环境损坏
> - 🎯 **统一管理**：单一工具处理包、环境、构建、运行
> - 🔄 **CI/CD友好**：可重现构建，适合自动化流程
> - 🌐 **现代化**：专为2024+Python开发设计

## 🏗️ 项目架构

### 核心模块结构 (v0.2.1更新)
```
src/genome_mcp/
├── __main__.py          # 主入口点
├── main.py              # MCP服务器实例创建
└── core/
    ├── __init__.py       # 核心模块导出
    ├── tools.py         # MCP工具接口定义
    ├── query_parser.py  # 查询解析器
    ├── query_executor.py # 查询执行器
    ├── clients.py       # API客户端（NCBI、UniProt、KEGG）
    ├── ensembl_client.py # 🆕 Ensembl REST API客户端
    └── evolution_tools.py # 进化分析工具
```

### 🔧 v0.2.1 重大架构变更

#### Ensembl API完全替换OrthoDB
- **❌ 删除**: OrthoDBClient（API完全不可用）
- **✅ 新增**: EnsemblClient（253个TP53同源基因）
- **🔄 更新**: 查询执行器和进化分析工具
- **📊 性能**: 从0个结果提升到253个同源基因

### 设计模式
1. **MCP工具模式**: 6个主要工具通过MCP接口暴露：
   - `get_data`: 智能数据获取（基因、蛋白质、区域、同源基因）
   - `advanced_query`: 高级批量查询
   - `smart_search`: 语义搜索
   - `analyze_gene_evolution_tool`: 基因进化分析
   - `build_phylogenetic_profile_tool`: 系统发育图谱构建
   - `kegg_pathway_enrichment_tool`: KEGG通路富集分析

2. **查询执行模式**:
   - `QueryParser`: 解析用户查询意图，支持智能识别
   - `QueryExecutor`: 协调多个API客户端执行查询
   - `NCBIClient`/`UniProtClient`/`EnsemblClient`/`KEGGClient`: 专门的数据源客户端

3. **数据类型支持**:
   - 基因信息查询（NCBI Gene）
   - 蛋白质信息查询（UniProt）
   - **🆕 同源基因查询（Ensembl REST API）**
   - **🆕 进化分析（基于真实数据）**
   - 通路富集分析（KEGG API）

### 关键特性
- **🧠 智能查询解析**: 自动识别查询类型和意图
- **⚡ 批量处理优化**: 异步并发查询，智能频率限制
- **🌐 多传输模式**: STDIO、HTTP、SSE支持
- **🔬 科学严谨**: 基于权威数据库，无模拟数据保证
- **🔄 异步架构**: 高性能异步处理架构
- **📊 现代构建**: 完整uv集成，快速构建部署

## 🛠️ 开发指南

### 添加新的MCP工具
1. 在 `src/genome_mcp/core/tools.py` 中添加新的 `@mcp.tool()` 装饰器函数
2. 如需要新的查询类型，在 `src/genome_mcp/core/query_parser.py` 中添加解析逻辑
3. 如需要新的数据源，创建新的客户端类（参考EnsemblClient模式）
4. 在 `src/genome_mcp/core/query_executor.py` 中添加执行逻辑

### 添加新的数据源客户端 (v0.2.1最佳实践)
1. **参考EnsemblClient模式**: 创建独立的客户端类文件
2. **实现异步接口**: 使用`async with`模式管理会话
3. **错误处理**: 实现透明的错误处理和用户友好的错误信息
4. **测试覆盖**: 添加单元测试和集成测试
5. **文档更新**: 更新相关文档和示例

```python
# 新客户端模板 (参考ensembl_client.py)
class NewAPIClient:
    def __init__(self):
        self.base_url = "https://api.example.com"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
```

### 🧪 测试策略 (v0.2.1)
- **单元测试**: `tests/unit/` - 测试核心功能模块 (42/42通过 ✅)
- **集成测试**: `tests/integration/` - 测试完整工作流程 (18/18通过 ✅)
- **使用pytest框架**: 支持异步测试，现代测试工具
- **覆盖率报告**: `uv run pytest --cov=genome_mcp --cov-report=html`
- **CI/CD**: 完整的持续集成支持

## 🚀 配置和部署

### MCP客户端配置
项目支持多种MCP客户端：
- **Claude Desktop**: 推荐使用 `uvx genome-mcp`
- **Continue.dev, Cursor, Cline**: 均支持类似配置
- **示例配置**:
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

### 🌐 环境变量
- `GENOME_MCP_LOG_LEVEL`: 控制日志级别（debug/info/warning/error）
- **推荐开发设置**: `export GENOME_MCP_LOG_LEVEL=debug`

### 📊 数据库和API (v0.2.1更新)
- **NCBI E-utilities API**: 基因信息查询
- **UniProt REST API**: 蛋白质数据查询
- **🆕 Ensembl REST API**: 同源基因查询（253+ TP53同源基因）
- **KEGG API**: 通路富集分析
- **频率限制**: 遵守各API的频率限制政策

## 🔧 故障排除

### 📊 常见问题 (v0.2.1更新)
1. **API可用性**:
   - ✅ Ensembl API: 完全可用
   - ✅ NCBI API: 正常运行
   - ✅ UniProt API: 正常运行
   - ✅ KEGG API: 正常运行
   - ❌ OrthoDB API: 已完全移除

2. **网络连接**: 确保可以访问外部API服务
3. **依赖安装**: 推荐使用`uv sync --dev`替代传统方式

### 🛠️ 调试技巧
- **详细日志**: `export GENOME_MCP_LOG_LEVEL=debug`
- **测试工具**: `uv run pytest -v` 查看详细测试输出
- **MCP测试**: 使用示例脚本测试MCP功能
- **功能验证**: 运行 `uv run pytest tests/` 确保所有测试通过

### 📈 性能优化
- **Ensembl查询**: 支持253+同源基因，响应时间秒级
- **批量处理**: 支持多基因并发查询
- **缓存机制**: 减少重复API调用
- **异步架构**: 高性能异步处理

## 📈 项目状态和质量保证

### ✅ 当前状态 (v0.2.1)
- **测试通过率**: 100% (42/42测试通过)
- **构建状态**: ✅ uv构建成功
- **功能完整性**: ✅ 所有核心功能正常
- **代码质量**: ✅ 现代化工具链集成
- **科学可靠性**: ✅ 无模拟数据，基于权威数据库

### 🎯 质量标准
- **测试覆盖**: 核心功能100%覆盖
- **文档完整**: 项目文档、API文档、使用示例完整
- **代码规范**: 现代Python开发标准
- **部署就绪**: 支持多种部署方式
