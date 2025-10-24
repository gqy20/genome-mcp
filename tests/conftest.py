"""
pytest配置文件
"""

import asyncio
import os
import sys

import pytest

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_gene_data():
    """示例基因数据"""
    return {
        "TP53": {
            "gene_id": "TP53",
            "uid": "7157",
            "data": {
                "name": "tumor protein p53",
                "description": "This gene encodes tumor protein p53",
                "chromosome": "17p13.1",
                "summary": "TP53 is a tumor suppressor gene",
            },
        }
    }


@pytest.fixture
def sample_batch_result():
    """示例批量查询结果"""
    return {
        "batch_size": 2,
        "results": {
            "TP53": {"gene_id": "TP53", "data": {"name": "TP53"}},
            "BRCA1": {"gene_id": "BRCA1", "data": {"name": "BRCA1"}},
        },
    }
