"""
Base MCP Server implementation.

This module provides the base functionality for all MCP servers in the Genome MCP system.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog

from genome_mcp.configuration import GenomeMCPConfig, get_config
from genome_mcp.core import generate_cache_key, log_execution_time
from genome_mcp.exceptions import (
    GenomeMCPError,
    ValidationError,
    create_error_from_exception,
)
from genome_mcp.http_utils import HTTPClient, RateLimiter

logger = structlog.get_logger(__name__)


@dataclass
class ServerCapabilities:
    """Server capabilities description."""

    name: str
    version: str
    description: str
    supports_batch: bool = True
    supports_streaming: bool = False
    max_batch_size: int = 100
    rate_limit_requests: int = 60
    rate_limit_window: int = 60  # seconds

    # Supported operations
    operations: List[str] = field(default_factory=list)
    data_formats: List[str] = field(default_factory=lambda: ["json"])

    # Authentication requirements
    requires_auth: bool = False
    auth_methods: List[str] = field(default_factory=list)


@dataclass
class ServerStats:
    """Server statistics."""

    requests_total: int = 0
    requests_success: int = 0
    requests_failed: int = 0
    avg_response_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    # Rate limiting stats
    rate_limit_hits: int = 0
    concurrent_requests: int = 0

    # Data transfer stats
    bytes_sent: int = 0
    bytes_received: int = 0

    def update_response_time(self, response_time: float) -> None:
        """Update average response time."""
        if self.requests_total == 0:
            self.avg_response_time = response_time
        else:
            # Rolling average
            alpha = 0.1
            self.avg_response_time = (
                alpha * response_time + (1 - alpha) * self.avg_response_time
            )

    def increment_success(
        self, response_time: float, bytes_sent: int = 0, bytes_received: int = 0
    ) -> None:
        """Increment success counter."""
        self.requests_total += 1
        self.requests_success += 1
        self.update_response_time(response_time)
        self.bytes_sent += bytes_sent
        self.bytes_received += bytes_received

    def increment_failure(self) -> None:
        """Increment failure counter."""
        self.requests_total += 1
        self.requests_failed += 1


class BaseMCPServer(ABC):
    """Base class for all MCP servers."""

    def __init__(self, config: Optional[GenomeMCPConfig] = None):
        """Initialize the base server.

        Args:
            config: Configuration object. If None, loads from default config.
        """
        self.config = config or get_config()
        self.stats = ServerStats()
        self._http_client: Optional[HTTPClient] = None
        self._rate_limiter: Optional[RateLimiter] = None
        self._cache: Optional[Dict[str, Any]] = None
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Initialize logger
        self.logger = structlog.get_logger(self.__class__.__name__)

        # Set up capabilities
        self.capabilities = self._define_capabilities()

        self.logger.info(
            "Server initialized",
            server_name=self.capabilities.name,
            version=self.capabilities.version,
        )

    @abstractmethod
    def _define_capabilities(self) -> ServerCapabilities:
        """Define server capabilities. Must be implemented by subclasses."""
        pass

    @property
    def http_client(self) -> HTTPClient:
        """Get HTTP client instance."""
        if self._http_client is None:
            self._http_client = HTTPClient(
                base_url=self._get_base_url(),
                timeout=self.config.api.timeout,
                max_retries=self.config.api.retry_attempts,
                user_agent=self.config.api.user_agent,
            )
        return self._http_client

    @property
    def rate_limiter(self) -> RateLimiter:
        """Get rate limiter instance."""
        if self._rate_limiter is None:
            self._rate_limiter = RateLimiter(
                requests_per_minute=self.capabilities.rate_limit_requests,
                requests_per_hour=self.capabilities.rate_limit_requests
                * 60
                // self.capabilities.rate_limit_window,
            )
        return self._rate_limiter

    @abstractmethod
    def _get_base_url(self) -> str:
        """Get base URL for the service. Must be implemented by subclasses."""
        pass

    async def start(self) -> None:
        """Start the server."""
        if self._running:
            self.logger.warning("Server already running")
            return

        self._running = True
        self._shutdown_event.clear()

        self.logger.info("Server started", capabilities=self.capabilities.__dict__)

    async def stop(self) -> None:
        """Stop the server."""
        if not self._running:
            self.logger.warning("Server not running")
            return

        self._running = False
        self._shutdown_event.set()

        # Close HTTP client
        if self._http_client:
            await self._http_client.close_session()
            self._http_client = None

        self.logger.info("Server stopped")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health_status = {
            "status": "healthy",
            "server": self.capabilities.name,
            "version": self.capabilities.version,
            "uptime": time.time(),  # In practice, track actual uptime
            "stats": {
                "requests_total": self.stats.requests_total,
                "requests_success": self.stats.requests_success,
                "requests_failed": self.stats.requests_failed,
                "avg_response_time": self.stats.avg_response_time,
                "success_rate": (
                    self.stats.requests_success / self.stats.requests_total
                    if self.stats.requests_total > 0
                    else 0.0
                ),
            },
        }

        return health_status

    @log_execution_time("request")
    async def execute_request(
        self, operation: str, params: Dict[str, Any], use_cache: bool = True
    ) -> Dict[str, Any]:
        """Execute a single request."""
        start_time = time.time()
        self.stats.concurrent_requests += 1

        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Generate cache key
            cache_key = None
            if use_cache and self.config.enable_caching:
                cache_key = generate_cache_key(
                    f"{self.capabilities.name}:{operation}", **params
                )

                # Check cache
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    self.stats.cache_hits += 1
                    return cached_result

            self.stats.cache_misses += 1

            # Validate request
            self._validate_request(operation, params)

            # Execute operation
            result = await self._execute_operation(operation, params)

            # Cache result
            if use_cache and cache_key and self.config.enable_caching:
                self._set_cache(cache_key, result)

            # Update stats
            response_time = time.time() - start_time
            self.stats.increment_success(response_time)

            return result

        except Exception as e:
            response_time = time.time() - start_time
            self.stats.increment_failure()

            # Log error
            self.logger.error(
                "Request failed",
                operation=operation,
                params=params,
                error=str(e),
                response_time=response_time,
            )

            # Convert to appropriate exception
            if isinstance(e, GenomeMCPError):
                raise
            else:
                raise create_error_from_exception(e)

        finally:
            self.stats.concurrent_requests -= 1

    async def execute_batch(
        self, requests: List[Dict[str, Any]], use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute multiple requests in batch."""
        if not self.capabilities.supports_batch:
            raise ValidationError(
                f"{self.capabilities.name} does not support batch operations"
            )

        if len(requests) > self.capabilities.max_batch_size:
            raise ValidationError(
                f"Batch size {len(requests)} exceeds maximum {self.capabilities.max_batch_size}"
            )

        # Execute requests concurrently
        tasks = []
        for request in requests:
            task = self.execute_request(
                operation=request["operation"],
                params=request.get("params", {}),
                use_cache=use_cache,
            )
            tasks.append(task)

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "success": False,
                            "error": str(result),
                            "error_type": type(result).__name__,
                        }
                    )
                else:
                    processed_results.append({"success": True, "result": result})

            return processed_results

        except Exception as e:
            self.logger.error("Batch execution failed", error=str(e))
            raise

    async def execute_stream(
        self, operation: str, params: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming request."""
        if not self.capabilities.supports_streaming:
            raise ValidationError(
                f"{self.capabilities.name} does not support streaming operations"
            )

        # For now, yield a single result
        # Subclasses can override for true streaming
        result = await self.execute_request(operation, params)
        yield {"data": result}

    @abstractmethod
    async def _execute_operation(
        self, operation: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific operation. Must be implemented by subclasses."""
        pass

    def _validate_request(self, operation: str, params: Dict[str, Any]) -> None:
        """Validate request parameters."""
        if operation not in self.capabilities.operations:
            raise ValidationError(
                f"Unsupported operation: {operation}",
                field_name="operation",
                field_value=operation,
            )

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache."""
        if not self._cache:
            return None

        cached = self._cache.get(cache_key)
        if cached and time.time() < cached.get("expires", 0):
            data = cached.get("data")
            return data if data is not None else {}

        return None

    def _set_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Set result in cache."""
        if not self._cache:
            # Initialize cache
            self._cache = {}

        # Simple cache with TTL
        self._cache[cache_key] = {
            "data": data,
            "expires": time.time() + self.config.cache.ttl,
        }

        # Clean up expired entries if cache is too large
        if len(self._cache) > self.config.cache.max_size:
            current_time = time.time()
            expired_keys = [
                key
                for key, value in self._cache.items()
                if value.get("expires", 0) < current_time
            ]
            for key in expired_keys:
                del self._cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "server": self.capabilities.name,
            "version": self.capabilities.version,
            "running": self._running,
            "stats": self.stats.__dict__,
            "capabilities": self.capabilities.__dict__,
        }

    def reset_stats(self) -> None:
        """Reset server statistics."""
        self.stats = ServerStats()
        self.logger.info("Server statistics reset")

    async def __aenter__(self) -> "BaseMCPServer":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()
