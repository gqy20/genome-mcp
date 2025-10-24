#!/usr/bin/env python3
"""
运行所有测试脚本

提供一个统一的入口来运行所有测试脚本
"""

import subprocess
import sys
import time
from pathlib import Path

# 获取脚本目录
script_dir = Path(__file__).parent
project_dir = script_dir.parent


def run_test_script(script_name, description):
    """运行单个测试脚本"""
    print(f"\n{'='*60}")
    print(f"🧪 运行测试: {description}")
    print(f"📁 脚本: {script_name}")
    print(f"{'='*60}")

    script_path = script_dir / script_name

    if not script_path.exists():
        print(f"❌ 测试脚本不存在: {script_path}")
        return False

    try:
        # 运行测试脚本
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=60,  # 60秒超时
        )

        # 输出结果
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("⚠️ 错误输出:")
            print(result.stderr)

        print(f"{'='*60}")

        if result.returncode == 0:
            print(f"✅ {description} 测试通过")
            return True
        else:
            print(f"❌ {description} 测试失败 (退出码: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ {description} 测试超时")
        return False
    except Exception as e:
        print(f"❌ {description} 测试异常: {e}")
        return False


def check_project_structure():
    """检查项目结构"""
    print("📁 检查项目结构...")

    required_files = [
        "src/genome_mcp/main.py",
        "src/genome_mcp/__init__.py",
        "src/genome_mcp/core/__init__.py",
        "src/genome_mcp/core/clients.py",
        "src/genome_mcp/core/query_parser.py",
        "src/genome_mcp/core/query_executor.py",
        "src/genome_mcp/core/evolution_tools.py",
        "src/genome_mcp/core/tools.py",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = project_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ 缺失文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ 项目结构完整")
        return True


def check_dependencies():
    """检查依赖项"""
    print("📦 检查依赖项...")

    try:
        import fastmcp

        print(
            f"✅ FastMCP: {fastmcp.__version__ if hasattr(fastmcp, '__version__') else 'installed'}"
        )
    except ImportError:
        print("❌ FastMCP 未安装")
        return False

    try:
        import aiohttp

        print(f"✅ aiohttp: {aiohttp.__version__}")
    except ImportError:
        print("❌ aiohttp 未安装")
        return False

    return True


def main():
    """主函数"""
    print("🧪 Genome MCP 完整测试套件")
    print("=" * 70)
    print("运行所有测试脚本来验证项目功能完整性")
    print("=" * 70)

    # 检查项目结构和依赖
    if not check_project_structure():
        print("\n❌ 项目结构检查失败，请先修复")
        return 1

    if not check_dependencies():
        print("\n❌ 依赖项检查失败，请先安装缺失的依赖")
        return 1

    # 定义测试脚本
    test_scripts = [
        ("test_core_functionality.py", "核心功能测试"),
    ]

    # 运行所有测试
    start_time = time.time()
    passed_tests = 0
    total_tests = len(test_scripts)

    for script_name, description in test_scripts:
        if run_test_script(script_name, description):
            passed_tests += 1
        time.sleep(1)  # 避免测试间的干扰

    end_time = time.time()
    duration = end_time - start_time

    # 输出总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print(f"⏱️ 总耗时: {duration:.2f} 秒")
    print(f"📋 测试脚本: {total_tests} 个")
    print(f"✅ 通过测试: {passed_tests} 个")
    print(f"❌ 失败测试: {total_tests - passed_tests} 个")
    print(f"📈 通过率: {passed_tests/total_tests*100:.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！")
        print("🚀 Genome MCP 项目功能完整，可以正常使用")
        print("\n💡 下一步:")
        print("   - 启动 MCP服务器: python -m src.genome_mcp.main")
        print("   - 或使用 uvx: uvx genome-mcp")
        print("   - 查看 README.md 了解使用方法")
        return 0
    else:
        print(f"\n⚠️ {total_tests - passed_tests} 个测试失败")
        print("🔧 请检查失败的功能并修复问题")
        return 1


if __name__ == "__main__":
    exit(main())
