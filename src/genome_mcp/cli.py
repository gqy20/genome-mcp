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

from genome_mcp.configuration import get_config, GenomeMCPConfig
from genome_mcp.servers.ncbi.gene import NCBIGeneServer
from genome_mcp.servers.base import BaseMCPServer
from genome_mcp.exceptions import GenomeMCPError, ValidationError, DataNotFoundError

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
        """Execute CLI command."""
        command = args.command

        if command == "server":
            return await self._run_server(args)
        elif command == "query":
            return await self._query_gene(args)
        elif command == "search":
            return await self._search_genes(args)
        elif command == "batch":
            return await self._batch_query(args)
        else:
            raise ValidationError(f"Unknown command: {command}")

    async def _run_server(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Run MCP server."""
        if not self.servers:
            raise ValidationError("No servers available")

        server_name = args.server_name or "ncbi-gene"
        if server_name not in self.servers:
            raise ValidationError(f"Server not available: {server_name}")

        server = self.servers[server_name]
        await server.start()

        print(f"🚀 {server_name} 服务器正在运行...")
        print("按 Ctrl+C 停止服务器")

        try:
            # Keep server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 正在停止服务器...")
            await server.stop()
            print("✅ 服务器已停止")

        return {"status": "stopped", "server": server_name}

    async def _query_gene(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Query gene information."""
        if "ncbi-gene" not in self.servers:
            raise ValidationError("NCBI Gene server not available")

        server = self.servers["ncbi-gene"]

        result = await server.execute_request(
            "get_gene_info",
            {"gene_id": args.gene_id, "species": args.species or "human"},
        )

        gene_info = result["info"]
        print(f"🧬 基因信息: {gene_info['name']}")
        print(f"   描述: {gene_info['description']}")
        print(f"   染色体: {gene_info['chromosome']}")
        print(f"   位置: {gene_info['chrstart']:,}")

        return result

    async def _search_genes(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Search for genes."""
        if "ncbi-gene" not in self.servers:
            raise ValidationError("NCBI Gene server not available")

        server = self.servers["ncbi-gene"]

        result = await server.execute_request(
            "search_genes",
            {
                "term": args.term,
                "species": args.species or "human",
                "max_results": args.max_results or 10,
            },
        )

        print(f"🔍 搜索结果: {result['term']}")
        print(f"   找到 {len(result['results'])} 个基因")

        for gene in result["results"][:5]:  # Show first 5 results
            print(f"   - {gene['gene_id']}: {gene['description']}")

        return result

    async def _batch_query(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Batch query multiple genes."""
        if "ncbi-gene" not in self.servers:
            raise ValidationError("NCBI Gene server not available")

        server = self.servers["ncbi-gene"]

        gene_ids = args.gene_ids.split(",")
        result = await server.execute_request(
            "batch_gene_info",
            {"gene_ids": gene_ids, "species": args.species or "human"},
        )

        print(f"📊 批量查询结果:")
        print(f"   总计: {result['total_genes']} 个基因")
        print(f"   成功: {result['successful']} 个")
        print(f"   失败: {result['failed']} 个")

        for gene_result in result["results"]:
            gene_id = gene_result["gene_id"]
            if gene_result["success"]:
                info = gene_result["data"]["info"]
                print(f"   ✅ {gene_id}: {info['name']}")
            else:
                print(f"   ❌ {gene_id}: {gene_result['error']}")

        return result


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="genome-mcp",
        description="Genome MCP Server - Genomic Data Access Tool",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser("server", help="Run MCP server")
    server_parser.add_argument(
        "--server-name",
        default="ncbi-gene",
        help="Server name to run (default: ncbi-gene)",
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Query gene information")
    query_parser.add_argument("gene_id", help="Gene ID (e.g., TP53)")
    query_parser.add_argument("--species", default="human", help="Species name")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for genes")
    search_parser.add_argument("term", help="Search term")
    search_parser.add_argument("--species", default="human", help="Species name")
    search_parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum results"
    )

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch query multiple genes")
    batch_parser.add_argument("gene_ids", help="Comma-separated gene IDs")
    batch_parser.add_argument("--species", default="human", help="Species name")

    return parser


async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = GenomeMCPCLI()
    await cli.initialize()

    try:
        result = await cli.execute_command(args)
        if args.command != "server":  # Don't print result for server command
            print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error("Command execution failed", error=str(e))
        print(f"❌ 命令执行失败: {e}")
        sys.exit(1)


def cli_entry_point():
    """Synchronous entry point for the CLI."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_entry_point()