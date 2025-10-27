.PHONY: help install test lint format check clean build version-patch version-minor version-major sync-version test-release

# 默认目标
help:
	@echo "Genome MCP 开发工具"
	@echo ""
	@echo "开发命令:"
	@echo "  install     - 安装开发依赖"
	@echo "  format      - 格式化代码 (black + isort)"
	@echo "  lint        - 代码质量检查 (ruff)"
	@echo "  check       - 完整代码检查"
	@echo "  test        - 运行测试"
	@echo "  test-cov    - 运行测试并生成覆盖率报告"
	@echo "  clean       - 清理临时文件"
	@echo "  build       - 构建包"
	@echo "  hooks       - 安装git hooks"
	@echo ""
	@echo "版本管理命令:"
	@echo "  version-patch    - 升级修订版本 (x.y.Z)"
	@echo "  version-minor    - 升级次版本 (x.Y.z)"
	@echo "  version-major    - 升级主版本 (X.y.z)"
	@echo "  sync-version     - 同步版本信息"
	@echo "  release-patch    - 升级并发布修订版本"
	@echo "  test-release     - 测试版本管理（不发布）"
	@echo "  version          - 显示当前版本"

# 安装开发依赖
install:
	uv sync --dev

# 格式化代码
format:
	uv run ruff format src/ tests/

# 代码质量检查
lint:
	uv run ruff check src/ tests/

# 完整代码检查
check: format lint
	@echo "✅ 代码格式化和检查完成"

# 运行测试
test:
	uv run pytest tests/ -v

# 运行测试并生成覆盖率报告
test-cov:
	uv run pytest tests/ --cov=src/genome_mcp --cov-report=html --cov-report=term-missing

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/
	rm -rf .pytest_cache/

# 构建包
build: clean
	uv build

# 安装git hooks
hooks:
	uv run pre-commit install
	uv run pre-commit run --all-files

# 完整CI检查流程
ci: install check test-cov

# 开发模式 - 持续检查文件变化
watch:
	@echo "开始监控文件变化..."
	@echo "使用 Ctrl+C 停止"
	@while true; do \
		inotifywait -r -e py --include='(src/|tests/)' .; \
		echo "检测到文件变化，运行检查..."; \
		$(MAKE) check; \
	done

# 版本管理命令
version-patch:
	@echo "🔄 升级修订版本 (patch)..."
	uv version --bump patch
	$(MAKE) sync-version
	@echo "✅ 版本升级完成: $$(uv version --short)"

version-minor:
	@echo "🔄 升级次版本 (minor)..."
	uv version --bump minor
	$(MAKE) sync-version
	@echo "✅ 版本升级完成: $$(uv version --short)"

version-major:
	@echo "⚠️  升级主版本 (major)..."
	uv version --bump major
	$(MAKE) sync-version
	@echo "✅ 版本升级完成: $$(uv version --short)"

# 同步版本信息
sync-version:
	@echo "🔄 同步版本信息..."
	python scripts/sync_version.py

# 本地发布流程（手动创建标签）
release-patch: version-patch
	@echo "🏷️  创建Git标签..."
	$(eval VERSION := $(shell uv version --short))
	git add -A
	git commit -m "chore: 升级版本到 v$(VERSION)"
	git tag -a "v$(VERSION)" -m "Release v$(VERSION)"
	git push origin main
	git push origin "v$(VERSION)"
	@echo "🚀 发布完成: v$(VERSION)"

# 测试版本管理（不发布）
test-release:
	@echo "🧪 测试版本管理流程..."
	$(MAKE) sync-version
	@echo "✅ 版本管理测试完成"

# 显示当前版本
version:
	@echo "📋 当前版本: $$(uv version --short)"

# GitHub Actions发布说明
help-github:
	@echo "GitHub Actions发布流程:"
	@echo "1. 访问 GitHub -> Actions -> 'Version Management and Release'"
	@echo "2. 点击 'Run workflow'"
	@echo "3. 选择版本升级类型: patch/minor/major"
	@echo "4. 选择是否发布到PyPI: true/false"
	@echo "5. 点击 'Run workflow'"
	@echo ""
	@echo "两种触发方式:"
	@echo "- 手动触发: 自动版本管理 + 可选发布"
	@echo "- 标签触发: 传统方式，仅发布"
