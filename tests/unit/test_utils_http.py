"""
Tests for HTTP utility functions.

This module contains tests for HTTP client, rate limiting, and other HTTP-related utilities.
"""

import pytest
import asyncio
import aiohttp
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from genome_mcp.utils.http import (
    HTTPClient,
    RateLimiter,
    fetch_with_retry,
    validate_url,
    sanitize_url,
    batch_requests,
)
from genome_mcp.exceptions import (
    ValidationError,
    NetworkError,
    RateLimitError,
    AuthenticationError,
    TimeoutError,
)


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_construction(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(requests_per_minute=10, requests_per_hour=600)
        assert limiter.requests_per_minute == 10
        assert limiter.requests_per_hour == 600
        assert len(limiter.minute_requests) == 0
        assert len(limiter.hour_requests) == 0
    
    def test_rate_limiter_single_request(self):
        """Test rate limiter with single request."""
        limiter = RateLimiter(requests_per_minute=10, requests_per_hour=600)
        # This should not block since we're under the limit
        asyncio.run(limiter.acquire())
        assert len(limiter.minute_requests) == 1
        assert len(limiter.hour_requests) == 1
    
    def test_rate_limiter_under_limit(self):
        """Test rate limiter when under limit."""
        limiter = RateLimiter(requests_per_minute=3, requests_per_hour=600)
        
        # Add 2 requests (under limit)
        now = time.time()
        limiter.minute_requests = [now - 1, now - 2]
        limiter.hour_requests = [now - 1, now - 2]
        
        # This should not block
        asyncio.run(limiter.acquire())
        assert len(limiter.minute_requests) == 3
    
    def test_rate_limiter_at_limit(self):
        """Test rate limiter when at limit."""
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=600)
        
        # Add 2 requests (at limit)
        now = time.time()
        limiter.minute_requests = [now - 1, now - 2]
        limiter.hour_requests = [now - 1, now - 2]
        
        # This should block since we're at the limit
        start_time = time.time()
        asyncio.run(limiter.acquire())
        end_time = time.time()
        
        # Should have waited at least some time
        assert end_time - start_time > 0
    
    def test_rate_limiter_expired_requests(self):
        """Test rate limiter with expired requests."""
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=600)
        
        # Add expired requests that should be cleaned up
        old_time = time.time() - 120  # 2 minutes ago
        limiter.minute_requests = [old_time, old_time - 1]
        limiter.hour_requests = [old_time, old_time - 1]
        
        # This should not block since old requests are cleaned up
        asyncio.run(limiter.acquire())
        assert len(limiter.minute_requests) == 1
    
  

