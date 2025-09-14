"""
Tests for core utility functions.

This module contains tests for the core utility functions in the utils module.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from genome_mcp.core import (
    generate_cache_key,
    format_duration,
    format_file_size,
    get_timestamp,
    sanitize_filename,
    ensure_directory,
    merge_dictionaries,
    flatten_list,
    chunk_list,
    retry_async,
    validate_required_fields,
    normalize_dict,
    safe_get_nested,
    truncate_string,
    calculate_similarity,
    async_timeout,
    memory_usage,
    log_execution_time,
)
from genome_mcp.exceptions import ValidationError


class TestCacheKeyGeneration:
    """Test cache key generation functions."""

    def test_generate_cache_key_basic(self):
        """Test basic cache key generation."""
        key = generate_cache_key("test", "arg1", "arg2", key1="value1", key2="value2")

        assert key.startswith("test:")
        assert len(key) > len("test:")

        # Same arguments should produce same key
        key2 = generate_cache_key("test", "arg1", "arg2", key1="value1", key2="value2")
        assert key == key2

    def test_generate_cache_key_different_args(self):
        """Test cache key generation with different arguments."""
        key1 = generate_cache_key("test", "arg1")
        key2 = generate_cache_key("test", "arg2")

        assert key1 != key2

    def test_generate_cache_key_order_independence(self):
        """Test that key order doesn't affect cache key."""
        key1 = generate_cache_key("test", key1="value1", key2="value2")
        key2 = generate_cache_key("test", key2="value2", key1="value1")

        assert key1 == key2


