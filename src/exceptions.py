"""
Core exception definitions for Genome MCP.

This module defines all custom exceptions used throughout the Genome MCP system,
providing consistent error handling and meaningful error messages.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime


class GenomeMCPError(Exception):
    """Base exception class for all Genome MCP errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize Genome MCP error.
        
        Args:
            message: Error message
            error_code: Optional error code for programmatic handling
            details: Additional error details as dictionary
            original_exception: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class ConfigurationError(GenomeMCPError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_key = config_key
        if config_key:
            self.details['config_key'] = config_key


class ValidationError(GenomeMCPError):
    """Exception raised for data validation errors."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, field_value: Any = None, **kwargs):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field_name = field_name
        self.field_value = field_value
        
        if field_name:
            self.details['field_name'] = field_name
        if field_value is not None:
            self.details['field_value'] = str(field_value)


class DataNotFoundError(GenomeMCPError):
    """Exception raised when requested data is not found."""
    
    def __init__(self, message: str, data_source: Optional[str] = None, query_params: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize data not found error.
        
        Args:
            message: Error message
            data_source: Data source that was queried
            query_params: Query parameters used
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="DATA_NOT_FOUND", **kwargs)
        self.data_source = data_source
        self.query_params = query_params or {}
        
        if data_source:
            self.details['data_source'] = data_source
        if query_params:
            self.details['query_params'] = query_params


class DataFormatError(GenomeMCPError):
    """Exception raised for data format-related errors."""
    
    def __init__(self, message: str, expected_format: Optional[str] = None, actual_format: Optional[str] = None, **kwargs):
        """
        Initialize data format error.
        
        Args:
            message: Error message
            expected_format: Expected data format
            actual_format: Actual data format received
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="DATA_FORMAT_ERROR", **kwargs)
        self.expected_format = expected_format
        self.actual_format = actual_format
        
        if expected_format:
            self.details['expected_format'] = expected_format
        if actual_format:
            self.details['actual_format'] = actual_format


class APIError(GenomeMCPError):
    """Exception raised for API-related errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            url: API endpoint URL
            response_data: Response data from API
            error_code: Error code (defaults to API_ERROR)
            **kwargs: Additional arguments passed to parent class
        """
        if error_code is None:
            error_code = "API_ERROR"
        
        super().__init__(message, error_code=error_code, **kwargs)
        self.status_code = status_code
        self.url = url
        self.response_data = response_data or {}
        
        if status_code:
            self.details['status_code'] = status_code
        if url:
            self.details['url'] = url
        if response_data:
            self.details['response_data'] = response_data


class RateLimitError(APIError):
    """Exception raised when API rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        rate_limit_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            rate_limit_type: Type of rate limit (e.g., 'per_minute', 'per_hour')
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="RATE_LIMIT_ERROR", **kwargs)
        self.retry_after = retry_after
        self.rate_limit_type = rate_limit_type
        
        if retry_after:
            self.details['retry_after'] = retry_after
        if rate_limit_type:
            self.details['rate_limit_type'] = rate_limit_type


class AuthenticationError(APIError):
    """Exception raised for authentication/authorization errors."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None, **kwargs):
        """
        Initialize authentication error.
        
        Args:
            message: Error message
            auth_type: Type of authentication that failed
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)
        self.auth_type = auth_type
        
        if auth_type:
            self.details['auth_type'] = auth_type


class NetworkError(GenomeMCPError):
    """Exception raised for network-related errors."""
    
    def __init__(self, message: str, host: Optional[str] = None, port: Optional[int] = None, **kwargs):
        """
        Initialize network error.
        
        Args:
            message: Error message
            host: Host that failed to connect
            port: Port that failed to connect
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)
        self.host = host
        self.port = port
        
        if host:
            self.details['host'] = host
        if port:
            self.details['port'] = port


class CacheError(GenomeMCPError):
    """Exception raised for cache-related errors."""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, operation: Optional[str] = None, **kwargs):
        """
        Initialize cache error.
        
        Args:
            message: Error message
            cache_key: Cache key involved in the error
            operation: Cache operation that failed
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="CACHE_ERROR", **kwargs)
        self.cache_key = cache_key
        self.operation = operation
        
        if cache_key:
            self.details['cache_key'] = cache_key
        if operation:
            self.details['operation'] = operation


class TimeoutError(GenomeMCPError):
    """Exception raised for timeout-related errors."""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, operation: Optional[str] = None, **kwargs):
        """
        Initialize timeout error.
        
        Args:
            message: Error message
            timeout_duration: Timeout duration in seconds
            operation: Operation that timed out
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)
        self.timeout_duration = timeout_duration
        self.operation = operation
        
        if timeout_duration:
            self.details['timeout_duration'] = timeout_duration
        if operation:
            self.details['operation'] = operation