class TestHTTPClient:
    """Test HTTP client functionality."""
    
    @pytest.fixture
    def http_client(self):
        """Create HTTP client fixture."""
        return HTTPClient(
            base_url="https://api.example.com",
            api_key="test_key",
            timeout=30,
            max_retries=3
        )
    
    def test_http_client_construction(self, http_client):
        """Test HTTPClient initialization."""
        assert http_client.base_url == "https://api.example.com"
        assert http_client.api_key == "test_key"
        assert http_client.timeout == 30
        assert http_client.max_retries == 3
        assert http_client.session is None
    
    def test_http_client_no_auth(self):
        """Test HTTPClient without authentication."""
        client = HTTPClient(base_url="https://api.example.com")
        assert client.api_key is None
    
    @pytest.mark.asyncio
    async def test_http_client_build_url(self, http_client):
        """Test URL building."""
        # Test with endpoint
        url = http_client._build_url("/genes/123")
        assert url == "https://api.example.com/genes/123"
        
        # Test with full URL
        url = http_client._build_url("https://other.com/api")
        assert url == "https://other.com/api"
    
    @pytest.mark.asyncio
    async def test_http_client_build_headers(self, http_client):
        """Test header building."""
        headers = http_client._build_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"].startswith("Genome-MCP/")
        assert headers["Authorization"] == "Bearer test_key"
    
    @pytest.mark.asyncio
    async def test_http_client_build_headers_no_auth(self):
        """Test header building without authentication."""
        client = HTTPClient(base_url="https://api.example.com")
        headers = client._build_headers()
        
        assert "Authorization" not in headers
    
    @pytest.mark.asyncio
    async def test_http_client_handle_response_success(self, http_client):
        """Test successful response handling."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.text = '{"data": "test"}'
        
        result = await http_client._handle_response(mock_response)
        assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_http_client_handle_response_error(self, http_client):
        """Test error response handling."""
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json.return_value = {"error": "Bad request"}
        mock_response.text = '{"error": "Bad request"}'
        
        with pytest.raises(ValidationError):
            await http_client._handle_response(mock_response)
    
    @pytest.mark.asyncio
    async def test_http_client_handle_response_rate_limit(self, http_client):
        """Test rate limit response handling."""
        # Mock rate limit response
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "5"}
        mock_response.json.return_value = {"error": "Rate limited"}
        mock_response.text = '{"error": "Rate limited"}'
        
        with pytest.raises(RateLimitError) as exc_info:
            await http_client._handle_response(mock_response)
        
        assert exc_info.value.retry_after == 5
    
    @pytest.mark.asyncio
    async def test_http_client_handle_response_auth_error(self, http_client):
        """Test authentication error response handling."""
        # Mock auth error response
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.text = '{"error": "Unauthorized"}'
        
        with pytest.raises(AuthenticationError):
            await http_client._handle_response(mock_response)
    
    @pytest.mark.asyncio
    async def test_http_client_get_success(self, http_client):
        """Test successful GET request."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"data": "test"}
        
        with patch.object(aiohttp.ClientSession, 'request', return_value=mock_response):
            result = await http_client.get("/test")
            assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_http_client_post_success(self, http_client):
        """Test successful POST request."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"data": "created"}
        
        with patch.object(aiohttp.ClientSession, 'request', return_value=mock_response):
            result = await http_client.post("/test", data={"key": "value"})
            assert result == {"data": "created"}
    
    @pytest.mark.asyncio
    async def test_http_client_put_success(self, http_client):
        """Test successful PUT request."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"data": "updated"}
        
        with patch.object(aiohttp.ClientSession, 'request', return_value=mock_response):
            result = await http_client.put("/test", data={"key": "value"})
            assert result == {"data": "updated"}
    
    @pytest.mark.asyncio
    async def test_http_client_delete_success(self, http_client):
        """Test successful DELETE request."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"data": "deleted"}
        
        with patch.object(aiohttp.ClientSession, 'request', return_value=mock_response):
            result = await http_client.delete("/test")
            assert result == {"data": "deleted"}
    
    @pytest.mark.asyncio
    async def test_http_client_network_error(self, http_client):
        """Test network error handling."""
        with patch.object(aiohttp.ClientSession, 'request', side_effect=aiohttp.ClientError):
            with pytest.raises(NetworkError):
                await http_client.get("/test")
    
    @pytest.mark.asyncio
    async def test_http_client_timeout_error(self, http_client):
        """Test timeout error handling."""
        with patch.object(aiohttp.ClientSession, 'request', side_effect=asyncio.TimeoutError):
            with pytest.raises(TimeoutError):
                await http_client.get("/test")


class TestFetchWithRetry:
    """Test fetch_with_retry functionality."""
    
    @pytest.mark.asyncio
    async def test_fetch_with_retry_success(self):
        """Test successful fetch with retry."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"data": "test"}
        
        with patch.object(aiohttp.ClientSession, 'get', return_value=mock_response):
            result = await fetch_with_retry("https://api.example.com/test")
            assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_fetch_with_retry_with_retries(self):
        """Test fetch with retry on failure."""
        call_count = 0
        
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise aiohttp.ClientError("Network error")
            
            # Mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"data": "test"}
            return mock_response
        
        with patch.object(aiohttp.ClientSession, 'get', side_effect=mock_get):
            result = await fetch_with_retry(
                "https://api.example.com/test",
                max_retries=3,
                retry_delay=0.1
            )
            assert result == {"data": "test"}
            assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_fetch_with_retry_max_retries_exceeded(self):
        """Test fetch with retry when max retries exceeded."""
        with patch.object(aiohttp.ClientSession, 'get', side_effect=aiohttp.ClientError):
            with pytest.raises(NetworkError):
                await fetch_with_retry(
                    "https://api.example.com/test",
                    max_retries=2,
                    retry_delay=0.1
                )


