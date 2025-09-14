#!/usr/bin/env python3
"""
Simplified CLI test script.

This script tests the CLI functionality with robust JSON parsing.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def extract_json_from_output(output):
    """Extract JSON from CLI output that may contain log messages."""
    if not output:
        return None

    # Find the JSON object - look for proper JSON structure
    lines = output.split("\n")
    json_lines = []
    in_json = False
    brace_count = 0

    for line in lines:
        if line.strip().startswith("{"):
            in_json = True
            brace_count = 1
            json_lines = [line]
        elif in_json:
            json_lines.append(line)
            # Count braces to determine when JSON object ends
            for char in line:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        # Found complete JSON object
                        return "\n".join(json_lines)

    # If we didn't find a complete JSON object, try the old method
    json_start = output.find("{")
    if json_start == -1:
        return None

    # Find the matching closing brace
    brace_count = 0
    json_end = json_start
    for i in range(json_start, len(output)):
        if output[i] == "{":
            brace_count += 1
        elif output[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break

    if json_end > json_start:
        return output[json_start:json_end]
    return None


def test_command(args, description):
    """Test a CLI command."""
    print(f"\n🧪 {description}")
    print(f"命令: python cli.py {' '.join(args)}")

    try:
        result = subprocess.run(
            ["python", "cli.py"] + args, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            print("✅ 命令执行成功")

            # Try to extract and parse JSON
            json_str = extract_json_from_output(result.stdout)
            if json_str:
                try:
                    data = json.loads(json_str)
                    print(f"📦 操作: {data.get('operation', 'unknown')}")

                    if "result" in data:
                        result_data = data["result"]
                        if "server_name" in result_data:
                            print(f"🏷️ 服务器: {result_data['server_name']}")
                        if "term" in result_data:
                            print(f"🔍 搜索词: {result_data['term']}")
                        if "total_count" in result_data:
                            print(f"📊 总数: {result_data['total_count']}")
                        if "gene_id" in result_data:
                            print(f"🧬 基因ID: {result_data['gene_id']}")

                    return True
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON解析错误: {e}")
                    return False
            else:
                print("⚠️ 未找到JSON输出")
                return False
        else:
            print(f"❌ 命令执行失败: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ 命令超时")
        return False
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return False


def main():
    """Run CLI tests."""
    print("🚀 Genome MCP CLI 简化测试")
    print("=" * 50)

    tests_passed = 0
    tests_total = 0

    # Test server info
    tests_total += 1
    if test_command(["--format", "json", "ncbi-gene", "server_info"], "服务器信息"):
        tests_passed += 1

    # Test health check
    tests_total += 1
    if test_command(["--format", "json", "ncbi-gene", "health_check"], "健康检查"):
        tests_passed += 1

    # Test gene search
    tests_total += 1
    if test_command(
        [
            "--format",
            "json",
            "ncbi-gene",
            "search_genes",
            "--term",
            "TP53",
            "--max-results",
            "3",
        ],
        "基因搜索",
    ):
        tests_passed += 1

    # Test gene info
    tests_total += 1
    if test_command(
        ["--format", "json", "ncbi-gene", "get_gene_info", "--gene-id", "TP53"],
        "基因信息",
    ):
        tests_passed += 1

    # Test gene summary
    tests_total += 1
    if test_command(
        ["--format", "json", "ncbi-gene", "get_gene_summary", "--gene-id", "TP53"],
        "基因摘要",
    ):
        tests_passed += 1

    # Test batch gene info
    tests_total += 1
    if test_command(
        [
            "--batch",
            "--format",
            "json",
            "ncbi-gene",
            "batch_gene_info",
            "--gene-ids",
            "TP53,BRCA1",
        ],
        "批量基因信息",
    ):
        tests_passed += 1

    # Test region search
    tests_total += 1
    if test_command(
        [
            "--format",
            "json",
            "ncbi-gene",
            "search_by_region",
            "--chromosome",
            "17",
            "--start",
            "43044295",
            "--end",
            "43125483",
            "--max-results",
            "5",
        ],
        "区域搜索",
    ):
        tests_passed += 1

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {tests_passed}/{tests_total} 通过")

    if tests_passed == tests_total:
        print("🎉 所有测试通过！")
        return True
    else:
        print(f"⚠️  {tests_total - tests_passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
