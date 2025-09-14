"""
Tests for core exception definitions.

This module contains tests for all custom exceptions defined in the exceptions module.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from genome_mcp.exceptions import (
    GenomeMCPError,
    ConfigurationError,
    ValidationError,
    DataNotFoundError,
    DataFormatError,
    APIError,
    RateLimitError,
    AuthenticationError,
    NetworkError,
    CacheError,
    TimeoutError,
    ResourceError,
    BatchProcessingError,
    QuerySyntaxError,
    ServerError,
    DatabaseError,
    create_error_from_exception
)


class TestGenomeMCPError:
    """Test base GenomeMCPError class."""
    
    def test_basic_initialization(self):
        """Test basic error initialization."""
        error = GenomeMCPError("Test error message")
        
        assert error.message == "Test error message"
        assert str(error) == "Test error message"
        assert error.error_code is None
        assert error.details == {}
        assert error.original_exception is None
        assert isinstance(error.timestamp, datetime)
    
    def test_initialization_with_all_params(self):
        """Test error initialization with all parameters."""
        original_exc = ValueError("Original error")
        error = GenomeMCPError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            original_exception=original_exc
        )
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        assert error.original_exception is original_exc
        assert isinstance(error.timestamp, datetime)
    
    def test_to_dict(self):
        """Test converting exception to dictionary."""
        error = GenomeMCPError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict['error_type'] == 'GenomeMCPError'
        assert error_dict['message'] == 'Test error'
        assert error_dict['error_code'] == 'TEST_ERROR'
        assert error_dict['details'] == {"key": "value"}
        assert 'timestamp' in error_dict


class TestConfigurationError:
    """Test ConfigurationError class."""
    
    def test_basic_initialization(self):
        """Test basic configuration error initialization."""
        error = ConfigurationError("Invalid configuration")
        
        assert error.message == "Invalid configuration"
        assert error.error_code == "CONFIG_ERROR"
        assert error.config_key is None
    
    def test_initialization_with_config_key(self):
        """Test configuration error with config key."""
        error = ConfigurationError("Invalid timeout", config_key="cache.timeout")
        
        assert error.config_key == "cache.timeout"
        assert error.details['config_key'] == "cache.timeout"


class TestValidationError:
    """Test ValidationError class."""
    
    def test_basic_initialization(self):
        """Test basic validation error initialization."""
        error = ValidationError("Invalid data")
        
        assert error.message == "Invalid data"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.field_name is None
        assert error.field_value is None
    
    def test_initialization_with_field_details(self):
        """Test validation error with field details."""
        error = ValidationError(
            message="Invalid gene symbol",
            field_name="gene_symbol",
            field_value="invalid_gene_123"
        )
        
        assert error.field_name == "gene_symbol"
        assert error.field_value == "invalid_gene_123"
        assert error.details['field_name'] == "gene_symbol"
        assert error.details['field_value'] == "invalid_gene_123"


class TestDataNotFoundError:
    """Test DataNotFoundError class."""
    
    def test_basic_initialization(self):
        """Test basic data not found error initialization."""
        error = DataNotFoundError("Gene not found")
        
        assert error.message == "Gene not found"
        assert error.error_code == "DATA_NOT_FOUND"
        assert error.data_source is None
        assert error.query_params == {}
    
    def test_initialization_with_query_details(self):
        """Test data not found error with query details."""
        query_params = {"gene_symbol": "NONEXISTENT", "species": "homo_sapiens"}
        error = DataNotFoundError(
            message="Gene not found in database",
            data_source="NCBI",
            query_params=query_params
        )
        
        assert error.data_source == "NCBI"
        assert error.query_params == query_params
        assert error.details['data_source'] == "NCBI"
        assert error.details['query_params'] == query_params


class TestDataFormatError:
    """Test DataFormatError class."""
    
    def test_basic_initialization(self):
        """Test basic data format error initialization."""
        error = DataFormatError("Invalid data format")
        
        assert error.message == "Invalid data format"
        assert error.error_code == "DATA_FORMAT_ERROR"
        assert error.expected_format is None
        assert error.actual_format is None
    
    def test_initialization_with_format_details(self):
        """Test data format error with format details."""
        error = DataFormatError(
            message="Unexpected response format",
            expected_format="JSON",
            actual_format="XML"
        )
        
        assert error.expected_format == "JSON"
        assert error.actual_format == "XML"
        assert error.details['expected_format'] == "JSON"
        assert error.details['actual_format'] == "XML"


class TestAPIError:
    """Test APIError class."""
    
    def test_basic_initialization(self):
        """Test basic API error initialization."""
        error = APIError("API request failed")
        
        assert error.message == "API request failed"
        assert error.error_code == "API_ERROR"
        assert error.status_code is None
        assert error.url is None
        assert error.response_data == {}
    
    def test_initialization_with_api_details(self):
        """Test API error with API details."""
        response_data = {"error": "Not found", "code": 404}
        error = APIError(
            message="Resource not found",
            status_code=404,
            url="https://api.example.com/genes/TP53",
            response_data=response_data
        )
        
        assert error.status_code == 404
        assert error.url == "https://api.example.com/genes/TP53"
        assert error.response_data == response_data
        assert error.details['status_code'] == 404
        assert error.details['url'] == "https://api.example.com/genes/TP53"
        assert error.details['response_data'] == response_data


class TestRateLimitError:
    """Test RateLimitError class."""
    
    def test_inheritance(self):
        """Test that RateLimitError inherits from APIError."""
        error = RateLimitError("Rate limit exceeded")
        
        assert isinstance(error, APIError)
        assert error.error_code == "RATE_LIMIT_ERROR"
    
    def test_initialization_with_rate_details(self):
        """Test rate limit error with rate details."""
        error = RateLimitError(
            message="Too many requests",
            retry_after=60,
            rate_limit_type="per_minute"
        )
        
        assert error.retry_after == 60
        assert error.rate_limit_type == "per_minute"
        assert error.details['retry_after'] == 60
        assert error.details['rate_limit_type'] == "per_minute"


class TestAuthenticationError:
    """Test AuthenticationError class."""
    
    def test_inheritance(self):
        """Test that AuthenticationError inherits from APIError."""
        error = AuthenticationError("Authentication failed")
        
        assert isinstance(error, APIError)
        assert error.error_code == "AUTHENTICATION_ERROR"
    
    def test_initialization_with_auth_details(self):
        """Test authentication error with auth details."""
        error = AuthenticationError(
            message="Invalid API key",
            auth_type="api_key"
        )
        
        assert error.auth_type == "api_key"
        assert error.details['auth_type'] == "api_key"


class TestNetworkError:
    """Test NetworkError class."""
    
    def test_basic_initialization(self):
        """Test basic network error initialization."""
        error = NetworkError("Connection failed")
        
        assert error.message == "Connection failed"
        assert error.error_code == "NETWORK_ERROR"
        assert error.host is None
        assert error.port is None
    
    def test_initialization_with_network_details(self):
        """Test network error with network details."""
        error = NetworkError(
            message="Connection timeout",
            host="api.ncbi.nlm.nih.gov",
            port=443
        )
        
        assert error.host == "api.ncbi.nlm.nih.gov"
        assert error.port == 443
        assert error.details['host'] == "api.ncbi.nlm.nih.gov"
        assert error.details['port'] == 443


class TestCacheError:
    """Test CacheError class."""
    
    def test_basic_initialization(self):
        """Test basic cache error initialization."""
        error = CacheError("Cache operation failed")
        
        assert error.message == "Cache operation failed"
        assert error.error_code == "CACHE_ERROR"
        assert error.cache_key is None
        assert error.operation is None
    
    def test_initialization_with_cache_details(self):
        """Test cache error with cache details."""
        error = CacheError(
            message="Cache key not found",
            cache_key="gene:TP53:homo_sapiens",
            operation="get"
        )
        
        assert error.cache_key == "gene:TP53:homo_sapiens"
        assert error.operation == "get"
        assert error.details['cache_key'] == "gene:TP53:homo_sapiens"
        assert error.details['operation'] == "get"


class TestTimeoutError:
    """Test TimeoutError class."""
    
    def test_basic_initialization(self):
        """Test basic timeout error initialization."""
        error = TimeoutError("Operation timed out")
        
        assert error.message == "Operation timed out"
        assert error.error_code == "TIMEOUT_ERROR"
        assert error.timeout_duration is None
        assert error.operation is None
    
    def test_initialization_with_timeout_details(self):
        """Test timeout error with timeout details."""
        error = TimeoutError(
            message="API request timed out",
            timeout_duration=30.5,
            operation="gene_query"
        )
        
        assert error.timeout_duration == 30.5
        assert error.operation == "gene_query"
        assert error.details['timeout_duration'] == 30.5
        assert error.details['operation'] == "gene_query"


class TestResourceError:
    """Test ResourceError class."""
    
    def test_basic_initialization(self):
        """Test basic resource error initialization."""
        error = ResourceError("Resource unavailable")
        
        assert error.message == "Resource unavailable"
        assert error.error_code == "RESOURCE_ERROR"
        assert error.resource_type is None
        assert error.resource_id is None
    
    def test_initialization_with_resource_details(self):
        """Test resource error with resource details."""
        error = ResourceError(
            message="File not found",
            resource_type="file",
            resource_id="/path/to/file.txt"
        )
        
        assert error.resource_type == "file"
        assert error.resource_id == "/path/to/file.txt"
        assert error.details['resource_type'] == "file"
        assert error.details['resource_id'] == "/path/to/file.txt"


class TestBatchProcessingError:
    """Test BatchProcessingError class."""
    
    def test_basic_initialization(self):
        """Test basic batch processing error initialization."""
        error = BatchProcessingError("Batch processing failed")
        
        assert error.message == "Batch processing failed"
        assert error.error_code == "BATCH_PROCESSING_ERROR"
        assert error.batch_size is None
        assert error.failed_items == []
        assert error.successful_items == 0
    
    def test_initialization_with_batch_details(self):
        """Test batch processing error with batch details."""
        failed_items = [
            {"item": "TP53", "error": "Data not found"},
            {"item": "BRCA1", "error": "Invalid format"}
        ]
        error = BatchProcessingError(
            message="Some items failed to process",
            batch_size=100,
            failed_items=failed_items,
            successful_items=98
        )
        
        assert error.batch_size == 100
        assert error.failed_items == failed_items
        assert error.successful_items == 98
        assert error.details['batch_size'] == 100
        assert error.details['failed_items'] == failed_items
        assert error.details['successful_items'] == 98


class TestQuerySyntaxError:
    """Test QuerySyntaxError class."""
    
    def test_basic_initialization(self):
        """Test basic query syntax error initialization."""
        error = QuerySyntaxError("Invalid query syntax")
        
        assert error.message == "Invalid query syntax"
        assert error.error_code == "QUERY_SYNTAX_ERROR"
        assert error.query is None
        assert error.syntax_position is None
    
    def test_initialization_with_query_details(self):
        """Test query syntax error with query details."""
        error = QuerySyntaxError(
            message="Unexpected token at position 10",
            query="gene:TP53 AND species:invalid",
            syntax_position=25
        )
        
        assert error.query == "gene:TP53 AND species:invalid"
        assert error.syntax_position == 25
        assert error.details['query'] == "gene:TP53 AND species:invalid"
        assert error.details['syntax_position'] == 25


class TestServerError:
    """Test ServerError class."""
    
    def test_basic_initialization(self):
        """Test basic server error initialization."""
        error = ServerError("Server operation failed")
        
        assert error.message == "Server operation failed"
        assert error.error_code == "SERVER_ERROR"
        assert error.server_name is None
        assert error.operation is None
    
    def test_initialization_with_server_details(self):
        """Test server error with server details."""
        error = ServerError(
            message="NCBI server unavailable",
            server_name="NCBI",
            operation="gene_query"
        )
        
        assert error.server_name == "NCBI"
        assert error.operation == "gene_query"
        assert error.details['server_name'] == "NCBI"
        assert error.details['operation'] == "gene_query"


class TestDatabaseError:
    """Test DatabaseError class."""
    
    def test_basic_initialization(self):
        """Test basic database error initialization."""
        error = DatabaseError("Database operation failed")
        
        assert error.message == "Database operation failed"
        assert error.error_code == "DATABASE_ERROR"
        assert error.database_name is None
        assert error.table_name is None
    
    def test_initialization_with_database_details(self):
        """Test database error with database details."""
        error = DatabaseError(
            message="Table not found",
            database_name="genome_db",
            table_name="genes"
        )
        
        assert error.database_name == "genome_db"
        assert error.table_name == "genes"
        assert error.details['database_name'] == "genome_db"
        assert error.details['table_name'] == "genes"


class TestErrorCreationFromException:
    """Test create_error_from_exception function."""
    
    def test_from_value_error(self):
        """Test creating error from ValueError."""
        original_exc = ValueError("Invalid value")
        error = create_error_from_exception(original_exc)
        
        assert isinstance(error, ValidationError)
        assert error.message == "Invalid value"
        assert error.original_exception is original_exc
    
    def test_from_file_not_found_error(self):
        """Test creating error from FileNotFoundError."""
        original_exc = FileNotFoundError("File not found")
        error = create_error_from_exception(original_exc)
        
        assert isinstance(error, ResourceError)
        assert error.message == "File not found"
        assert error.resource_type == "file"
        assert error.original_exception is original_exc
    
    def test_from_permission_error(self):
        """Test creating error from PermissionError."""
        original_exc = PermissionError("Permission denied")
        error = create_error_from_exception(original_exc)
        
        assert isinstance(error, ResourceError)
        assert error.message == "Permission denied"
        assert error.resource_type == "permission"
        assert error.original_exception is original_exc
    
    def test_from_connection_error(self):
        """Test creating error from ConnectionError."""
        original_exc = ConnectionError("Connection failed")
        error = create_error_from_exception(original_exc)
        
        assert isinstance(error, NetworkError)
        assert error.message == "Connection failed"
        assert error.original_exception is original_exc
    
    def test_from_timeout_error(self):
        """Test creating error from TimeoutError."""
        original_exc = TimeoutError("Operation timed out")
        error = create_error_from_exception(original_exc)
        
        assert isinstance(error, TimeoutError)
        assert error.message == "Operation timed out"
        assert error.original_exception is original_exc
    
    def test_from_memory_error(self):
        """Test creating error from MemoryError."""
        original_exc = MemoryError("Out of memory")
        error = create_error_from_exception(original_exc)
        
        assert isinstance(error, ResourceError)
        assert error.message == "Out of memory"
        assert error.resource_type == "memory"
        assert error.original_exception is original_exc
    
    def test_from_generic_exception(self):
        """Test creating error from generic exception."""
        original_exc = Exception("Generic error")
        error = create_error_from_exception(original_exc, error_code="CUSTOM_ERROR")
        
        assert isinstance(error, GenomeMCPError)
        assert error.message == "Generic error"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.original_exception is original_exc
    
    def test_from_generic_exception_without_error_code(self):
        """Test creating error from generic exception without error code."""
        original_exc = Exception("Generic error")
        error = create_error_from_exception(original_exc)
        
        assert isinstance(error, GenomeMCPError)
        assert error.message == "Generic error"
        assert error.error_code is None
        assert error.original_exception is original_exc


if __name__ == "__main__":
    pytest.main([__file__])