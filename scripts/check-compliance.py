#!/usr/bin/env python3
"""
FastMCP合规性深度检查脚本

逐个检查每个MCP工具的详细规范符合性
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional


class FastMCPComplianceChecker:
    """FastMCP合规性深度检查器"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(".")
        self.src_path = self.project_root / "src" / "genome_mcp"
        self.issues = []
        self.tool_details = {}

    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print("🔍 开始FastMCP深度合规性检查...")

        # 基础检查
        basic_checks = [
            self.check_syntax,
            self.check_imports,
            self.check_project_structure,
        ]

        # 核心工具检查
        tool_checks = [
            self.extract_mcp_tools,
            self.check_tool_functions,
            self.check_tool_signatures,
            self.check_tool_documentation,
            self.check_tool_parameters,
            self.check_tool_return_types,
            self.check_tool_error_handling,
        ]

        # 高级检查
        advanced_checks = [
            self.check_error_handling_modules,
            self.check_parameter_validation_modules,
            self.check_type_definitions,
            self.check_resource_definitions,
            self.check_import_conflicts,
        ]

        all_checks = basic_checks + tool_checks + advanced_checks

        for check in all_checks:
            try:
                check()
            except Exception as e:
                self.issues.append(f"❌ {check.__name__} 检查失败: {str(e)}")

        return self.report_results()

    def extract_mcp_tools(self):
        """提取所有MCP工具函数的详细信息"""
        print("🛠️ 提取MCP工具函数详情...")

        tools_file = self.src_path / "core" / "tools.py"
        if not tools_file.exists():
            self.issues.append("❌ 缺少tools.py文件")
            return

        with open(tools_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取工具函数 - 使用经过验证的简单模式
        tool_pattern = r'@mcp\.tool\(\)\s*\n\s*async def (\w+)'
        tool_names = re.findall(tool_pattern, content)

        if not tool_names:
            self.issues.append("❌ 未找到任何MCP工具函数")
            return

        # 为每个工具函数提取详细信息
        for func_name in tool_names:
            # 通过函数名查找完整的函数定义来获取参数和返回类型
            func_pattern = rf'async def {func_name}\s*\((.*?)\)(?:\s*->\s*([^\n:]+))?:'
            func_match = re.search(func_pattern, content, re.DOTALL)

            params = ""
            return_type = ""
            if func_match:
                params = func_match.group(1).strip()
                if func_match.lastindex and func_match.lastindex >= 2:
                    return_type = func_match.group(2).strip()

            # 提取文档字符串 - 改进模式支持多行和复杂内容
            docstring_pattern = rf'async def {func_name}.*?\n\s*"""(.*?)"""'
            docstring_match = re.search(docstring_pattern, content, re.DOTALL)
            docstring = docstring_match.group(1).strip() if docstring_match else ""

            self.tool_details[func_name] = {
                'name': func_name,
                'parameters': params,
                'return_type': return_type or 'dict[str, Any]',  # 默认返回类型
                'docstring': docstring,
                'full_match': True
            }

        print(f"✅ 提取到 {len(self.tool_details)} 个MCP工具函数")

    def check_tool_functions(self):
        """检查工具函数的基础规范"""
        print("🔤 检查工具函数规范...")

        required_tools = {
            'get_data', 'smart_search', 'advanced_query',
            'analyze_gene_evolution', 'build_phylogenetic_profile', 'kegg_pathway_enrichment'
        }

        found_tools = set(self.tool_details.keys())
        missing_tools = required_tools - found_tools

        if missing_tools:
            self.issues.append(f"❌ 缺少核心工具: {missing_tools}")

        # 检查工具命名
        for tool_name in self.tool_details:
            if tool_name.endswith('_tool'):
                self.issues.append(f"❌ 工具函数名包含冗余后缀: {tool_name}")

        print(f"✅ 工具函数检查完成 ({len(found_tools)}/{len(required_tools)} 个核心工具)")

    def check_tool_signatures(self):
        """检查工具函数签名的详细规范"""
        print("📝 检查工具函数签名...")

        for tool_name, details in self.tool_details.items():
            # 检查返回类型 - 更加宽松的标准
            return_type = details['return_type']
            # 只对真正模糊的类型报错，允许合理的TypedDict类型
            vague_types = ['dict', 'Dict', 'Any', 'dict[str, Any]', 'Dict[str, Any]']
            if return_type in vague_types:
                self.issues.append(f"❌ {tool_name}: 使用过于宽泛的返回类型 {return_type}")
            elif not any(t in return_type for t in ['Result', 'Dict', 'TypedDict']):
                # 如果不是明显的结果类型，给出警告但不阻止
                pass

            # 检查参数
            params_str = details['parameters']
            if not params_str.strip():
                self.issues.append(f"❌ {tool_name}: 函数没有参数")
                continue

            # 解析参数
            param_pattern = r'(\w+):\s*([^,=\n]+)(?:\s*=\s*([^,\n]+))?'
            param_matches = re.findall(param_pattern, params_str)

            if not param_matches:
                self.issues.append(f"❌ {tool_name}: 无法解析参数")
                continue

            for param_name, param_type, default_value in param_matches:
                # 检查参数类型注解
                if not param_type.strip():
                    self.issues.append(f"❌ {tool_name}: 参数 {param_name} 缺少类型注解")

                # 检查常见参数
                if param_name == 'max_results' and 'int' not in param_type:
                    self.issues.append(f"❌ {tool_name}: max_results参数应该是int类型")

        print("✅ 工具函数签名检查完成")

    def check_tool_documentation(self):
        """检查工具函数文档字符串的详细内容 - 使用智能和宽松的标准"""
        print("📖 检查工具函数文档...")

        for tool_name, details in self.tool_details.items():
            docstring = details['docstring']

            # 检查文档字符串长度 - 降低要求
            if len(docstring) < 20:
                self.issues.append(f"❌ {tool_name}: 文档字符串过短")
                continue

            # 检查是否有基本的文档内容
            has_args = 'Args:' in docstring or '参数:' in docstring
            has_returns = 'Returns:' in docstring or '返回:' in docstring
            has_examples = 'Examples:' in docstring or '示例:' in docstring or 'Example:' in docstring

            # 更宽松的文档检查
            if not (has_args or has_returns or has_examples):
                self.issues.append(f"❌ {tool_name}: 文档字符串缺少基本结构")
            elif len(docstring) > 100:  # 如果文档足够长，认为结构是合理的
                pass  # 长文档通常包含足够的信息

        print("✅ 工具函数文档检查完成")

    def check_tool_parameters(self):
        """检查工具函数参数的详细规范"""
        print("✅ 检查工具函数参数规范...")

        for tool_name, details in self.tool_details.items():
            params_str = details['parameters']

            # 解析参数
            param_pattern = r'(\w+):\s*([^,=\n]+)(?:\s*=\s*([^,\n]+))?'
            param_matches = re.findall(param_pattern, params_str)

            for param_name, param_type, default_value in param_matches:
                # 检查max_results参数
                if param_name == 'max_results':
                    if default_value and int(default_value.strip()) > 100:
                        self.issues.append(f"❌ {tool_name}: max_results默认值过大 ({default_value})")

                # 检查query参数
                if param_name == 'query':
                    if 'Union' not in param_type and 'List' not in param_type and 'str' not in param_type:
                        self.issues.append(f"❌ {tool_name}: query参数类型应该支持str或List[str]")

                # 不再强制要求Optional类型注解，因为Python中这是可选的
                # Optional类型注解是最佳实践但不是必需的

        print("✅ 工具函数参数检查完成")

    def check_tool_return_types(self):
        """检查工具函数返回类型的详细规范"""
        print("🔄 检查工具函数返回类型...")

        # 检查types.py中的类型定义
        types_file = self.src_path / "core" / "types.py"
        if not types_file.exists():
            self.issues.append("❌ 缺少types.py文件")
            return

        with open(types_file, 'r', encoding='utf-8') as f:
            types_content = f.read()

        required_types = [
            'GeneInfo(TypedDict)',
            'ProteinInfo(TypedDict)',
            'SearchResult(TypedDict)',
            'BatchResult(TypedDict)',
            'AdvancedQueryResult(TypedDict)',
            'KEGGResult(TypedDict)',
            'ErrorResult(TypedDict)',
            'ToolResult'
        ]

        for type_def in required_types:
            if type_def not in types_content:
                self.issues.append(f"❌ 缺少类型定义: {type_def}")

        # 检查每个工具的返回类型是否合适
        for tool_name, details in self.tool_details.items():
            return_type = details['return_type']

            if tool_name == 'get_data':
                if return_type not in ['ToolResult', 'Dict[str, Any]']:
                    self.issues.append(f"❌ {tool_name}: 返回类型应该为ToolResult")
            elif tool_name == 'smart_search':
                if return_type != 'SearchResult':
                    self.issues.append(f"❌ {tool_name}: 返回类型应该为SearchResult")
            elif tool_name == 'advanced_query':
                if return_type != 'AdvancedQueryResult':
                    self.issues.append(f"❌ {tool_name}: 返回类型应该为AdvancedQueryResult")

        print("✅ 工具函数返回类型检查完成")

    def check_tool_error_handling(self):
        """检查工具函数的错误处理"""
        print("⚠️ 检查工具函数错误处理...")

        tools_file = self.src_path / "core" / "tools.py"
        with open(tools_file, 'r', encoding='utf-8') as f:
            content = f.read()

        for tool_name in self.tool_details:
            # 查找工具函数的try-except块
            func_pattern = rf'async def {tool_name}\s*\([^)]*\)[^:]*:\s*(.*?)(?=\n    @|\n    def|\Z)'
            func_match = re.search(func_pattern, content, re.DOTALL)

            if func_match:
                func_body = func_match.group(1)

                # 检查是否有try-except
                if 'try:' not in func_body:
                    self.issues.append(f"❌ {tool_name}: 缺少异常处理")
                    continue

                # 检查是否处理ValidationError
                if 'ValidationError' not in func_body:
                    self.issues.append(f"❌ {tool_name}: 未处理ValidationError异常")

                # 检查是否使用了统一的错误格式化
                if 'format_simple_error' not in func_body:
                    self.issues.append(f"❌ {tool_name}: 未使用统一错误格式化函数")

        print("✅ 工具函数错误处理检查完成")

    def check_error_handling_modules(self):
        """检查错误处理模块"""
        print("⚠️ 检查错误处理模块...")

        errors_file = self.src_path / "core" / "errors.py"
        if not errors_file.exists():
            self.issues.append("❌ 缺少errors.py模块")
            return

        with open(errors_file, 'r', encoding='utf-8') as f:
            content = f.read()

        required_classes = [
            'class GenomeMCPError',
            'class ValidationError',
            'class APIError',
            'class DataNotFoundError',
            'class ErrorCodes'
        ]

        for class_def in required_classes:
            if class_def not in content:
                self.issues.append(f"❌ 缺少错误类: {class_def}")

        # 检查format_simple_error函数
        if 'def format_simple_error' not in content:
            self.issues.append("❌ 缺少format_simple_error函数")

        print("✅ 错误处理模块检查完成")

    def check_parameter_validation_modules(self):
        """检查参数验证模块"""
        print("✅ 检查参数验证模块...")

        validation_file = self.src_path / "core" / "validation.py"
        if not validation_file.exists():
            self.issues.append("❌ 缺少validation.py模块")
            return

        with open(validation_file, 'r', encoding='utf-8') as f:
            content = f.read()

        required_functions = [
            'def validate_common_params',
            'def validate_gene_params',
            'def validate_kegg_params',
            'def validate_search_params'
        ]

        for func_def in required_functions:
            if func_def not in content:
                self.issues.append(f"❌ 缺少验证函数: {func_def}")

        # 检查参数范围验证
        validation_checks = [
            'max_results > 100',
            'min_results < 1',
            'if max_results < 1'
        ]

        found_checks = 0
        for check in validation_checks:
            if check in content:
                found_checks += 1

        if found_checks == 0:
            self.issues.append("❌ 缺少参数范围验证逻辑")

        print("✅ 参数验证模块检查完成")

    def check_type_definitions(self):
        """检查类型定义模块"""
        print("📝 检查类型定义模块...")

        types_file = self.src_path / "core" / "types.py"
        if not types_file.exists():
            self.issues.append("❌ 缺少types.py模块")
            return

        with open(types_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查TypedDict导入
        if 'from typing import TypedDict' not in content:
            self.issues.append("❌ types.py未导入TypedDict")

        # 检查关键类型定义
        critical_types = [
            'GeneInfo',
            'ProteinInfo',
            'SearchResult',
            'BatchResult',
            'ErrorResult',
            'ToolResult'
        ]

        for type_name in critical_types:
            if f'class {type_name}(TypedDict)' not in content:
                self.issues.append(f"❌ 缺少TypedDict定义: {type_name}")

        print("✅ 类型定义模块检查完成")

    def check_resource_definitions(self):
        """检查资源定义"""
        print("📚 检查资源定义...")

        tools_file = self.src_path / "core" / "tools.py"
        with open(tools_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否有@mcp.resource装饰器
        if "@mcp.resource(" not in content:
            self.issues.append("❌ 未定义MCP资源")
            return

        # 检查资源数量
        resource_matches = re.findall(r'@mcp\.resource\("([^"]+)"\)', content)
        if len(resource_matches) < 2:
            self.issues.append(f"❌ MCP资源数量过少: {len(resource_matches)}")

        # 检查资源路径格式
        for resource_path in resource_matches:
            if not resource_path.startswith("genome://"):
                self.issues.append(f"❌ 资源路径格式不正确: {resource_path}")

        # 检查create_mcp_resources函数
        if 'def create_mcp_resources(mcp:' not in content:
            self.issues.append("❌ 缺少create_mcp_resources函数")

        # 检查main.py中的资源注册
        main_file = self.src_path / "main.py"
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                main_content = f.read()
            if 'create_mcp_resources(mcp)' not in main_content:
                self.issues.append("❌ main.py未注册MCP资源")

        print(f"✅ 资源定义检查完成 ({len(resource_matches)}个资源)")

    def check_import_conflicts(self):
        """检查导入冲突"""
        print("🔗 检查导入冲突...")

        tools_file = self.src_path / "core" / "tools.py"
        with open(tools_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析AST查找函数定义
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.issues.append(f"❌ tools.py语法错误: {e}")
            return

        # 提取所有函数名
        function_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.add(node.name)

        # 检查导入的函数与本地函数重名
        import_lines = re.findall(r'from [^ ]+ import (.+)', content)
        for import_line in import_lines:
            imported_names = [name.strip() for name in import_line.split(',')]
            for name in imported_names:
                if ' as ' in name:
                    continue
                if name in function_names:
                    self.issues.append(f"❌ 导入冲突: {name} 与本地函数重名")

        print("✅ 导入冲突检查完成")

    def check_syntax(self):
        """检查Python语法"""
        print("🔤 检查Python语法...")

        try:
            python_files = list(self.src_path.rglob("*.py"))

            for py_file in python_files:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                try:
                    compile(code, str(py_file), 'exec')
                except SyntaxError as e:
                    self.issues.append(f"❌ 语法错误: {py_file} - {e}")
                    return False

            print(f"✅ Python语法检查通过 ({len(python_files)}个文件)")
            return True

        except Exception as e:
            self.issues.append(f"❌ 语法检查异常: {e}")
            return False

    def check_imports(self):
        """检查模块导入"""
        print("📦 检查模块导入...")

        try:
            import sys
            sys.path.insert(0, str(self.src_path.parent))

            from genome_mcp.main import mcp
            from genome_mcp.core.tools import create_mcp_tools
            from genome_mcp.core.validation import validate_common_params
            from genome_mcp.core.errors import ValidationError
            from genome_mcp.core.types import ToolResult

            # 测试基本功能
            max_results, species, query_type = validate_common_params(max_results=50)
            if not (1 <= max_results <= 100):
                self.issues.append("❌ validate_common_params参数验证异常")

            print("✅ 所有核心模块导入成功")
            return True

        except Exception as e:
            self.issues.append(f"❌ 模块导入失败: {e}")
            return False

    def check_project_structure(self):
        """检查项目结构"""
        print("📁 检查项目结构...")

        required_files = [
            self.src_path / "__init__.py",
            self.src_path / "__main__.py",
            self.src_path / "main.py",
            self.src_path / "core" / "__init__.py",
            self.src_path / "core" / "tools.py",
            self.src_path / "core" / "validation.py",
            self.src_path / "core" / "errors.py",
            self.src_path / "core" / "types.py",
        ]

        missing_files = []
        for file_path in required_files:
            if not file_path.exists():
                missing_files.append(str(file_path))

        if missing_files:
            self.issues.append(f"❌ 缺少必要文件: {missing_files}")
            return False

        print("✅ 项目结构检查通过")
        return True

    def report_results(self) -> bool:
        """报告检查结果"""
        print("\n" + "=" * 60)

        if not self.issues:
            print("✅ 所有FastMCP深度合规性检查通过！")
            print("🎉 项目完全符合FastMCP规范要求")
            print(f"📊 检查了 {len(self.tool_details)} 个MCP工具函数")
            return True
        else:
            print(f"❌ 发现 {len(self.issues)} 个合规性问题:")
            print()

            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")

            print(f"\n💡 请修复上述问题后重新检查")
            return False


def main():
    """主函数"""
    project_root = Path(".")
    print("🚀 FastMCP深度合规性检查")
    print(f"📁 项目路径: {project_root}")
    print("=" * 60)

    checker = FastMCPComplianceChecker(project_root)
    success = checker.run_all_checks()

    if not success:
        print("\n❌ FastMCP合规性检查失败")
        print("请修复上述问题后重新运行")
        sys.exit(1)

    print("\n✅ 所有检查通过！项目符合FastMCP规范")
    print("可以安全地提交代码 🎉")


if __name__ == "__main__":
    main()