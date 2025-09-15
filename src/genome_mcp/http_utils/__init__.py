"""
HTTP utility functions for Genome MCP.

This module provides utility functions for making HTTP requests, handling responses,
and managing network operations with proper error handling and retry logic.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import structlog

from genome_mcp.exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    TimeoutError,
)

logger = structlog.get_logger(__name__)


class HTTPClient:
    """HTTP client with retry logic and error handling."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        user_agent: str = "Genome-MCP/1.0.0",
        api_key: Optional[str] = None,
    ):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            user_agent: User agent string
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.user_agent = user_agent
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def start_session(self) -> None:
        """Start HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            headers = self._build_headers()

            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(
                    limit=100, limit_per_host=30, ttl_dns_cache=300, use_dns_cache=True
                ),
            )

    async def close_session(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _extract_retry_after(self, response: aiohttp.ClientResponse) -> Optional[int]:
        """Extract Retry-After header value."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                # Try to parse HTTP date
                from email.utils import parsedate_to_datetime

                try:
                    retry_date = parsedate_to_datetime(retry_after)
                    return max(0, int(retry_date.timestamp() - time.time()))
                except (ValueError, TypeError):
                    pass
        return None

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        url = self._build_url(endpoint)

        for attempt in range(self.max_retries + 1):
            try:
                if self.session is None:
                    await self.start_session()

                async with self.session.request(method, url, **kwargs) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = self._extract_retry_after(response)
                        if retry_after and attempt < self.max_retries:
                            logger.warning(
                                "Rate limited, retrying after %d seconds", retry_after
                            )
                            await asyncio.sleep(retry_after)
                            continue

                        raise RateLimitError(
                            message=f"Rate limit exceeded for {url}",
                            status_code=response.status,
                            url=url,
                            retry_after=retry_after,
                            response_data=await response.text(),
                        )

                    # Handle authentication errors
                    if response.status == 401:
                        raise AuthenticationError(
                            message="Authentication failed",
                            status_code=response.status,
                            url=url,
                            response_data=await response.text(),
                        )

                    # Handle other error status codes
                    if response.status >= 400:
                        response_text = await response.text()
                        raise APIError(
                            message=f"HTTP {response.status} error for {url}",
                            status_code=response.status,
                            url=url,
                            response_data={"response": response_text},
                        )

                    # Parse successful response
                    try:
                        return await response.json()
                    except ValueError:
                        # Return raw text if JSON parsing fails
                        return {"data": await response.text()}

            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    logger.warning(
                        "Request timed out, retrying (%d/%d)",
                        attempt + 1,
                        self.max_retries,
                    )
                    await asyncio.sleep(self.retry_delay * (2**attempt))
                    continue

                raise TimeoutError(
                    message=f"Request timeout for {url}",
                    timeout_duration=self.timeout,
                    operation="http_request",
                )

            except aiohttp.ClientError as e:
                if attempt < self.max_retries:
                    logger.warning(
                        "Network error, retrying (%d/%d): %s",
                        attempt + 1,
                        self.max_retries,
                        str(e),
                    )
                    await asyncio.sleep(self.retry_delay * (2**attempt))
                    continue

                raise NetworkError(
                    message=f"Network error for {url}: {str(e)}", original_exception=e
                )

        # This should never be reached due to the loop logic
        raise NetworkError(f"Failed to complete request to {url}")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make GET request."""
        return await self._make_request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        if json_data:
            return await self._make_request(
                "POST", endpoint, json=json_data, headers=headers
            )
        else:
            return await self._make_request(
                "POST", endpoint, data=data, headers=headers
            )

    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make PUT request."""
        if json_data:
            return await self._make_request(
                "PUT", endpoint, json=json_data, headers=headers
            )
        else:
            return await self._make_request("PUT", endpoint, data=data, headers=headers)

    async def delete(
        self, endpoint: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self._make_request("DELETE", endpoint, headers=headers)


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 3600):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = []
        self.hour_requests = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.time()

            # Clean old requests
            self.minute_requests = [t for t in self.minute_requests if now - t < 60]
            self.hour_requests = [t for t in self.hour_requests if now - t < 3600]

            # Check limits
            if len(self.minute_requests) >= self.requests_per_minute:
                sleep_time = 60 - (now - self.minute_requests[0])
                if sleep_time > 0:
                    logger.info("Rate limiting: sleeping for %.2f seconds", sleep_time)
                    await asyncio.sleep(sleep_time)

            if len(self.hour_requests) >= self.requests_per_hour:
                sleep_time = 3600 - (now - self.hour_requests[0])
                if sleep_time > 0:
                    logger.info("Rate limiting: sleeping for %.2f seconds", sleep_time)
                    await asyncio.sleep(sleep_time)

            # Record this request
            now = time.time()
            self.minute_requests.append(now)
            self.hour_requests.append(now)


async def fetch_with_retry(
    url: str,
    method: str = "GET",
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 30.0,
    **kwargs,
) -> Dict[str, Any]:
    """
    Simple HTTP request with retry logic.

    Args:
        url: URL to fetch
        method: HTTP method
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries
        timeout: Request timeout
        **kwargs: Additional arguments passed to aiohttp

    Returns:
        Response data as dictionary
    """
    timeout_config = aiohttp.ClientTimeout(total=timeout)

    for attempt in range(max_retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status >= 400:
                        response_text = await response.text()
                        raise APIError(
                            message=f"HTTP {response.status} error",
                            status_code=response.status,
                            url=url,
                            response_data={"response": response_text},
                        )

                    try:
                        return await response.json()
                    except ValueError:
                        return {"data": await response.text()}

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            if attempt < max_retries:
                await asyncio.sleep(retry_delay * (2**attempt))
                continue

            raise NetworkError(f"Failed to fetch {url}: {str(e)}", original_exception=e)

    raise NetworkError(f"Failed to complete request to {url}")


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def sanitize_url(url: str) -> str:
    """
    Sanitize URL by removing sensitive parameters.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL
    """
    parsed = urlparse(url)

    # Remove sensitive query parameters
    sensitive_params = {"api_key", "token", "password", "secret"}
    if parsed.query:
        query_params = []
        for param in parsed.query.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                if key.lower() in sensitive_params:
                    value = "***"
                query_params.append(f"{key}={value}")
            else:
                query_params.append(param)

        sanitized_query = "&".join(query_params)
    else:
        sanitized_query = ""

    # Reconstruct URL
    sanitized_url = parsed._replace(query=sanitized_query).geturl()
    return sanitized_url


async def batch_requests(
    urls: List[str], max_concurrent: int = 10, **kwargs
) -> List[Dict[str, Any]]:
    """
    Make multiple HTTP requests concurrently with controlled concurrency.

    Args:
        urls: List of URLs to fetch
        max_concurrent: Maximum concurrent requests
        **kwargs: Additional arguments passed to fetch_with_retry

    Returns:
        List of response data
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_single(url: str) -> Dict[str, Any]:
        async with semaphore:
            try:
                return await fetch_with_retry(url, **kwargs)
            except Exception as e:
                logger.error("Failed to fetch %s: %s", url, str(e))
                return {"error": str(e), "url": url}

    tasks = [fetch_single(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results and handle exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append(
                {"error": str(result), "url": urls[i], "success": False}
            )
        else:
            processed_results.append({"data": result, "url": urls[i], "success": True})

    return processed_results
