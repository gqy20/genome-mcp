"""
Core functionality module for Genome MCP.

This module contains core utility functions for caching, formatting, and async operations.
"""

from .caching import (
    generate_cache_key,
    ensure_directory,
    merge_dictionaries,
    flatten_list,
    chunk_list,
    validate_required_fields,
    normalize_dict,
    safe_get_nested,
    calculate_similarity,
    memory_usage,
)

from .formatting import (
    format_duration,
    format_file_size,
    get_timestamp,
    sanitize_filename,
    truncate_string,
)

from .async_utils import (
    retry_async,
    async_timeout,
    log_execution_time,
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