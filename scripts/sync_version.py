#!/usr/bin/env python3
"""
版本同步脚本 - 从pyproject.toml同步版本到所有项目文件

用法:
  python scripts/sync_version.py
"""

import re
import sys
from pathlib import Path
import tomllib

def read_version_from_pyproject():
    """从pyproject.toml读取版本号"""
    try:
        pyproject_path = Path('pyproject.toml')
        with open(pyproject_path, 'rb') as f:
            data = tomllib.load(f)
        return data['project']['version']
    except Exception as e:
        print(f"❌ 读取pyproject.toml失败: {e}")
        sys.exit(1)

def update_init_py(version):
    """更新__init__.py中的版本"""
    try:
        init_py_path = Path('src/genome_mcp/__init__.py')
        content = init_py_path.read_text()
        content = re.sub(r'__version__ = ".*"', f'__version__ = "{version}"', content)
        init_py_path.write_text(content)
        print(f"✅ 更新 __init__.py: {version}")
    except Exception as e:
        print(f"❌ 更新__init__.py失败: {e}")
        return False
    return True

def update_main_py(version):
    """更新main.py中的版本"""
    try:
        main_py_path = Path('src/genome_mcp/main.py')
        content = main_py_path.read_text()

        # 更新FastMCP版本
        content = re.sub(r'version=".*"', f'version="{version}"', content)
        # 更新CLI版本信息
        content = re.sub(r'version="Genome MCP v.*"', f'version="Genome MCP v{version}"', content)

        main_py_path.write_text(content)
        print(f"✅ 更新 main.py: {version}")
    except Exception as e:
        print(f"❌ 更新main.py失败: {e}")
        return False
    return True

def main():
    """主函数"""
    print("🔄 开始同步版本信息...")

    # 读取当前版本
    version = read_version_from_pyproject()
    print(f"📋 当前版本: {version}")

    # 更新各文件
    success = True
    success &= update_init_py(version)
    success &= update_main_py(version)

    if success:
        print("✅ 版本同步完成!")
    else:
        print("❌ 版本同步失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()