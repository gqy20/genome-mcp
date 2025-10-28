#!/usr/bin/env python3
"""
标准化错误处理模块 - 简化但有效的错误格式

提供统一的错误处理，但不过度复杂化
"""

from typing import Any


class GenomeMCPError(Exception):
    """基因组MCP基础错误类"""

    def __init__(
        self,
        message: str,
        error_code: str,
        suggestions: list[str] | None = None,
        query_info: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.suggestions = suggestions or []
        self.query_info = query_info or {}

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {
            "error": self.message,
            "error_code": self.error_code,
            "suggestions": self.suggestions,
        }

        if self.query_info:
            result["query_info"] = self.query_info

        return result


class ValidationError(GenomeMCPError):
    """参数验证错误"""

    def __init__(self, message: str, param_name: str | None = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            suggestions=[
                "Check parameter format",
                "Ensure all required parameters are provided",
                "Refer to documentation for valid parameter ranges",
            ],
            query_info={"invalid_param": param_name} if param_name else None,
        )


class APIError(GenomeMCPError):
    """外部API调用错误"""

    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: int | None = None,
        suggestions: list[str] | None = None,
    ):
        default_suggestions = [
            "Check network connection",
            "Try again later",
            "Verify API service status",
        ]

        if suggestions:
            default_suggestions.extend(suggestions)

        super().__init__(
            message=message,
            error_code="API_ERROR",
            suggestions=default_suggestions,
            query_info={"api_name": api_name, "status_code": status_code},
        )


class DataNotFoundError(GenomeMCPError):
    """数据未找到错误"""

    def __init__(self, query: str, data_type: str = "gene"):
        super().__init__(
            message=f"No {data_type} found for query: {query}",
            error_code="DATA_NOT_FOUND",
            suggestions=[
                "Check spelling of gene/protein names",
                "Try using different identifiers",
                "Verify the species is correct",
                "Use broader search terms",
            ],
            query_info={"query": query, "data_type": data_type},
        )


class RateLimitError(GenomeMCPError):
    """API频率限制错误"""

    def __init__(self, api_name: str, retry_after: int | None = None):
        message = f"Rate limit exceeded for {api_name} API"
        if retry_after:
            message += f". Please wait {retry_after} seconds before retrying."

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            suggestions=[
                "Reduce query frequency",
                "Use batch queries when possible",
                f"Wait {retry_after or 'a few'} seconds before retrying",
            ],
            query_info={"api_name": api_name, "retry_after": retry_after},
        )


class InternalError(GenomeMCPError):
    """内部系统错误"""

    def __init__(self, message: str, component: str | None = None):
        super().__init__(
            message=f"Internal error: {message}",
            error_code="INTERNAL_ERROR",
            suggestions=[
                "Try the query again",
                "Contact support if the problem persists",
                "Check system status",
            ],
            query_info={"component": component} if component else None,
        )


def format_simple_error(
    error: Exception, query: str | None = None, operation: str | None = None
) -> dict[str, Any]:
    """
    格式化简单错误响应

    Args:
        error: 异常对象
        query: 相关查询
        operation: 操作类型

    Returns:
        标准化的错误响应
    """
    if isinstance(error, GenomeMCPError):
        result = error.to_dict()
    else:
        result = {
            "error": str(error),
            "error_code": "UNKNOWN_ERROR",
            "suggestions": [
                "Try the query again",
                "Check input parameters",
                "Contact support if the problem persists",
            ],
        }

    # 添加通用查询信息
    if query:
        result["query"] = query
    if operation:
        result["operation"] = operation

    return result


def create_validation_error_message(
    param_name: str, value: Any, expected_type: str
) -> str:
    """
    创建参数验证错误消息

    Args:
        param_name: 参数名
        value: 参数值
        expected_type: 期望类型

    Returns:
        格式化的错误消息
    """
    return f"Invalid {param_name}: '{value}'. Expected {expected_type}"


def create_api_error_message(
    api_name: str, status: str, details: str | None = None
) -> str:
    """
    创建API错误消息

    Args:
        api_name: API名称
        status: 状态描述
        details: 详细信息

    Returns:
        格式化的错误消息
    """
    message = f"{api_name} API {status}"
    if details:
        message += f": {details}"
    return message


# 常用错误代码常量
class ErrorCodes:
    """错误代码常量"""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    API_ERROR = "API_ERROR"
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    PARSING_ERROR = "PARSING_ERROR"


# 错误处理装饰器
def handle_errors(operation_name: str):
    """
    错误处理装饰器

    Args:
        operation_name: 操作名称，用于错误报告
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except GenomeMCPError:
                # 已经是标准化的错误，直接重新抛出
                raise
            except ConnectionError as e:
                raise APIError(
                    create_api_error_message("Network", "connection failed", str(e)),
                    "Network",
                ) from e
            except TimeoutError as e:
                raise APIError(
                    create_api_error_message("Network", "timeout", str(e)), "Network"
                ) from e
            except ValueError as e:
                raise ValidationError(f"Invalid parameter: {str(e)}") from e
            except Exception as e:
                raise InternalError(
                    f"Unexpected error in {operation_name}: {str(e)}", operation_name
                ) from e

        return wrapper

    return decorator
