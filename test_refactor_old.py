#!/usr/bin/env python3
"""
Genome MCP 使用效果测试脚本

此脚本验证重构后的项目是否正常工作，包括：
1. 核心功能测试
2. 异常处理测试
3. 配置管理测试
4. 数据处理测试
5. HTTP客户端测试
"""

import sys
import os
import asyncio
import tempfile
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 导入异常模块
import exceptions

def test_core_functionality():
    """测试核心功能"""
    print("🔧 测试核心功能...")
    
    # 测试缓存键生成
    from core import generate_cache_key, format_duration, format_file_size
    
    key = generate_cache_key("test", "gene:TP53", species="homo_sapiens")
    assert key.startswith("test:")
    print(f"✓ 缓存键生成: {key[:50]}...")
    
    # 测试格式化功能
    duration = format_duration(125.5)
    assert duration == "2m 5.5s"
    print(f"✓ 时长格式化: {duration}")
    
    size = format_file_size(1024 * 1024 * 2.5)
    assert "MB" in size
    print(f"✓ 文件大小格式化: {size}")
    
    print("✅ 核心功能测试通过")

def test_exception_handling():
    """测试异常处理"""
    print("🚨 测试异常处理...")
    
    from exceptions import (
        ValidationError, 
        APIError, 
        NetworkError, 
        DataNotFoundError,
        create_error_from_exception
    )
    
    # 测试基本异常
    try:
        raise ValidationError("测试验证错误", field_name="test_field")
    except ValidationError as e:
        assert e.field_name == "test_field"
        assert e.error_code == "VALIDATION_ERROR"
        print("✓ 验证异常正常工作")
    
    # 测试API异常
    try:
        raise APIError("API调用失败", status_code=404, url="https://api.test.com")
    except APIError as e:
        assert e.status_code == 404
        assert "api.test.com" in e.url
        print("✓ API异常正常工作")
    
    # 测试异常创建
    original = ValueError("原始错误")
    converted = create_error_from_exception(original)
    assert isinstance(converted, ValidationError)
    assert converted.original_exception is original
    print("✓ 异常转换正常工作")
    
    print("✅ 异常处理测试通过")

def test_configuration():
    """测试配置管理"""
    print("⚙️ 测试配置管理...")
    
    from configuration import (
        GenomeMCPConfig,
        ConfigManager,
        create_default_config,
        LogLevel
    )
    
    # 测试默认配置创建
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_config_file = f.name
    
    try:
        create_default_config(temp_config_file)
        # 读取创建的配置文件
        with open(temp_config_file, 'r') as f:
            config_dict = json.load(f)
        assert "server" in config_dict
        assert "logging" in config_dict
        print("✓ 默认配置创建成功")
    finally:
        if os.path.exists(temp_config_file):
            os.unlink(temp_config_file)
    
    # 测试配置模型
    config = GenomeMCPConfig(
        server={"host": "localhost", "port": 8080},
        logging={"level": LogLevel.INFO}
    )
    assert config.server.host == "localhost"
    assert config.logging.level == LogLevel.INFO
    print("✓ 配置模型验证成功")
    
    # 测试配置管理器
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_file = f.name
    
    try:
        manager = ConfigManager()
        manager.config_file = Path(temp_file)
        config = manager.load_config()
        assert config.server.host == "localhost"  # 默认值
        print("✓ 配置管理器工作正常")
    finally:
        os.unlink(temp_file)
    
    print("✅ 配置管理测试通过")

def test_data_processing():
    """测试数据处理功能"""
    print("📊 测试数据处理...")
    
    from data.parsers import GenomicDataParser
    from data.validators import GenomicValidator
    from type_defs.common import DataSource, ConfidenceLevel
    
    # 测试基因组位置解析
    position = GenomicDataParser.parse_genomic_position("1:1000-2000")
    assert position["chromosome"] == "1"
    assert position["start"] == 1000
    assert position["end"] == 2000
    print("✓ 基因组位置解析成功")
    
    # 测试验证功能
    validator = GenomicValidator()
    assert validator.validate_chromosome("chr1") == "1"
    try:
        validator.validate_chromosome("invalid")
        assert False, "Should have raised ValidationError"
    except exceptions.ValidationError:
        pass
    print("✓ 染色体验证成功")
    
    # 测试类型定义
    assert DataSource.NCBI == "ncbi"
    assert ConfidenceLevel.HIGH == "high"
    print("✓ 类型定义正常工作")
    
    print("✅ 数据处理测试通过")

async def test_http_functionality():
    """测试HTTP功能"""
    print("🌐 测试HTTP功能...")
    
    from http_utils import HTTPClient, RateLimiter, validate_url
    
    # 测试URL验证
    assert validate_url("https://api.ncbi.nlm.nih.gov") is True
    assert validate_url("invalid-url") is False
    print("✓ URL验证功能正常")
    
    # 测试限流器
    limiter = RateLimiter(requests_per_minute=10)
    assert limiter is not None
    print("✓ 限流器创建成功")
    
    # 测试HTTP客户端创建
    client = HTTPClient(
        base_url="https://api.example.com",
        timeout=30,
        max_retries=3
    )
    assert client.base_url == "https://api.example.com"
    assert client.timeout == 30
    print("✓ HTTP客户端创建成功")
    
    print("✅ HTTP功能测试通过")

def test_integration():
    """集成测试"""
    print("🔄 集成测试...")
    
    # 测试模块间协作
    from core import generate_cache_key
    from exceptions import ValidationError
    from data.validators import GenomicValidator
    
    # 使用缓存和验证协作
    validator = GenomicValidator()
    cache_key = generate_cache_key("validation", "chr1", "test")
    
    assert cache_key is not None
    assert isinstance(cache_key, str)
    print("✓ 模块间协作正常")
    
    # 测试异常在数据处理中的使用
    try:
        if not validator.validate_chromosome("invalid"):
            raise exceptions.ValidationError("无效的染色体名称", field_name="chromosome")
    except exceptions.ValidationError as e:
        assert e.field_name == "chromosome"
        print("✓ 异常处理集成正常")
    
    print("✅ 集成测试通过")

def main():
    """主测试函数"""
    print("🚀 开始 Genome MCP 使用效果测试")
    print("=" * 50)
    
    try:
        test_core_functionality()
        print()
        
        test_exception_handling()
        print()
        
        test_configuration()
        print()
        
        test_data_processing()
        print()
        
        asyncio.run(test_http_functionality())
        print()
        
        test_integration()
        print()
        
        print("🎉 所有测试通过！重构成功！")
        print("✨ 项目结构优化完成，功能正常")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()