# Scripts Directory

这个目录包含项目的辅助脚本。

## 📁 脚本说明

### `sync_version.py`
**用途**: 版本同步脚本
- 从 `pyproject.toml` 读取版本信息
- 同步版本到 `src/genome_mcp/__init__.py` 和 `src/genome_mcp/main.py`
- 由版本管理系统和GitHub Actions自动调用

### `check-compliance.py`
**用途**: FastMCP合规性检查脚本
- 检查项目是否符合FastMCP规范
- 验证工具函数、文档、错误处理等
- 用于CI/CD中的质量检查

## 🚀 使用方法

### 版本同步
```bash
# 手动同步版本
python scripts/sync_version.py

# 通过Makefile调用
make sync-version
```

### 合规性检查
```bash
# 运行合规性检查
python scripts/check-compliance.py

# 通过GitHub Actions自动运行
# 见 .github/workflows/fastmcp-compliance.yml
```

## 📝 维护说明

- 所有脚本都应该是独立的，不依赖外部配置
- 脚本应该有适当的错误处理和用户友好的输出
- 新增脚本时需要更新这个README文件
