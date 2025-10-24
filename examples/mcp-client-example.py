#!/usr/bin/env python3
"""
MCP客户端示例 - 演示如何连接和使用Genome MCP服务器
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List


class MCPClient:
    def __init__(self, command: List[str]):
        self.process = None
        self.command = command
        self.request_id = 1

    async def start(self):
        """启动MCP服务器进程"""
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            text=True
        )
        print(f"MCP服务器已启动: {' '.join(self.command)}")

    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送JSON-RPC消息并接收响应"""
        if not self.process:
            raise RuntimeError("MCP服务器未启动")

        message_str = json.dumps(message) + "\n"
        self.process.stdin.write(message_str)
        await self.process.stdin.drain()

        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("MCP服务器连接断开")

        return json.loads(response_line.strip())

    async def initialize(self) -> Dict[str, Any]:
        """初始化MCP连接"""
        init_message = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True}
                },
                "clientInfo": {
                    "name": "genome-mcp-example-client",
                    "version": "1.0.0"
                }
            }
        }
        self.request_id += 1

        response = await self.send_message(init_message)
        print("✓ MCP连接已初始化")
        return response

    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        tools_message = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/list"
        }
        self.request_id += 1

        response = await self.send_message(tools_message)
        tools = response.get("result", {}).get("tools", [])
        print(f"✓ 发现 {len(tools)} 个可用工具")
        return tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用MCP工具"""
        call_message = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        self.request_id += 1

        response = await self.send_message(call_message)
        result = response.get("result", {})
        print(f"✓ 工具 '{tool_name}' 调用成功")
        return result

    async def close(self):
        """关闭MCP连接"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("✓ MCP连接已关闭")


async def main():
    """主函数 - 演示MCP客户端使用"""
    client = MCPClient(["python", "-m", "genome_mcp"])

    try:
        # 启动MCP服务器
        await client.start()

        # 初始化连接
        await client.initialize()

        # 获取工具列表
        tools = await client.list_tools()
        print("\n可用工具:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', '无描述')}")

        # 调用基因信息查询
        print("\n查询TP53基因信息...")
        gene_info = await client.call_tool("get_gene_info", {"gene_id": "TP53"})
        print(f"基因信息: {json.dumps(gene_info, indent=2, ensure_ascii=False)}")

        # 调用基因搜索
        print("\n搜索与癌症相关的基因...")
        search_results = await client.call_tool("search_genes", {
            "query": "cancer",
            "max_results": 5
        })
        print(f"搜索结果: {json.dumps(search_results, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"错误: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())