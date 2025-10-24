.PHONY: help install test lint format check clean build

# 默认目标
help:
	@echo "Genome MCP 开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  install     - 安装开发依赖"
	@echo "  format      - 格式化代码 (black + isort)"
	@echo "  lint        - 代码质量检查 (ruff)"
	@echo "  check       - 完整代码检查"
	@echo "  test        - 运行测试"
	@echo "  test-cov    - 运行测试并生成覆盖率报告"
	@echo "  clean       - 清理临时文件"
	@echo "  build       - 构建包"
	@echo "  hooks       - 安装git hooks"

# 安装开发依赖
install:
	pip install -e ".[dev,test]"
	pip install pre-commit

# 格式化代码
format:
	black src/ tests/
	isort src/ tests/

# 代码质量检查
lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

# 完整代码检查
check: format lint
	@echo "✅ 代码格式化和检查完成"

# 运行测试
test:
	pytest tests/ -v

# 运行测试并生成覆盖率报告
test-cov:
	pytest tests/ --cov=src/genome_mcp --cov-report=html --cov-report=term-missing

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/
	rm -rf .pytest_cache/

# 构建包
build: clean
	python -m build

# 安装git hooks
hooks:
	pre-commit install
	pre-commit run --all-files

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
