"""
Test script for BaseMCPServer implementation.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from genome_mcp.configuration import GenomeMCPConfig
from genome_mcp.servers.base import BaseMCPServer, ServerCapabilities


class TestServer(BaseMCPServer):
    """Test server implementation."""

    def _define_capabilities(self) -> ServerCapabilities:
        return ServerCapabilities(
            name="TestServer",
            version="1.0.0",
            description="Test MCP Server",
            operations=["test_operation", "echo"],
            supports_streaming=True,
            max_batch_size=50,
            rate_limit_requests=100,
        )

    def _get_base_url(self) -> str:
        return "https://api.test.com"

    async def _execute_operation(
        self, operation: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        if operation == "test_operation":
            return {"message": "Test operation successful", "params": params}
        elif operation == "echo":
            return {"echo": params.get("message", "No message")}
        else:
            raise ValueError(f"Unknown operation: {operation}")


async def test_base_server():
    """Test BaseMCPServer functionality."""
    print("🧪 测试基础服务器类...")

    # Test server initialization
    config = GenomeMCPConfig()
    server = TestServer(config)

    print(f"✓ 服务器初始化: {server.capabilities.name} v{server.capabilities.version}")

    # Test server start/stop
    await server.start()
    assert server._running == True
    print("✓ 服务器启动成功")

    await server.stop()
    assert server._running == False
    print("✓ 服务器停止成功")

    # Test async context manager
    async with TestServer(config) as server_ctx:
        assert server_ctx._running == True
        print("✓ 异步上下文管理器工作正常")

    # Test health check
    async with TestServer(config) as server:
        health = await server.health_check()
        assert health["status"] == "healthy"
        assert health["server"] == "TestServer"
        print("✓ 健康检查功能正常")

    # Test single request execution
    async with TestServer(config) as server:
        result = await server.execute_request("test_operation", {"key": "value"})
        assert result["message"] == "Test operation successful"
        assert result["params"]["key"] == "value"
        print("✓ 单个请求执行成功")

    # Test batch request execution
    async with TestServer(config) as server:
        requests = [
            {"operation": "echo", "params": {"message": "Hello"}},
            {"operation": "echo", "params": {"message": "World"}},
        ]
        results = await server.execute_batch(requests)
        assert len(results) == 2
        assert all(r["success"] for r in results)
        assert results[0]["result"]["echo"] == "Hello"
        assert results[1]["result"]["echo"] == "World"
        print("✓ 批量请求执行成功")

    # Test streaming
    async with TestServer(config) as server:
        stream_result = []
        async for chunk in server.execute_stream("echo", {"message": "Stream test"}):
            stream_result.append(chunk)

        assert len(stream_result) == 1
        assert stream_result[0]["data"]["echo"] == "Stream test"
        print("✓ 流式请求执行成功")

    # Test error handling
    async with TestServer(config) as server:
        try:
            await server.execute_request("invalid_operation", {})
            assert False, "Should have raised ValidationError"
        except Exception as e:
            assert "ValidationError" in str(type(e))
            print("✓ 错误处理正常")

    # Test stats
    async with TestServer(config) as server:
        # Execute some requests to generate stats
        await server.execute_request("test_operation", {})
        await server.execute_request("echo", {"message": "test"})

        stats = server.get_stats()
        assert stats["stats"]["requests_total"] >= 2
        assert stats["stats"]["requests_success"] >= 2
        print("✓ 统计功能正常")

    print("✅ 基础服务器类测试通过")


if __name__ == "__main__":
    asyncio.run(test_base_server())
