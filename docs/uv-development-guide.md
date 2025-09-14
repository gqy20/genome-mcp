# 基因组数据代理MCP系统 - uv开发和使用指南

## 1. 概述

本指南详细介绍了如何使用uv（现代Python包和依赖管理工具）进行基因组数据代理MCP系统的开发、测试和部署。

## 2. 环境设置

### 2.1 安装uv
```bash
# 在macOS/Linux上安装
curl -LsSf https://astral.sh/uv/install.sh | sh

# 在Windows上安装
powershell -c "irm astral.sh/uv/install.sh | iex"

# 验证安装
uv --version
```

### 2.2 项目初始化
```bash
# 创建项目目录
mkdir genome-mcp
cd genome-mcp

# 初始化项目
uv init --name genome-mcp --app

# 创建详细的项目结构
mkdir -p src/genome_mcp/{config,servers/{ncbi,ensembl,variation,functional},clients,utils/{http,parsers,validators},core/{models,cache},types}
mkdir -p tests/{unit/{test_servers/{test_ncbi,test_ensembl},test_clients,test_utils},integration,fixtures}
mkdir docs examples scripts
```

### 2.3 配置开发环境
```bash
# 添加核心依赖
uv add mcp biopython pyensembl mygene myvariant pandas numpy aiohttp pydantic structlog click

# 添加开发依赖
uv add --dev pytest pytest-asyncio pytest-cov black isort mypy pre-commit ruff bandit

# 添加构建工具
uv add --dev build twine bumpversion towncrier
```

## 3. 项目结构

```
genome-mcp/
├── src/genome_mcp/          # 源代码包
│   ├── __init__.py         # 版本信息和核心导出
│   ├── cli.py              # 命令行接口 (300-400行)
│   ├── config/             # 配置管理模块
│   │   ├── __init__.py
│   │   ├── settings.py     # 基础配置 (200-300行)
│   │   ├── env.py          # 环境变量管理 (100-200行)
│   │   └── validation.py   # 配置验证 (150-250行)
│   ├── servers/            # MCP服务器实现
│   │   ├── __init__.py
│   │   ├── base.py        # 基础服务器类 (200-300行)
│   │   ├── ncbi/          # NCBI相关服务器
│   │   │   ├── __init__.py
│   │   │   ├── gene.py     # NCBI基因服务器 (300-400行)
│   │   │   ├── publication.py  # NCBI文献服务器 (300-400行)
│   │   │   └── clinvar.py # NCBI临床变异数据库 (300-400行)
│   │   ├── ensembl/       # Ensembl相关服务器
│   │   │   ├── __init__.py
│   │   │   ├── gene.py     # Ensembl基因服务器 (300-400行)
│   │   │   ├── sequence.py # Ensembl序列服务器 (300-400行)
│   │   │   └── coordinate.py  # 坐标转换服务器 (200-300行)
│   │   ├── variation/     # 变异数据服务器
│   │   │   ├── __init__.py
│   │   │   ├── dbsnp.py    # dbSNP服务器 (300-400行)
│   │   │   └── clinvar.py  # ClinVar服务器 (300-400行)
│   │   └── functional/    # 功能基因组学服务器
│   │       ├── __init__.py
│   │       ├── go.py      # Gene Ontology服务器 (300-400行)
│   │       └── kegg.py    # KEGG通路服务器 (300-400行)
│   ├── clients/            # MCP客户端实现
│   │   ├── __init__.py
│   │   ├── base.py        # 基础客户端类 (200-300行)
│   │   ├── orchestrator.py  # 查询编排器 (400-500行)
│   │   └── validator.py   # 数据验证客户端 (300-400行)
│   ├── utils/              # 工具函数
│   │   ├── __init__.py
│   │   ├── http.py        # HTTP客户端工具 (200-300行)
│   │   ├── cache.py       # 缓存工具 (200-300行)
│   │   ├── parsers.py     # 数据解析器 (400-500行)
│   │   ├── validators.py  # 数据验证器 (300-400行)
│   │   └── helpers.py     # 通用辅助函数 (200-300行)
│   ├── core/               # 核心功能模块
│   │   ├── __init__.py
│   │   ├── models.py      # 数据模型 (400-500行)
│   │   ├── exceptions.py  # 异常定义 (150-250行)
│   │   ├── cache.py       # 缓存管理 (300-400行)
│   │   └── monitoring.py  # 监控和日志 (300-400行)
│   └── types/              # 类型定义
│       ├── __init__.py
│       ├── gene.py        # 基因相关类型 (200-300行)
│       ├── variant.py     # 变异相关类型 (200-300行)
│       └── common.py      # 通用类型定义 (150-250行)
├── tests/                  # 测试代码
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   ├── performance/       # 性能测试
│   └── fixtures/          # 测试数据和夹具
├── docs/                   # 文档
├── examples/               # 示例代码
├── scripts/                # 构建和部署脚本
├── pyproject.toml         # 项目配置
├── .pre-commit-config.yaml # pre-commit配置
├── .gitignore
├── README.md
└── LICENSE
```

## 4. 开发工作流

### 4.1 代码质量检查
```bash
# 安装pre-commit hooks
uv run pre-commit install

# 手动运行所有检查
uv run pre-commit run --all-files

# 运行特定检查
uv run pre-commit run black
uv run pre-commit run mypy
uv run pre-commit run ruff
```