class TestFormattingFunctions:
    """Test data formatting functions."""

    def test_format_duration_milliseconds(self):
        """Test duration formatting for milliseconds."""
        assert format_duration(0.001) == "1.0ms"
        assert format_duration(0.999) == "999.0ms"

    def test_format_duration_seconds(self):
        """Test duration formatting for seconds."""
        assert format_duration(1.5) == "1.5s"
        assert format_duration(59.9) == "59.9s"

    def test_format_duration_minutes(self):
        """Test duration formatting for minutes."""
        assert format_duration(60) == "1m 0.0s"
        assert format_duration(90) == "1m 30.0s"
        assert format_duration(3599) == "59m 59.0s"

    def test_format_duration_hours(self):
        """Test duration formatting for hours."""
        assert format_duration(3600) == "1h 0m 0.0s"
        assert format_duration(3661) == "1h 1m 1.0s"

    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        assert format_file_size(0) == "0B"
        assert format_file_size(1) == "1.0B"
        assert format_file_size(999) == "999.0B"

    def test_format_file_size_kilobytes(self):
        """Test file size formatting for kilobytes."""
        assert format_file_size(1024) == "1.0KB"
        assert format_file_size(1536) == "1.5KB"
        assert format_file_size(1024 * 999) == "999.0KB"

    def test_format_file_size_megabytes(self):
        """Test file size formatting for megabytes."""
        assert format_file_size(1024 * 1024) == "1.0MB"
        assert format_file_size(1024 * 1024 * 1.5) == "1.5MB"

    def test_format_file_size_gigabytes(self):
        """Test file size formatting for gigabytes."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0GB"
        assert format_file_size(1024 * 1024 * 1024 * 1.5) == "1.5GB"


class TestTimestampFunctions:
    """Test timestamp functions."""

    def test_get_timestamp(self):
        """Test timestamp generation."""
        timestamp = get_timestamp()

        # Should be a valid ISO format timestamp
        assert "T" in timestamp
        assert timestamp.endswith("Z") or "+" in timestamp or "-" in timestamp

        # Should be recent (within 1 second)
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        assert abs((now - dt).total_seconds()) < 1.0


class TestFilenameFunctions:
    """Test filename manipulation functions."""

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"
        assert sanitize_filename("file with spaces.txt") == "file with spaces.txt"

    def test_sanitize_filename_invalid_chars(self):
        """Test filename sanitization with invalid characters."""
        assert sanitize_filename("file<name>.txt") == "file_name_.txt"
        assert sanitize_filename("file>name>.txt") == "file_name_.txt"
        assert sanitize_filename("file:name:.txt") == "file_name_.txt"
        assert sanitize_filename('file"name".txt') == "file_name_.txt"
        assert sanitize_filename("file|name|.txt") == "file_name_.txt"
        assert sanitize_filename("file?name?.txt") == "file_name_.txt"
        assert sanitize_filename("file*name*.txt") == "file_name_.txt"

    def test_sanitize_filename_dots(self):
        """Test filename sanitization with dots."""
        assert sanitize_filename(".hidden") == "hidden"
        assert sanitize_filename("file.") == "file"
        assert sanitize_filename("..file..") == "file"

    def test_sanitize_filename_long(self):
        """Test filename sanitization for long filenames."""
        long_name = "a" * 300
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255

        # Test with extension
        long_with_ext = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_with_ext)
        assert len(sanitized) <= 255
        assert sanitized.endswith(".txt")


class TestDirectoryFunctions:
    """Test directory manipulation functions."""

    def test_ensure_directory_exists(self):
        """Test ensure_directory with existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ensure_directory(temp_dir)
            assert result == Path(temp_dir)
            assert result.exists()

    def test_ensure_directory_create(self):
        """Test ensure_directory creates new directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new" / "nested" / "directory"
            result = ensure_directory(new_dir)
            assert result == new_dir
            assert result.exists()
            assert result.is_dir()


class TestDictionaryFunctions:
    """Test dictionary manipulation functions."""

    def test_merge_dictionaries_basic(self):
        """Test basic dictionary merging."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}

        result = merge_dictionaries(dict1, dict2)
        expected = {"a": 1, "b": 2, "c": 3, "d": 4}
        assert result == expected

    def test_merge_dictionaries_overlap(self):
        """Test dictionary merging with overlapping keys."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}

        result = merge_dictionaries(dict1, dict2)
        expected = {"a": 1, "b": 3, "c": 4}
        assert result == expected

    def test_merge_dictionaries_nested(self):
        """Test nested dictionary merging."""
        dict1 = {"a": 1, "nested": {"x": 10, "y": 20}}
        dict2 = {"b": 2, "nested": {"y": 30, "z": 40}}

        result = merge_dictionaries(dict1, dict2)
        expected = {"a": 1, "b": 2, "nested": {"x": 10, "y": 30, "z": 40}}
        assert result == expected

    def test_flatten_list_basic(self):
        """Test basic list flattening."""
        nested = [[1, 2], [3, 4], [5, 6]]
        result = flatten_list(nested)
        assert result == [1, 2, 3, 4, 5, 6]

    def test_flatten_list_deeply_nested(self):
        """Test flattening deeply nested lists."""
        nested = [[1, [2, 3]], [[4, 5], 6], [7, [8, [9]]]]
        result = flatten_list(nested)
        assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_flatten_list_empty(self):
        """Test flattening empty lists."""
        assert flatten_list([]) == []
        assert flatten_list([[], []]) == []

    def test_chunk_list_basic(self):
        """Test basic list chunking."""
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = chunk_list(items, 3)
        expected = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
        assert result == expected

    def test_chunk_list_exact(self):
        """Test chunking when list divides evenly."""
        items = [1, 2, 3, 4, 5, 6]
        result = chunk_list(items, 3)
        expected = [[1, 2, 3], [4, 5, 6]]
        assert result == expected

    def test_chunk_list_single_item(self):
        """Test chunking with single item chunks."""
        items = [1, 2, 3]
        result = chunk_list(items, 1)
        expected = [[1], [2], [3]]
        assert result == expected

    def test_chunk_list_invalid_size(self):
        """Test chunking with invalid chunk size."""
        with pytest.raises(ValidationError):
            chunk_list([1, 2, 3], 0)

        with pytest.raises(ValidationError):
            chunk_list([1, 2, 3], -1)


class TestValidationFunctions:
    """Test validation functions."""

    def test_validate_required_fields_success(self):
        """Test required fields validation success."""
        data = {"name": "test", "value": 123}
        required = ["name", "value"]

        # Should not raise exception
        validate_required_fields(data, required)

    def test_validate_required_fields_missing(self):
        """Test required fields validation with missing fields."""
        data = {"name": "test"}
        required = ["name", "missing"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, required)

        assert "Missing required fields" in str(exc_info.value)
        assert "missing" in str(exc_info.value)

    def test_validate_required_fields_none_values(self):
        """Test required fields validation with None values."""
        data = {"name": "test", "value": None}
        required = ["name", "value"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, required)

        assert "Missing required fields" in str(exc_info.value)
        assert "value" in str(exc_info.value)

    def test_normalize_dict_basic(self):
        """Test dictionary normalization."""
        data = {"Name": "Test", "VALUE": 123, "None_Key": None, "  Spaces  ": "value"}
        result = normalize_dict(data)

        expected = {"name": "Test", "value": 123, "spaces": "value"}
        assert result == expected

    def test_normalize_dict_empty(self):
        """Test normalization of empty dictionary."""
        assert normalize_dict({}) == {}

    def test_safe_get_nested_basic(self):
        """Test safe nested value access."""
        data = {"a": {"b": {"c": "value"}}}

        assert safe_get_nested(data, "a.b.c") == "value"
        assert safe_get_nested(data, "a.b.c.d", "default") == "default"
        assert safe_get_nested(data, "x.y.z", "default") == "default"

    def test_safe_get_nested_invalid_path(self):
        """Test safe nested value access with invalid path."""
        data = {"a": {"b": 123}}

        assert safe_get_nested(data, "a.b.c", "default") == "default"
        assert safe_get_nested(data, "a.x", "default") == "default"


class TestStringFunctions:
    """Test string manipulation functions."""

    def test_truncate_string_short(self):
        """Test truncation of short strings."""
        text = "short text"
        assert truncate_string(text, 20) == text

    def test_truncate_string_long(self):
        """Test truncation of long strings."""
        text = "this is a very long text that needs to be truncated"
        result = truncate_string(text, 20)

        assert len(result) <= 20
        assert result.endswith("...")

    def test_truncate_string_custom_suffix(self):
        """Test truncation with custom suffix."""
        text = "this is a very long text that needs to be truncated"
        result = truncate_string(text, 20, suffix=" [more]")

        assert len(result) <= 20
        assert result.endswith(" [more]")

    def test_calculate_similarity_identical(self):
        """Test similarity calculation for identical strings."""
        assert calculate_similarity("test", "test") == 1.0
        assert calculate_similarity("", "") == 1.0

    def test_calculate_similarity_different(self):
        """Test similarity calculation for different strings."""
        similarity = calculate_similarity("test", "completely different")
        assert 0.0 <= similarity <= 1.0

    def test_calculate_similarity_empty(self):
        """Test similarity calculation with empty strings."""
        assert calculate_similarity("", "test") == 0.0
        assert calculate_similarity("test", "") == 0.0


class TestAsyncFunctions:
    """Test async utility functions."""

    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """Test retry decorator with successful function."""
        call_count = 0

        @retry_async(max_retries=3, retry_delay=0.1)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_async_with_retries(self):
        """Test retry decorator with retries."""
        call_count = 0

        @retry_async(max_retries=3, retry_delay=0.1, exceptions=(ValueError,))
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("try again")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_async_max_retries_exceeded(self):
        """Test retry decorator when max retries exceeded."""
        call_count = 0

        @retry_async(max_retries=2, retry_delay=0.1, exceptions=(ValueError,))
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fails")

        with pytest.raises(ValueError):
            await test_func()

        assert call_count == 3  # 1 initial + 2 retries

    @pytest.mark.asyncio
    async def test_async_timeout_success(self):
        """Test timeout decorator with successful function."""

        @async_timeout(1.0)
        async def test_func():
            await asyncio.sleep(0.1)
            return "success"

        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_timeout_timeout(self):
        """Test timeout decorator with timeout."""

        @async_timeout(0.1)
        async def test_func():
            await asyncio.sleep(0.5)
            return "success"

        from genome_mcp.exceptions import TimeoutError

        with pytest.raises(TimeoutError):
            await test_func()


class TestUtilityFunctions:
    """Test miscellaneous utility functions."""

    def test_memory_usage(self):
        """Test memory usage function."""
        memory = memory_usage()

        assert isinstance(memory, dict)
        assert "rss" in memory
        assert "vms" in memory
        assert "percent" in memory

        # Values should be non-negative
        assert memory["rss"] >= 0
        assert memory["vms"] >= 0
        assert memory["percent"] >= 0

    def test_log_execution_time_async(self):
        """Test execution time logging for async functions."""
        call_log = []

        @log_execution_time("test_func")
        async def test_func():
            await asyncio.sleep(0.1)
            return "result"

        # Test would require logger mocking
        result = asyncio.run(test_func())
        assert result == "result"

    def test_log_execution_time_sync(self):
        """Test execution time logging for sync functions."""

        @log_execution_time("test_func")
        def test_func():
            return "result"

        result = test_func()
        assert result == "result"


if __name__ == "__main__":
    pytest.main([__file__])
