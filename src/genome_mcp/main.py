#!/usr/bin/env python3
"""
Genome MCP - 优化版本：3个极简工具覆盖所有功能

Linus风格：统一接口，智能解析，高效批量查询
现在支持进化生物学数据分析！
"""

from fastmcp import FastMCP

from .core.tools import create_mcp_tools

# 创建MCP实例
mcp = FastMCP("Genome MCP", version="0.2.1")

# 注册所有工具
create_mcp_tools(mcp)


def main():
    """主入口点"""
    mcp.run()


if __name__ == "__main__":
    main()