### 4.2 代码格式化
```bash
# 格式化代码
uv run black src/ tests/

# 导入排序
uv run isort src/ tests/

# 类型检查
uv run mypy src/
```

### 4.3 测试
```bash
# 运行所有测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov=genome_mcp --cov-report=html

# 运行特定测试文件
uv run pytest tests/test_ncbi.py

# 运行测试并显示详细输出
uv run pytest -v
```

### 4.4 依赖管理
```bash
# 添加新的运行时依赖
uv add new-package

# 添加开发依赖
uv add --dev new-dev-package

# 更新所有依赖
uv sync

# 移除依赖
uv remove package-name

# 查看依赖树
uv tree
```

## 5. 构建和发布

### 5.1 构建项目
```bash
# 构建分发包
uv build

# 检查构建结果
ls -la dist/
```

### 5.2 版本管理
```bash
# 更新补丁版本 (1.0.0 -> 1.0.1)
uv run bumpversion patch

# 更新次要版本 (1.0.0 -> 1.1.0)
uv run bumpversion minor

# 更新主要版本 (1.0.0 -> 2.0.0)
uv run bumpversion major

# 查看当前版本
uv run python -c "import genome_mcp; print(genome_mcp.__version__)"
```

### 5.3 发布到PyPI
```bash
# 构建项目
uv build

# 检查包
uv run python -m twine check dist/*

# 发布到TestPyPI (测试)
uv run python -m twine upload --repository testpypi dist/*

# 发布到PyPI (生产)
uv run python -m twine upload dist/*
```

## 6. 用户使用指南

### 6.1 安装
```bash
# 使用pip安装
pip install genome-mcp

# 使用uvx直接运行 (无需安装)
uvx genome-mcp --help
```

### 6.2 基本使用
```bash
# 查看帮助
uvx genome-mcp --help

# 查询基因信息
uvx genome-mcp query-gene TP53 --species human

# 查询变异数据
uvx genome-mcp query-variant rs123456

# 批量查询
uvx genome-mcp batch-query --input genes.txt --output results.csv

# 交互式模式
uvx genome-mcp interactive
```

### 6.3 配置管理
```bash
# 配置API密钥
uvx genome-mcp config --ncbi-api-key YOUR_NCBI_KEY
uvx genome-mcp config --ensembl-api-key YOUR_ENSEMBL_KEY

# 查看当前配置
uvx genome-mcp config --show

# 重置配置
uvx genome-mcp config --reset
```

### 6.4 高级功能
```bash
# 数据验证和交叉引用
uvx genome-mcp validate-gene TP53 --sources ncbi,ensembl

# 富集分析
uvx genome-mcp enrichment-analysis --gene-list gene_list.txt --species human

# 变异注释
uvx genome-mcp annotate-variants --input variants.vcf --output annotated.vcf
```

## 7. 开发最佳实践

### 7.1 开发环境设置
```bash
# 创建开发环境
uv venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装开发依赖
uv sync --dev

# 运行开发服务器
uv run python -m genome_mcp.cli dev-server
```

### 7.2 调试配置
```bash
# 启用调试模式
export DEBUG=1
uv run python -m genome_mcp.cli --debug

# 查看详细日志
uv run python -m genome_mcp.cli --log-level DEBUG

# 性能分析
uv run python -c "import cProfile; cProfile.run('import genome_mcp; genome_mcp.main()')"
```

### 7.3 内存和性能优化
```bash
# 限制内存使用
uv run --python 3.11 python -m genome_mcp.cli --max-memory 1g

# 并发控制
uv run python -m genome_mcp.cli --max-concurrent 5

# 启用缓存
uv run python -m genome_mcp.cli --enable-cache
```

## 8. 故障排除

### 8.1 常见问题
```bash
# 清理缓存
uv cache clean

# 重新安装所有依赖
uv sync --reinstall

# 检查Python版本兼容性
uv run python --version

# 检查依赖冲突
uv tree --depth 2
```

### 8.2 性能问题
```bash
# 查看依赖占用空间
uv cache dir
du -sh $(uv cache dir)

# 优化依赖安装
uv sync --no-dev  # 仅安装运行时依赖

# 使用更快的镜像
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple/"
uv sync
```

### 8.3 发布问题
```bash
# 检查包完整性
uv run python -m twine check dist/*

# 测试本地安装
uv pip install dist/genome_mcp-*.whl --force-reinstall

# 清理构建缓存
uv build --clean
```

## 9. CI/CD集成

### 9.1 GitHub Actions示例
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

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
    
    - name: Run pre-commit
      run: |
        uv run pre-commit run --all-files
    
    - name: Run tests
      run: |
        uv run pytest tests/ -v --cov=genome_mcp --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### 9.2 自动发布
```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    
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

## 10. 总结

使用uv进行基因组数据代理MCP系统的开发具有以下优势：

1. **快速依赖管理**：uv比传统的pip更快，支持更好的依赖解析
2. **标准化项目结构**：符合现代Python项目的最佳实践
3. **简化的发布流程**：通过PyPI和uvx实现便捷的部署
4. **完善的工具链**：集成代码质量检查、测试、构建等工具
5. **跨平台兼容**：支持Linux、macOS、Windows等平台

通过遵循本指南，可以高效地进行基因组数据代理MCP系统的开发和维护。

---

**版本**：v1.0  
**创建日期**：2025-09-14  
**最后更新**：2025-09-14  
**状态**：开发指南