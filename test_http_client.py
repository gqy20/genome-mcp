#!/usr/bin/env python3
"""
测试HTTP模式的MCP服务器
"""

import asyncio
import json

import aiohttp


async def test_http_mcp():
    """测试HTTP模式的MCP服务器"""
    url = "http://127.0.0.1:8031/mcp"

    async with aiohttp.ClientSession() as session:
        # 首先建立连接
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }

        session_id = None

        # 初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        # 获取工具列表请求
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        try:
            # 先初始化连接
            async with session.post(
                url, headers=headers, json=init_request
            ) as response:
                print(f"初始化响应状态: {response.status}")
                if response.status == 200:
                    print("✅ MCP服务器初始化成功!")
                    # 获取session ID
                    session_id = response.headers.get("mcp-session-id")
                    print(f"会话ID: {session_id}")

                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if line:
                            print(f"收到初始化数据: {line}")
                            if line.startswith("data: "):
                                data = line[6:]  # 移除 'data: ' 前缀
                                try:
                                    json_data = json.loads(data)
                                    print(
                                        f"服务器信息: {json_data['result']['serverInfo']}"
                                    )
                                    break  # 只读取第一个响应
                                except json.JSONDecodeError:
                                    pass
                    print()

            # 使用session ID获取工具列表
            if session_id:
                headers["mcp-session-id"] = session_id
                async with session.post(
                    url, headers=headers, json=tools_request
                ) as response:
                    print(f"工具列表响应状态: {response.status}")

                if response.status == 200:
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if line:
                            print(f"收到数据: {line}")
                            if line.startswith("data: "):
                                data = line[6:]  # 移除 'data: ' 前缀
                                try:
                                    json_data = json.loads(data)
                                    print(f"解析的JSON: {json_data}")
                                    break  # 只读取第一个响应
                                except json.JSONDecodeError:
                                    print(f"无法解析JSON: {data}")
                else:
                    text = await response.text()
                    print(f"错误响应: {text}")

        except Exception as e:
            print(f"请求失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_http_mcp())
