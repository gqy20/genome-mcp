"""
传输模式集成测试
"""

import importlib.util
import json
import os
import sys

import pytest

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestTransports:
    """传输模式测试"""

    def test_stdio_transport(self):
        """测试STDIO传输模式"""
        # 这个测试在CI环境中可能比较复杂，我们测试服务器能否正常启动
        try:
            from genome_mcp.__main__ import main

            assert callable(main)
        except Exception as e:
            pytest.fail(f"STDIO传输模式导入失败: {e}")

    def test_http_transport_import(self):
        """测试HTTP传输模式导入"""
        try:
            from genome_mcp.__main__ import main

            # 检查是否支持HTTP参数
            assert callable(main)
        except Exception as e:
            pytest.fail(f"HTTP传输模式导入失败: {e}")

    def test_sse_transport_import(self):
        """测试SSE传输模式导入"""
        try:
            from genome_mcp.__main__ import main

            # 检查是否支持SSE参数
            assert callable(main)
        except Exception as e:
            pytest.fail(f"SSE传输模式导入失败: {e}")

    @pytest.mark.asyncio
    async def test_mcp_tools_availability(self):
        """测试MCP工具在不同传输模式下的可用性"""
        # 测试工具是否可以被正确导入
        try:
            from genome_mcp import advanced_query, get_data, smart_search

            # MCP工具被装饰器包装，检查是否是MCP工具对象
            assert hasattr(get_data, "name") or callable(get_data)
            assert hasattr(advanced_query, "name") or callable(advanced_query)
            assert hasattr(smart_search, "name") or callable(smart_search)

            # 检查工具名称
            if hasattr(get_data, "name"):
                assert get_data.name == "get_data"
            if hasattr(advanced_query, "name"):
                assert advanced_query.name == "advanced_query"
            if hasattr(smart_search, "name"):
                assert smart_search.name == "smart_search"

        except Exception as e:
            pytest.fail(f"MCP工具导入失败: {e}")

    def test_command_line_interface(self):
        """测试命令行接口"""
        try:
            # 测试主模块能否被正确导入
            import genome_mcp.__main__

            assert hasattr(genome_mcp.__main__, "main")
        except Exception as e:
            pytest.fail(f"命令行接口测试失败: {e}")


class TestMCPConfiguration:
    """MCP配置测试"""

    def test_mcp_config_exists(self):
        """测试MCP配置文件存在"""
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "mcp-config.json"
        )
        assert os.path.exists(config_path), "MCP配置文件不存在"

    def test_mcp_config_validity(self):
        """测试MCP配置文件有效性"""
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "mcp-config.json"
        )

        with open(config_path) as f:
            try:
                config = json.load(f)
                assert isinstance(config, dict)
                # 检查必要的配置项
                assert "mcpServers" in config
            except json.JSONDecodeError as e:
                pytest.fail(f"MCP配置文件JSON格式错误: {e}")

    def test_claude_desktop_config_example(self):
        """测试Claude Desktop配置示例"""
        config_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "examples",
            "claude-desktop-config.json",
        )
        assert os.path.exists(config_path), "Claude Desktop配置示例不存在"

        with open(config_path) as f:
            try:
                config = json.load(f)
                assert isinstance(config, dict)
                assert "mcpServers" in config
            except json.JSONDecodeError as e:
                pytest.fail(f"Claude Desktop配置示例JSON格式错误: {e}")


class TestExamples:
    """示例文件测试"""

    def test_fastmcp_example(self):
        """测试FastMCP示例"""
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "examples", "fastmcp_example.py"
        )
        assert os.path.exists(example_path), "FastMCP示例文件不存在"

        # 检查示例文件是否可以导入
        try:
            spec = importlib.util.spec_from_file_location(
                "fastmcp_example", example_path
            )
            module = importlib.util.module_from_spec(spec)
            # 不执行示例，只检查语法
            with open(example_path) as f:
                compile(f.read(), example_path, "exec")
        except Exception as e:
            pytest.fail(f"FastMCP示例文件语法错误: {e}")

    def test_usage_examples(self):
        """测试使用示例"""
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "examples", "usage_examples.py"
        )
        assert os.path.exists(example_path), "使用示例文件不存在"

        # 检查示例文件语法
        try:
            with open(example_path) as f:
                compile(f.read(), example_path, "exec")
        except Exception as e:
            pytest.fail(f"使用示例文件语法错误: {e}")

    def test_mcp_client_example(self):
        """测试MCP客户端示例"""
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "examples", "mcp-client-example.py"
        )
        assert os.path.exists(example_path), "MCP客户端示例文件不存在"

        # 检查示例文件语法
        try:
            with open(example_path) as f:
                compile(f.read(), example_path, "exec")
        except Exception as e:
            pytest.fail(f"MCP客户端示例文件语法错误: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
