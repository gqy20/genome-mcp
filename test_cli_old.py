#!/usr/bin/env python3
"""
Comprehensive test script for Genome MCP CLI functionality.

This script tests the complete CLI interface including all operations,
error handling, and output formats.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any


class CLITester:
    """CLI functionality tester."""
    
    def __init__(self):
        self.cli_path = Path(__file__).parent / "cli.py"
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def run_command(self, args: List[str], expect_success: bool = True) -> Dict[str, Any]:
        """Run a CLI command and return result."""
        # Suppress logging during tests
        env = {**os.environ, 'PYTHONPATH': str(Path(__file__).parent), 'LOG_LEVEL': 'ERROR'}
        cmd = [sys.executable, str(self.cli_path)] + args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            success = result.returncode == 0
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            # 过滤掉日志信息，只保留JSON内容
            if output and output.startswith('{'):
                # 如果是纯JSON，直接使用
                json_output = output
            elif '{' in output:
                # 如果包含日志，提取JSON部分
                json_start = output.find('{')
                json_end = output.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_output = output[json_start:json_end]
                else:
                    json_output = output
            else:
                json_output = output
            
            # 验证JSON格式
            try:
                json.loads(json_output)
            except json.JSONDecodeError:
                # 如果JSON解析失败，记录错误但不中断测试
                print(f"⚠️ JSON解析警告: 输出可能包含非JSON内容")
                print(f"前100字符: {json_output[:100]}")
                json_output = '{"error": "Failed to parse JSON output"}'
            
            test_result = {
                "command": " ".join(cmd),
                "success": success,
                "expected_success": expect_success,
                "output": output,
                "json_output": json_output,
                "error": error,
                "return_code": result.returncode
            }
            
            if success == expect_success:
                self.passed += 1
                test_result["status"] = "PASS"
            else:
                self.failed += 1
                test_result["status"] = "FAIL"
            
            self.test_results.append(test_result)
            return test_result
            
        except subprocess.TimeoutExpired:
            self.failed += 1
            timeout_result = {
                "command": " ".join(cmd),
                "success": False,
                "expected_success": expect_success,
                "output": "",
                "error": "Command timed out",
                "return_code": -1,
                "status": "TIMEOUT"
            }
            self.test_results.append(timeout_result)
            return timeout_result
        except Exception as e:
            self.failed += 1
            error_result = {
                "command": " ".join(cmd),
                "success": False,
                "expected_success": expect_success,
                "output": "",
                "error": str(e),
                "return_code": -1,
                "status": "ERROR"
            }
            self.test_results.append(error_result)
            return error_result
    
    def test_help_functionality(self):
        """Test help commands."""
        print("🧪 测试帮助功能...")
        
        # Test main help
        result = self.run_command(["--help"])
        assert "Genome MCP" in result["output"]
        assert "get_gene_info" in result["output"]
        
        # Test server-specific help
        result = self.run_command(["ncbi-gene", "--help"])
        assert "ncbi-gene" in result["output"]
        
        # Test operation-specific help
        result = self.run_command(["ncbi-gene", "get_gene_info", "--help"])
        assert "--gene-id" in result["output"]
        
        print("✅ 帮助功能测试通过")
    
    def test_server_info_and_health(self):
        """Test server information and health check commands."""
        print("🧪 测试服务器信息命令...")
        
        # Test server info
        result = self.run_command(["--format", "json", "ncbi-gene", "server_info"])
        assert result["success"]
        data = json.loads(result["json_output"])
        assert data["operation"] == "server_info"
        assert data["result"]["server_name"] == "NCBIGeneServer"
        
        # Test server info pretty format
        result = self.run_command(["--format", "pretty", "ncbi-gene", "server_info"])
        assert result["success"]
        assert "NCBIGeneServer" in result["output"]
        assert "版本" in result["output"]
        
        # Test health check
        result = self.run_command(["--format", "json", "ncbi-gene", "health_check"])
        assert result["success"]
        data = json.loads(result["json_output"])
        assert data["operation"] == "health_check"
        assert data["result"]["status"] == "healthy"
        
        print("✅ 服务器信息命令测试通过")
    
    def test_gene_operations(self):
        """Test gene information operations."""
        print("🧪 测试基因操作...")
        
        # Test gene info retrieval
        result = self.run_command([
            "--format", "json",
            "ncbi-gene", "get_gene_info",
            "--gene-id", "TP53",
            "--species", "human"
        ])
        if result["success"]:
            data = json.loads(result["json_output"])
            assert data["operation"] == "get_gene_info"
            assert data["result"]["gene_id"] == "TP53"
            assert "uid" in data["result"]
        
        # Test gene search
        result = self.run_command([
            "--format", "json",
            "ncbi-gene", "search_genes",
            "--term", "BRCA",
            "--max-results", "3"
        ])
        if result["success"]:
            data = json.loads(result["json_output"])
            assert data["operation"] == "search_genes"
            assert data["result"]["term"] == "BRCA"
            assert len(data["result"]["results"]) <= 3
        
        # Test gene summary
        result = self.run_command([
            "--format", "json",
            "ncbi-gene", "get_gene_summary",
            "--gene-id", "TP53"
        ])
        if result["success"]:
            data = json.loads(result["json_output"])
            assert data["operation"] == "get_gene_summary"
            assert data["result"]["gene_id"] == "TP53"
            assert "summary" in data["result"]
        
        print("✅ 基因操作测试通过")
    
    def test_batch_operations(self):
        """Test batch operations."""
        print("🧪 测试批量操作...")
        
        # Test batch gene info
        result = self.run_command([
            "--batch",
            "--format", "json",
            "ncbi-gene", "batch_gene_info",
            "--gene-ids", "TP53,BRCA1,EGFR"
        ])
        if result["success"]:
            data = json.loads(result["json_output"])
            assert data["operation"] == "batch_gene_info"
            assert data["batch"] == True
            assert data["result"]["total_genes"] == 3
        
        # Test batch with pretty format
        result = self.run_command([
            "--batch",
            "--format", "pretty",
            "ncbi-gene", "batch_gene_info",
            "--gene-ids", "TP53,BRCA1"
        ])
        if result["success"]:
            assert "批量" in result["output"]
            assert "成功" in result["output"]
        
        print("✅ 批量操作测试通过")
    
    def test_genomic_region_search(self):
        """Test genomic region search."""
        print("🧪 测试基因组区域搜索...")
        
        result = self.run_command([
            "--format", "json",
            "ncbi-gene", "search_by_region",
            "--chromosome", "17",
            "--start", "43044295",
            "--end", "43125483",
            "--max-results", "5"
        ])
        if result["success"]:
            data = json.loads(result["json_output"])
            assert data["operation"] == "search_by_region"
            assert "results" in data["result"]
        
        print("✅ 基因组区域搜索测试通过")
    
    def test_homologs_search(self):
        """Test gene homologs search."""
        print("🧪 测试基因同源体搜索...")
        
        result = self.run_command([
            "--format", "json",
            "ncbi-gene", "get_gene_homologs",
            "--gene-id", "TP53",
            "--species", "human"
        ])
        if result["success"]:
            data = json.loads(result["json_output"])
            assert data["operation"] == "get_gene_homologs"
            assert data["result"]["gene_id"] == "TP53"
            assert "homologs" in data["result"]
        
        print("✅ 基因同源体搜索测试通过")
    
    def test_placeholder_operations(self):
        """Test placeholder operations (expression and pathways)."""
        print("🧪 测试占位符操作...")
        
        # Test gene expression (placeholder)
        result = self.run_command([
            "--format", "json",
            "ncbi-gene", "get_gene_expression",
            "--gene-id", "TP53"
        ])
        if result["success"]:
            data = json.loads(result["json_output"])
            assert data["operation"] == "get_gene_expression"
            assert "placeholder" in data["result"]["expression"]
        
        # Test gene pathways (placeholder)
        result = self.run_command([
            "--format", "json",
            "ncbi-gene", "get_gene_pathways",
            "--gene-id", "TP53"
        ])
        if result["success"]:
            data = json.loads(result["json_output"])
            assert data["operation"] == "get_gene_pathways"
            assert "placeholder" in data["result"]["pathways"]
        
        print("✅ 占位符操作测试通过")
    
    def test_error_handling(self):
        """Test error handling."""
        print("🧪 测试错误处理...")
        
        # Test missing required argument
        result = self.run_command([
            "ncbi-gene", "get_gene_info"
        ], expect_success=False)
        assert not result["success"]
        assert "gene_id" in result["error"] or "required" in result["error"]
        
        # Test invalid operation
        result = self.run_command([
            "ncbi-gene", "invalid_operation"
        ], expect_success=False)
        assert not result["success"]
        
        # Test invalid server
        result = self.run_command([
            "invalid-server", "server_info"
        ], expect_success=False)
        assert not result["success"]
        
        print("✅ 错误处理测试通过")
    
    def test_output_formats(self):
        """Test different output formats."""
        print("🧪 测试输出格式...")
        
        # Test JSON format
        result = self.run_command([
            "--format", "json",
            "ncbi-gene", "server_info"
        ])
        if result["success"]:
            try:
                json.loads(result["json_output"])
            except json.JSONDecodeError:
                assert False, "Invalid JSON output"
        
        # Test pretty format
        result = self.run_command([
            "--format", "pretty",
            "ncbi-gene", "server_info"
        ])
        if result["success"]:
            assert "🧬" in result["output"]
            assert "服务器" in result["output"]
        
        print("✅ 输出格式测试通过")
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\n📊 测试总结:")
        print(f"   总计: {total}")
        print(f"   通过: {self.passed} ✅")
        print(f"   失败: {self.failed} ❌")
        print(f"   成功率: {self.passed/total*100:.1f}%")
        
        if self.failed > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.test_results:
                if result["status"] in ["FAIL", "TIMEOUT", "ERROR"]:
                    print(f"   • {result['command']}")
                    if result["error"]:
                        print(f"     错误: {result['error']}")
    
    def run_all_tests(self):
        """Run all CLI tests."""
        print("🚀 开始CLI功能测试...")
        print("=" * 50)
        
        try:
            self.test_help_functionality()
            self.test_server_info_and_health()
            self.test_gene_operations()
            self.test_batch_operations()
            self.test_genomic_region_search()
            self.test_homologs_search()
            self.test_placeholder_operations()
            self.test_error_handling()
            self.test_output_formats()
            
            print("=" * 50)
            self.print_summary()
            
            if self.failed == 0:
                print("\n🎉 所有CLI测试通过！")
                return True
            else:
                print(f"\n⚠️  {self.failed} 个测试失败")
                return False
                
        except Exception as e:
            print(f"\n💥 测试运行出错: {e}")
            return False


async def main():
    """Main test function."""
    tester = CLITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())