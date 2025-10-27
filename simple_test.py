#!/usr/bin/env python3
"""
简单测试HTTP模式的MCP服务器
"""

import requests


def test_simple():
    """简单测试HTTP连接"""
    url = "http://127.0.0.1:8031/mcp"

    # 测试服务器是否可达
    try:
        response = requests.get(url)
        print(f"GET请求状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"连接失败: {e}")


if __name__ == "__main__":
    test_simple()
