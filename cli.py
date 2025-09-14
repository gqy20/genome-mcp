"""
Command Line Interface for Genome MCP.

This module provides a comprehensive CLI for interacting with genome data servers
including NCBI Gene database operations and other genomic data sources.
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
import structlog

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from configuration import get_config, GenomeMCPConfig
from servers.ncbi.gene import NCBIGeneServer
from servers.base import BaseMCPServer
from exceptions import GenomeMCPError, ValidationError, DataNotFoundError

logger = structlog.get_logger(__name__)


class GenomeMCPCLI:
    """Command Line Interface for Genome MCP."""

    def __init__(self):
        self.config: Optional[GenomeMCPConfig] = None
        self.servers: Dict[str, BaseMCPServer] = {}

    async def initialize(self, config_file: Optional[str] = None):
        """Initialize CLI with configuration."""
        try:
            self.config = get_config(config_file)

            # Initialize available servers
            if self.config.enable_ncbi:
                self.servers["ncbi-gene"] = NCBIGeneServer(self.config)

            logger.info("CLI initialized", servers=list(self.servers.keys()))

        except Exception as e:
            logger.error("Failed to initialize CLI", error=str(e))
            print(f"❌ 初始化失败: {e}")
            sys.exit(1)

    async def execute_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Execute a command based on parsed arguments."""
        server_name = args.server
        operation = args.operation

        if server_name not in self.servers:
            raise ValidationError(f"Unknown server: {server_name}")

        server = self.servers[server_name]

        # Build parameters from arguments
        params = self._build_params(args)

        # Execute the operation
        async with server:
            if args.batch:
                # Batch operation
                requests = self._build_batch_requests(args)
                results = await server.execute_batch(requests)
                return {
                    "operation": operation,
                    "server": server_name,
                    "batch": True,
                    "results": results,
                }
            else:
                # Single operation
                result = await server.execute_request(operation, params)
                return {
                    "operation": operation,
                    "server": server_name,
                    "batch": False,
                    "result": result,
                }

    def _build_params(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Build parameters dictionary from arguments."""
        params = {}

        # Common parameters
        if hasattr(args, "gene_id") and args.gene_id:
            params["gene_id"] = args.gene_id
        if hasattr(args, "species") and args.species:
            params["species"] = args.species
        if hasattr(args, "term") and args.term:
            params["term"] = args.term
        if hasattr(args, "max_results") and args.max_results:
            params["max_results"] = args.max_results
        if hasattr(args, "offset") and args.offset:
            params["offset"] = args.offset

        # Gene-specific parameters
        if hasattr(args, "chromosome") and args.chromosome:
            params["chromosome"] = args.chromosome
        if hasattr(args, "start") and args.start:
            params["start"] = args.start
        if hasattr(args, "end") and args.end:
            params["end"] = args.end
        if hasattr(args, "target_species") and args.target_species:
            params["target_species"] = args.target_species
        if hasattr(args, "include_summary") and args.include_summary is not None:
            params["include_summary"] = args.include_summary

        # Batch parameters
        if hasattr(args, "gene_ids") and args.gene_ids:
            params["gene_ids"] = args.gene_ids.split(",")

        return params

    def _build_batch_requests(self, args: argparse.Namespace) -> List[Dict[str, Any]]:
        """Build batch requests from arguments."""
        if args.operation == "batch_gene_info":
            gene_ids = args.gene_ids.split(",")
            requests = []
            for gene_id in gene_ids:
                requests.append(
                    {
                        "operation": "get_gene_info",
                        "params": {
                            "gene_id": gene_id.strip(),
                            "species": getattr(args, "species", "human"),
                            "include_summary": False,
                        },
                    }
                )
            return requests
        else:
            raise ValidationError(
                f"Batch operation not supported for: {args.operation}"
            )

    def format_output(self, result: Dict[str, Any], format_type: str = "json") -> str:
        """Format output for display."""
        if format_type == "json":
            return json.dumps(result, indent=2, ensure_ascii=False)
        elif format_type == "pretty":
            return self._format_pretty(result)
        else:
            raise ValidationError(f"Unsupported output format: {format_type}")

    def _format_pretty(self, result: Dict[str, Any]) -> str:
        """Format result in a pretty, human-readable way."""
        output = []

        # Header
        server_name = result.get(
            "server", result.get("result", {}).get("server_name", "Unknown")
        )
        output.append(f"🧬 服务器: {server_name}")
        output.append(f"🔧 操作: {result['operation']}")
        output.append(f"📦 批量: {'是' if result.get('batch', False) else '否'}")
        output.append("")

        if result.get("batch", False):
            # Batch results
            batch_results = result.get("results", [])
            successful = sum(1 for r in batch_results if r.get("success", False))
            failed = len(batch_results) - successful

            output.append(f"✅ 成功: {successful}")
            output.append(f"❌ 失败: {failed}")
            output.append("")

            for i, batch_result in enumerate(batch_results, 1):
                status = "✅" if batch_result.get("success", False) else "❌"
                output.append(f"{status}. 结果 {i}:")

                if batch_result.get("success", False):
                    data = batch_result.get("result", {})
                    if "gene_id" in data:
                        output.append(f"   基因ID: {data['gene_id']}")
                    if "uid" in data:
                        output.append(f"   UID: {data['uid']}")
                    if "species" in data:
                        output.append(f"   物种: {data['species']}")
                else:
                    output.append(
                        f"   错误: {batch_result.get('error', 'Unknown error')}"
                    )
                output.append("")
        else:
            # Single result
            data = result.get("result", {})

            # Special formatting for server_info and health_check
            if result["operation"] == "server_info":
                output.append(f"🏷️ 名称: {data.get('server_name', 'Unknown')}")
                output.append(f"📋 版本: {data.get('version', 'Unknown')}")
                output.append(f"📝 描述: {data.get('description', 'No description')}")
                output.append(
                    f"🔄 批量支持: {'✅' if data.get('supports_batch', False) else '❌'}"
                )
                output.append(f"📦 最大批量大小: {data.get('max_batch_size', 0)}")
                output.append(f"⏱️ 速率限制: {data.get('rate_limit', 'Unknown')}")
                output.append(f"🔧 支持的操作: {', '.join(data.get('operations', []))}")
                return "\n".join(output)

            elif result["operation"] == "health_check":
                output.append(f"💚 状态: {data.get('status', 'Unknown')}")
                output.append(f"⏱️ 运行时间: {data.get('uptime', 0)} 秒")
                if "stats" in data:
                    stats = data["stats"]
                    output.append(f"📊 统计信息:")
                    output.append(f"   总请求数: {stats.get('requests_total', 0)}")
                    output.append(f"   成功请求: {stats.get('requests_success', 0)}")
                    output.append(f"   失败请求: {stats.get('requests_failed', 0)}")
                    output.append(
                        f"   平均响应时间: {stats.get('avg_response_time', 0):.3f} 秒"
                    )
                    output.append(f"   成功率: {stats.get('success_rate', 0):.1%}")
                return "\n".join(output)

            if "gene_id" in data:
                output.append(f"🧬 基因ID: {data['gene_id']}")
            if "species" in data:
                output.append(f"🐭 物种: {data['species']}")
            if "uid" in data:
                output.append(f"🆔 UID: {data['uid']}")

            # Gene info
            if "info" in data and data["info"]:
                info = data["info"]
                if "name" in info:
                    output.append(f"📛 名称: {info['name']}")
                if "description" in info:
                    output.append(f"📝 描述: {info['description']}")
                if "otheraliases" in info:
                    output.append(f"🏷️ 别名: {', '.join(info['otheraliases'])}")

            # Search results
            if "results" in data and data["results"]:
                output.append(f"🔍 搜索结果:")
                for i, search_result in enumerate(
                    data["results"][:5], 1
                ):  # Show first 5
                    output.append(
                        f"   {i}. {search_result.get('gene_id', 'N/A')} - {search_result.get('description', 'N/A')}"
                    )
                if len(data["results"]) > 5:
                    output.append(f"   ... 还有 {len(data['results']) - 5} 个结果")

            if "total_count" in data:
                output.append(f"📊 总数: {data['total_count']}")

            # Summary
            if "summary" in data and data["summary"]:
                output.append("📄 摘要:")
                summary_text = (
                    data["summary"][:300] + "..."
                    if len(data["summary"]) > 300
                    else data["summary"]
                )
                output.append(f"   {summary_text}")

            # Homologs
            if "homologs" in data and data["homologs"]:
                output.append(f"🧬 同源体:")
                for homolog in data["homologs"][:5]:  # Show first 5
                    output.append(
                        f"   • {homolog.get('species', 'N/A')}: {homolog.get('gene_id', 'N/A')}"
                    )
                if len(data["homologs"]) > 5:
                    output.append(f"   ... 还有 {len(data['homologs']) - 5} 个同源体")

        return "\n".join(output)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Genome MCP - 基因组数据代理命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s ncbi-gene get-gene-info --gene-id TP53 --species human
  %(prog)s ncbi-gene search-genes --term "BRCA" --max-results 10
  %(prog)s ncbi-gene batch-gene-info --gene-ids "TP53,BRCA1,EGFR" --format pretty
  %(prog)s ncbi-gene get-gene-homologs --gene-id TP53 --target-species mouse
  %(prog)s ncbi-gene search-by-region --chromosome 17 --start 43044295 --end 43125483
        """,
    )

    # Global options
    parser.add_argument("--config", "-c", type=str, help="配置文件路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--batch", "-b", action="store_true", help="批量操作模式")

    # Format option
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "pretty"],
        default="pretty",
        help="输出格式 (默认: pretty)",
    )

    # Server selection
    parser.add_argument("server", choices=["ncbi-gene"], help="选择服务器")

    # Operation selection
    subparsers = parser.add_subparsers(dest="operation", help="选择操作", required=True)

    # Gene info operation
    gene_info_parser = subparsers.add_parser("get_gene_info", help="获取基因详细信息")
    gene_info_parser.add_argument("--gene-id", "-g", required=True, help="基因ID")
    gene_info_parser.add_argument(
        "--species", "-s", default="human", help="物种 (默认: human)"
    )
    gene_info_parser.add_argument(
        "--include-summary", action="store_true", help="包含基因摘要"
    )

    # Search genes operation
    search_parser = subparsers.add_parser("search_genes", help="搜索基因")
    search_parser.add_argument("--term", "-t", required=True, help="搜索词")
    search_parser.add_argument(
        "--species", "-s", default="human", help="物种 (默认: human)"
    )
    search_parser.add_argument(
        "--max-results", "-m", type=int, default=20, help="最大结果数 (默认: 20)"
    )
    search_parser.add_argument(
        "--offset", "-o", type=int, default=0, help="结果偏移量 (默认: 0)"
    )

    # Gene summary operation
    summary_parser = subparsers.add_parser("get_gene_summary", help="获取基因摘要")
    summary_parser.add_argument("--gene-id", "-g", required=True, help="基因ID")
    summary_parser.add_argument(
        "--species", "-s", default="human", help="物种 (默认: human)"
    )

    # Gene homologs operation
    homologs_parser = subparsers.add_parser("get_gene_homologs", help="获取基因同源体")
    homologs_parser.add_argument("--gene-id", "-g", required=True, help="基因ID")
    homologs_parser.add_argument(
        "--species", "-s", default="human", help="源物种 (默认: human)"
    )
    homologs_parser.add_argument("--target-species", help="目标物种过滤器")

    # Batch gene info operation
    batch_parser = subparsers.add_parser("batch_gene_info", help="批量获取基因信息")
    batch_parser.add_argument(
        "--gene-ids", "-i", required=True, help="基因ID列表，用逗号分隔"
    )
    batch_parser.add_argument(
        "--species", "-s", default="human", help="物种 (默认: human)"
    )

    # Search by region operation
    region_parser = subparsers.add_parser(
        "search_by_region", help="按基因组区域搜索基因"
    )
    region_parser.add_argument("--chromosome", "-c", required=True, help="染色体")
    region_parser.add_argument("--start", type=int, required=True, help="起始位置")
    region_parser.add_argument("--end", type=int, required=True, help="结束位置")
    region_parser.add_argument(
        "--species", "-s", default="human", help="物种 (默认: human)"
    )
    region_parser.add_argument(
        "--max-results", "-m", type=int, default=50, help="最大结果数 (默认: 50)"
    )

    # Gene expression operation (placeholder)
    expression_parser = subparsers.add_parser(
        "get_gene_expression", help="获取基因表达数据 (占位符)"
    )
    expression_parser.add_argument("--gene-id", "-g", required=True, help="基因ID")
    expression_parser.add_argument(
        "--species", "-s", default="human", help="物种 (默认: human)"
    )

    # Gene pathways operation (placeholder)
    pathways_parser = subparsers.add_parser(
        "get_gene_pathways", help="获取基因通路数据 (占位符)"
    )
    pathways_parser.add_argument("--gene-id", "-g", required=True, help="基因ID")
    pathways_parser.add_argument(
        "--species", "-s", default="human", help="物种 (默认: human)"
    )

    # Server info operation
    info_parser = subparsers.add_parser("server_info", help="显示服务器信息")

    # Health check operation
    health_parser = subparsers.add_parser("health_check", help="服务器健康检查")

    return parser


async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    # Initialize CLI
    cli = GenomeMCPCLI()
    await cli.initialize(args.config)

    try:
        # Special operations that don't need server execution
        if args.operation == "server_info":
            server = cli.servers[args.server]
            info = {
                "server_name": server.capabilities.name,
                "version": server.capabilities.version,
                "description": server.capabilities.description,
                "operations": server.capabilities.operations,
                "supports_batch": server.capabilities.supports_batch,
                "max_batch_size": server.capabilities.max_batch_size,
                "rate_limit": f"{server.capabilities.rate_limit_requests}/{server.capabilities.rate_limit_window}s",
            }
            result = {"operation": "server_info", "result": info}
        elif args.operation == "health_check":
            server = cli.servers[args.server]
            async with server:
                health = await server.health_check()
            result = {"operation": "health_check", "result": health}
        else:
            # Regular operations
            result = await cli.execute_command(args)

        # Format and display output
        output = cli.format_output(result, args.format)
        print(output)

    except GenomeMCPError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ 操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        print(f"❌ 意外错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