class TestURLValidation:
    """Test URL validation functions."""
    
    def test_validate_url_valid(self):
        """Test validation of valid URLs."""
        valid_urls = [
            "https://api.example.com",
            "http://localhost:8080",
            "https://subdomain.example.com/path",
            "https://example.com:443/api",
        ]
        
        for url in valid_urls:
            assert validate_url(url) == url
    
    def test_validate_url_invalid(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "javascript:alert(1)",
            "example.com",
            "",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                validate_url(url)
    
    def test_sanitize_url_basic(self):
        """Test basic URL sanitization."""
        url = "https://api.example.com/path?param=value#fragment"
        sanitized = sanitize_url(url)
        
        # Should preserve basic URL structure
        assert sanitized.startswith("https://api.example.com")
    
    def test_sanitize_url_credentials(self):
        """Test URL sanitization with credentials."""
        url = "https://user:password@api.example.com/path"
        sanitized = sanitize_url(url)
        
        # Should remove credentials
        assert "user:password" not in sanitized
    
    def test_sanitize_url_query_params(self):
        """Test URL sanitization with sensitive query parameters."""
        url = "https://api.example.com/path?api_key=secret&public=param"
        sanitized = sanitize_url(url)
        
        # Should remove sensitive parameters
        assert "api_key" not in sanitized
        assert "secret" not in sanitized
        assert "public" in sanitized


class TestBatchRequests:
    """Test batch request functionality."""
    
    @pytest.mark.asyncio
    async def test_batch_requests_success(self):
        """Test successful batch requests."""
        urls = [
            "https://api.example.com/item1",
            "https://api.example.com/item2",
            "https://api.example.com/item3",
        ]
        
        # Mock responses
        async def mock_fetch(url, **kwargs):
            await asyncio.sleep(0.01)  # Simulate network delay
            return {"url": url, "data": f"data for {url}"}
        
        results = await batch_requests(urls, mock_fetch, max_concurrent=2)
        
        assert len(results) == 3
        assert all("url" in result for result in results)
        assert all("data" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_batch_requests_with_errors(self):
        """Test batch requests with some errors."""
        urls = [
            "https://api.example.com/item1",
            "https://api.example.com/item2",
            "https://api.example.com/item3",
        ]
        
        async def mock_fetch(url, **kwargs):
            if "item2" in url:
                raise NetworkError("Network error")
            return {"url": url, "data": f"data for {url}"}
        
        results = await batch_requests(urls, mock_fetch, max_concurrent=2, continue_on_error=True)
        
        assert len(results) == 2  # One request failed
        assert all("url" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_batch_requests_rate_limiting(self):
        """Test batch requests with rate limiting."""
        urls = ["https://api.example.com/item1", "https://api.example.com/item2"]
        
        call_times = []
        
        async def mock_fetch(url, **kwargs):
            call_times.append(time.time())
            return {"url": url, "data": "data"}
        
        # Add rate limiting
        rate_limiter = RateLimiter(max_requests=1, time_window=0.1)
        
        results = await batch_requests(
            urls, 
            mock_fetch, 
            max_concurrent=2,
            rate_limiter=rate_limiter
        )
        
        assert len(results) == 2
        # Should have some delay between requests due to rate limiting
        assert call_times[1] - call_times[0] >= 0.05


if __name__ == "__main__":
    pytest.main([__file__])