class ResourceError(GenomeMCPError):
    """Exception raised for resource-related errors."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, **kwargs):
        """
        Initialize resource error.
        
        Args:
            message: Error message
            resource_type: Type of resource
            resource_id: Identifier of the resource
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="RESOURCE_ERROR", **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        if resource_type:
            self.details['resource_type'] = resource_type
        if resource_id:
            self.details['resource_id'] = resource_id


class BatchProcessingError(GenomeMCPError):
    """Exception raised for batch processing errors."""
    
    def __init__(
        self,
        message: str,
        batch_size: Optional[int] = None,
        failed_items: Optional[List[Dict[str, Any]]] = None,
        successful_items: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize batch processing error.
        
        Args:
            message: Error message
            batch_size: Total batch size
            failed_items: List of failed items with their errors
            successful_items: Number of successfully processed items
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="BATCH_PROCESSING_ERROR", **kwargs)
        self.batch_size = batch_size
        self.failed_items = failed_items or []
        self.successful_items = successful_items or 0
        
        if batch_size:
            self.details['batch_size'] = batch_size
        if failed_items:
            self.details['failed_items'] = failed_items
        if successful_items:
            self.details['successful_items'] = successful_items


class QuerySyntaxError(GenomeMCPError):
    """Exception raised for query syntax errors."""
    
    def __init__(self, message: str, query: Optional[str] = None, syntax_position: Optional[int] = None, **kwargs):
        """
        Initialize query syntax error.
        
        Args:
            message: Error message
            query: Query that has syntax error
            syntax_position: Position in query where error occurred
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="QUERY_SYNTAX_ERROR", **kwargs)
        self.query = query
        self.syntax_position = syntax_position
        
        if query:
            self.details['query'] = query
        if syntax_position:
            self.details['syntax_position'] = syntax_position


class ServerError(GenomeMCPError):
    """Exception raised for server-related errors."""
    
    def __init__(self, message: str, server_name: Optional[str] = None, operation: Optional[str] = None, **kwargs):
        """
        Initialize server error.
        
        Args:
            message: Error message
            server_name: Name of the server
            operation: Server operation that failed
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="SERVER_ERROR", **kwargs)
        self.server_name = server_name
        self.operation = operation
        
        if server_name:
            self.details['server_name'] = server_name
        if operation:
            self.details['operation'] = operation


class DatabaseError(GenomeMCPError):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, database_name: Optional[str] = None, table_name: Optional[str] = None, **kwargs):
        """
        Initialize database error.
        
        Args:
            message: Error message
            database_name: Name of the database
            table_name: Name of the table
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(message, error_code="DATABASE_ERROR", **kwargs)
        self.database_name = database_name
        self.table_name = table_name
        
        if database_name:
            self.details['database_name'] = database_name
        if table_name:
            self.details['table_name'] = table_name


def create_error_from_exception(exception: Exception, error_code: Optional[str] = None) -> GenomeMCPError:
    """
    Create a GenomeMCPError from a generic exception.
    
    Args:
        exception: Original exception
        error_code: Optional error code to use
        
    Returns:
        GenomeMCPError: Wrapped exception
    """
    message = str(exception)
    
    # Map common exception types to our custom exceptions
    if isinstance(exception, ValueError):
        return ValidationError(message, original_exception=exception)
    elif isinstance(exception, FileNotFoundError):
        return ResourceError(message, resource_type="file", original_exception=exception)
    elif isinstance(exception, PermissionError):
        return ResourceError(message, resource_type="permission", original_exception=exception)
    elif isinstance(exception, ConnectionError):
        return NetworkError(message, original_exception=exception)
    elif isinstance(exception, TimeoutError):
        return TimeoutError(message, original_exception=exception)
    elif isinstance(exception, MemoryError):
        return ResourceError(message, resource_type="memory", original_exception=exception)
    else:
        return GenomeMCPError(message, error_code=error_code, original_exception=exception)