"""
Core functionality module for Genome MCP.

This module contains core utility functions for caching, formatting, and async operations.
"""

from .async_utils import async_timeout, log_execution_time, retry_async
from .caching import (
    calculate_similarity,
    chunk_list,
    ensure_directory,
    flatten_list,
    generate_cache_key,
    memory_usage,
    merge_dictionaries,
    normalize_dict,
    safe_get_nested,
    validate_required_fields,
)
from .formatting import (
    format_duration,
    format_file_size,
    get_timestamp,
    sanitize_filename,
    truncate_string,
)

__all__ = [
    # Caching utilities
    "generate_cache_key",
    "ensure_directory",
    "merge_dictionaries",
    "flatten_list",
    "chunk_list",
    "validate_required_fields",
    "normalize_dict",
    "safe_get_nested",
    "calculate_similarity",
    "memory_usage",
    # Formatting utilities
    "format_duration",
    "format_file_size",
    "get_timestamp",
    "sanitize_filename",
    "truncate_string",
    # Async utilities
    "retry_async",
    "async_timeout",
    "log_execution_time",
]
