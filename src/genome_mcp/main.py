#!/usr/bin/env python3
"""
Genome MCP - 智能基因组数据服务器

版本: 0.2.5
功能: 基因信息查询、同源基因分析、进化研究、语义搜索、批量处理

支持模式:
- STDIO: 标准输入输出模式（默认）
- HTTP: HTTP服务器模式
- SSE: Server-Sent Events模式

使用示例:
  # STDIO模式（默认）
  python -m genome_mcp

  # HTTP模式 - 本地访问
  python -m genome_mcp --port 8080

  # HTTP模式 - 外部访问（0.0.0.0）
  python -m genome_mcp --port 8080 --host 0.0.0.0

  # SSE模式
  python -m genome_mcp --mode sse --port 8080

更多信息请访问: https://github.com/your-repo/genome-mcp
"""

import argparse
import sys

from fastmcp import FastMCP

from .core.tools import create_mcp_resources, create_mcp_tools

# 创建MCP实例
mcp = FastMCP("Genome MCP", version="0.2.5")

# 注册所有资源和工具
create_mcp_resources(mcp)
create_mcp_tools(mcp)


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="genome-mcp",
        description="Genome MCP - 智能基因组数据服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                           # STDIO模式（默认）
  %(prog)s --port 8080              # HTTP模式 - 本地访问
  %(prog)s --port 8080 --host 0.0.0.0  # HTTP模式 - 外部访问
  %(prog)s --mode sse --port 8080   # SSE模式
  %(prog)s --help                   # 显示帮助信息

传输模式说明:
  STDIO   - 标准输入输出模式，适用于本地MCP客户端（如Claude Desktop）
  HTTP    - HTTP服务器模式，支持远程访问和Web客户端
  SSE     - Server-Sent Events模式，支持实时通信

网络配置说明:
  --host 127.0.0.1    - 仅本地访问（默认）
  --host 0.0.0.0      - 允许外部访问，适用于Docker和云部署
  --port <端口号>      - 指定服务器端口（HTTP/SSE模式需要）

更多信息请访问: https://github.com/your-repo/genome-mcp
        """,
    )

    parser.add_argument("--port", "-p", type=int, help="指定端口号（HTTP/SSE模式必需）")

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="指定绑定地址（默认: 127.0.0.1，使用0.0.0.0允许外部访问）",
    )

    parser.add_argument(
        "--mode",
        "-m",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="传输模式（默认: stdio）",
    )

    parser.add_argument(
        "--version", "-v", action="version", version="Genome MCP v0.2.5"
    )

    return parser


def main():
    """主入口点"""
    parser = create_parser()
    args = parser.parse_args()

    # 确定传输模式
    transport_map = {"stdio": "stdio", "http": "streamable-http", "sse": "sse"}
    transport = transport_map[args.mode]

    # 验证参数组合
    if args.mode in ["http", "sse"] and not args.port:
        parser.error(f"{args.mode.upper()}模式需要指定端口号 (--port)")

    if args.mode == "stdio" and args.port:
        print("⚠️  警告: STDIO模式忽略--port参数")

    # 准备启动参数
    run_kwargs = {"transport": transport}

    # 只有非STDIO模式才添加端口和主机参数
    if args.mode != "stdio" and args.port:
        run_kwargs["port"] = args.port
        if args.host != "127.0.0.1":
            run_kwargs["host"] = args.host

    # 只有非STDIO模式才显示启动信息
    if args.mode != "stdio":
        print("\n" + "=" * 60)
        print(f"🧬 启动Genome MCP服务器 ({args.mode.upper()}模式)")
        if args.host == "0.0.0.0":
            print(f"🌐 服务器地址: http://0.0.0.0:{args.port}/mcp")
            print("🔓 允许外部访问 - 适用于Docker和云部署")
        else:
            print(f"🏠 服务器地址: http://{args.host}:{args.port}/mcp")
            print("🔒 仅本地访问")
        print(f"📊 传输协议: {transport}")
        print("🛠️  工具数量: 6个核心工具")
        print("📚 资源数量: 3个数据资源")
        print("🧬 功能: 基因查询 | 同源分析 | 进化研究 | 语义搜索")
        print("=" * 60)
        print("🚀 正在启动服务器...\n")
    # STDIO模式保持静默，避免干扰MCP协议通信

    # 启动服务器
    try:
        mcp.run(**run_kwargs)
    except KeyboardInterrupt:
        if args.mode != "stdio":
            print("\n👋 服务器已停止")
    except Exception as e:
        if args.mode != "stdio":
            print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
