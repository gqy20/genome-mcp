"""
Core utilities for Genome MCP.

This module provides core utility functions for caching, formatting,
and common operations.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from pathlib import Path

from genome_mcp.exceptions import ValidationError


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate consistent cache key from arguments.

    Args:
        prefix: Key prefix for categorization
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key

    Returns:
        Cache key string
    """
    # Create a dictionary with all arguments
    key_data = {"args": args, "kwargs": kwargs}

    # Convert to JSON string for consistent hashing
    key_json = json.dumps(key_data, sort_keys=True, default=str)

    # Generate hash
    key_hash = hashlib.md5(key_json.encode()).hexdigest()

    return f"{prefix}:{key_hash}"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted file size string
    """
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f}{size_names[i]}"


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        ISO format timestamp string
    """
    return datetime.now(timezone.utc).isoformat()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Invalid characters for most filesystems
    invalid_chars = '<>:"/\\|?*'

    # Replace invalid characters with underscores
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing whitespace and dots
    filename = filename.strip(". ")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        name = name[: 255 - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name

    return filename or "unnamed"


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if necessary.

    Args:
        path: Directory path

    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def merge_dictionaries(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries recursively.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (overrides dict1)

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dictionaries(result[key], value)
        else:
            result[key] = value

    return result


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """
    Flatten a nested list.

    Args:
        nested_list: Nested list to flatten

    Returns:
        Flattened list
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        raise ValidationError("Chunk size must be positive")

    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields are present in data dictionary.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = []

    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            field_name="required_fields",
            field_value={"missing": missing_fields, "provided": list(data.keys())},
        )


def normalize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize dictionary by converting keys to lowercase and removing None values.

    Args:
        data: Dictionary to normalize

    Returns:
        Normalized dictionary
    """
    normalized = {}

    for key, value in data.items():
        if value is not None:
            normalized_key = key.lower().strip()
            normalized[normalized_key] = value

    return normalized


def safe_get_nested(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Safely get nested value from dictionary using dot notation.

    Args:
        data: Dictionary to get value from
        key_path: Dot-separated key path (e.g., "result.data.value")
        default: Default value if key not found

    Returns:
        Value at key path or default
    """
    keys = key_path.split(".")
    current = data

    try:
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    except (KeyError, TypeError, AttributeError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    truncated = text[: max_length - len(suffix)]
    return truncated + suffix


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two strings (simple implementation).

    Args:
        text1: First string
        text2: Second string

    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0

    # Simple Levenshtein distance implementation
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    distance = levenshtein_distance(text1.lower(), text2.lower())
    max_length = max(len(text1), len(text2))

    return 1.0 - (distance / max_length) if max_length > 0 else 1.0


def memory_usage() -> Dict[str, float]:
    """
    Get current memory usage statistics.

    Returns:
        Dictionary with memory usage information
    """
    try:
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "rss": memory_info.rss / 1024 / 1024,  # MB
            "vms": memory_info.vms / 1024 / 1024,  # MB
            "percent": process.memory_percent(),
        }
    except ImportError:
        return {"rss": 0.0, "vms": 0.0, "percent": 0.0}
