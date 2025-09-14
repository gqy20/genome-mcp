"""
Tests for configuration management.

This module contains tests for configuration loading, validation, and management.
"""

import pytest
import json
import yaml
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from genome_mcp.configuration import (
    GenomeMCPConfig,
    ConfigManager,
    get_config,
    create_default_config,
    LogLevel,
    CacheConfig,
    RateLimitConfig,
    APIConfig,
    NCBIConfig,
    EnsemblConfig,
    DataSourceConfig,
    ServerConfig,
    LoggingConfig,
)


class TestConfigModels:
    """Test configuration model validation."""

    def test_cache_config_validation(self):
        """Test CacheConfig validation."""
        # Valid config
        config = CacheConfig(enabled=True, ttl=3600, max_size=1000)
        assert config.enabled is True
        assert config.ttl == 3600
        assert config.max_size == 1000

        # Invalid TTL (too small)
        with pytest.raises(ValueError):
            CacheConfig(ttl=30)

        # Invalid TTL (too large)
        with pytest.raises(ValueError):
            CacheConfig(ttl=0.1.00)

        # Invalid max_size (too small)
        with pytest.raises(ValueError):
            CacheConfig(max_size=50)

    def test_rate_limit_config_validation(self):
        """Test RateLimitConfig validation."""
        # Valid config
        config = RateLimitConfig(
            enabled=True, requests_per_minute=60, requests_per_hour=3600, burst_size=10
        )
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 3600
        assert config.burst_size == 10

        # Invalid requests_per_minute
        with pytest.raises(ValueError):
            RateLimitConfig(requests_per_minute=0)

        # Invalid burst_size
        with pytest.raises(ValueError):
            RateLimitConfig(burst_size=0)

    def test_api_config_validation(self):
        """Test APIConfig validation."""
        # Valid config
        config = APIConfig(timeout=30, retry_attempts=3, retry_delay=1.0)
        assert config.timeout == 30
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0

        # Invalid timeout
        with pytest.raises(ValueError):
            APIConfig(timeout=0)

        # Invalid retry_delay
        with pytest.raises(ValueError):
            APIConfig(retry_delay=0.0)

    def test_ncbi_config_defaults(self):
        """Test NCBIConfig default values."""
        config = NCBIConfig()
        assert config.base_url == "https://api.ncbi.nlm.nih.gov"
        assert config.api_key is None
        assert config.max_batch_size == 100
        assert config.rate_limit_delay == 0.1

    def test_ensembl_config_defaults(self):
        """Test EnsemblConfig default values."""
        config = EnsemblConfig()
        assert config.base_url == "https://rest.ensembl.org"
        assert config.server_url == "https://www.ensembl.org"
        assert config.max_batch_size == 1000
        assert config.rate_limit_delay == 0.05

    def test_server_config_validation(self):
        """Test ServerConfig validation."""
        # Valid config
        config = ServerConfig(host="localhost", port=8080)
        assert config.host == "localhost"
        assert config.port == 8080

        # Invalid port
        with pytest.raises(ValueError):
            ServerConfig(port=0)

        with pytest.raises(ValueError):
            ServerConfig(port=70000)

    def test_logging_config_validation(self):
        """Test LoggingConfig validation."""
        # Valid config
        config = LoggingConfig(level=LogLevel.INFO)
        assert config.level == LogLevel.INFO

        # Invalid max_file_size
        with pytest.raises(ValueError):
            LoggingConfig(max_file_size=500000)

        # Invalid backup_count
        with pytest.raises(ValueError):
            LoggingConfig(backup_count=0)

    def test_genome_mcp_config_validation(self):
        """Test GenomeMCPConfig validation."""
        # Valid config
        config = GenomeMCPConfig(app_name="test-app", version="0.1.0", debug=False)
        assert config.app_name == "test-app"
        assert config.version == "0.1.0"
        assert config.debug is False

        # Invalid version format
        with pytest.raises(ValueError):
            GenomeMCPConfig(version="")

        with pytest.raises(ValueError):
            GenomeMCPConfig(version="invalid")

        with pytest.raises(ValueError):
            GenomeMCPConfig(version="1")

    def test_config_with_all_sections(self):
        """Test configuration with all sections."""
        config = GenomeMCPConfig(
            app_name="genome-mcp-test",
            version="2.0.0",
            debug=True,
            enable_ncbi=True,
            enable_ensembl=True,
            cache=CacheConfig(enabled=True, ttl=7200, max_size=2000),
            rate_limit=RateLimitConfig(requests_per_minute=120),
            api=APIConfig(timeout=60, retry_attempts=5),
            server=ServerConfig(host="0.0.0.0", port=9000),
            logging=LoggingConfig(level=LogLevel.DEBUG),
        )

        assert config.app_name == "genome-mcp-test"
        assert config.version == "2.0.0"
        assert config.debug is True
        assert config.cache.ttl == 7200
        assert config.rate_limit.requests_per_minute == 120
        assert config.api.timeout == 60
        assert config.server.host == "0.0.0.0"
        assert config.logging.level == LogLevel.DEBUG


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_config_manager_init(self):
        """Test ConfigManager initialization."""
        manager = ConfigManager()
        assert manager.config_file is None
        assert manager._config is None
        assert manager._env_prefix == "GENOME_MCP_"

        manager = ConfigManager("test_config.json")
        assert manager.config_file == Path("test_config.json")

    def test_load_default_config(self):
        """Test loading default configuration."""
        manager = ConfigManager()
        config = manager.load_config()

        assert isinstance(config, GenomeMCPConfig)
        assert config.app_name == "genome-mcp"
        assert config.version == "0.1.0"
        assert config.debug is False

    def test_load_config_from_json(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "app_name": "test-app",
            "version": "0.1.0",
            "debug": True,
            "cache": {"enabled": True, "ttl": 7200},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            manager = ConfigManager(temp_file)
            config = manager.load_config()

            assert config.app_name == "test-app"
            assert config.version == "0.1.0"
            assert config.debug is True
            assert config.cache.ttl == 7200
        finally:
            os.unlink(temp_file)

    def test_load_config_from_yaml(self):
        """Test loading configuration from YAML file."""
        config_data = """
        app_name: test-app
        version: 0.1.0
        debug: true
        cache:
            enabled: true
            ttl: 7200
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_data)
            temp_file = f.name

        try:
            manager = ConfigManager(temp_file)
            config = manager.load_config()

            assert config.app_name == "test-app"
            assert config.version == "0.1.0"
            assert config.debug is True
            assert config.cache.ttl == 7200
        finally:
            os.unlink(temp_file)

    def test_load_config_file_not_found(self):
        """Test loading configuration from non-existent file."""
        manager = ConfigManager("nonexistent.json")

        with pytest.raises(FileNotFoundError):
            manager.load_config()

    def test_load_config_invalid_format(self):
        """Test loading configuration from invalid file format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("invalid content")
            temp_file = f.name

        try:
            manager = ConfigManager(temp_file)

            with pytest.raises(ValueError):
                manager.load_config()
        finally:
            os.unlink(temp_file)

    @patch.dict(
        os.environ,
        {
            "GENOME_MCP_DEBUG": "true",
            "GENOME_MCP_APP_NAME": "env-test",
            "GENOME_MCP_LOG_LEVEL": "DEBUG",
            "GENOME_MCP_SERVER_PORT": "9000",
            "GENOME_MCP_CACHE_ENABLED": "false",
            "GENOME_MCP_RATE_LIMIT_RPM": "120",
        },
    )
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        manager = ConfigManager()
        config = manager.load_config()

        assert config.debug is True
        assert config.app_name == "env-test"
        assert config.logging.level == LogLevel.DEBUG
        assert config.server.port == 9000
        assert config.cache.enabled is False
        assert config.rate_limit.requests_per_minute == 120

    @patch.dict(os.environ, {"GENOME_MCP_VERSION": "2.1.0"})
    def test_env_override_file_config(self):
        """Test that environment variables override file configuration."""
        config_data = {"app_name": "file-app", "version": "0.1.0", "debug": False}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            manager = ConfigManager(temp_file)
            config = manager.load_config()

            # File values
            assert config.app_name == "file-app"
            assert config.debug is False

            # Environment override
            assert config.version == "2.1.0"
        finally:
            os.unlink(temp_file)

    def test_get_config_before_load(self):
        """Test getting configuration before loading."""
        manager = ConfigManager()

        with pytest.raises(ValueError):
            manager.get_config()

    def test_get_config_after_load(self):
        """Test getting configuration after loading."""
        manager = ConfigManager()
        config = manager.load_config()

        retrieved_config = manager.get_config()
        assert retrieved_config is config
        assert retrieved_config.app_name == "genome-mcp"

    def test_save_config_no_file(self):
        """Test saving configuration without specifying file."""
        manager = ConfigManager()
        manager.load_config()

        with pytest.raises(ValueError):
            manager.save_config()

    def test_save_config_json(self):
        """Test saving configuration to JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            # Delete the file so we can test creation
            os.unlink(temp_file)

            manager = ConfigManager(temp_file)
            # Create a default config without loading from file
            config = GenomeMCPConfig(app_name="saved-app")

            manager.save_config(config)

            # Verify file was created and contains correct data
            assert Path(temp_file).exists()

            with open(temp_file, "r") as f:
                saved_data = json.load(f)

            assert saved_data["app_name"] == "saved-app"
        finally:
            if Path(temp_file).exists():
                os.unlink(temp_file)

    def test_save_config_yaml(self):
        """Test saving configuration to YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_file = f.name

        try:
            # Delete the file so we can test creation
            os.unlink(temp_file)

            manager = ConfigManager(temp_file)
            # Create a default config without loading from file
            config = GenomeMCPConfig(app_name="saved-app")

            manager.save_config(config)

            # Verify file was created and contains correct data
            assert Path(temp_file).exists()

            with open(temp_file, "r") as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["app_name"] == "saved-app"
        finally:
            if Path(temp_file).exists():
                os.unlink(temp_file)

    def test_reload_config(self):
        """Test reloading configuration."""
        config_data = {"app_name": "original-app", "version": "0.1.0"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            manager = ConfigManager(temp_file)
            config = manager.load_config()
            assert config.app_name == "original-app"

            # Modify file
            config_data["app_name"] = "reloaded-app"
            with open(temp_file, "w") as f:
                json.dump(config_data, f)

            # Reload
            reloaded_config = manager.reload_config()
            assert reloaded_config.app_name == "reloaded-app"
        finally:
            os.unlink(temp_file)

    def test_get_value(self):
        """Test getting specific configuration values."""
        manager = ConfigManager()
        config = manager.load_config()

        # Test existing values
        assert manager.get_value("app_name") == "genome-mcp"
        assert manager.get_value("cache.enabled") is True
        assert manager.get_value("server.port") == 8080

        # Test non-existing values with default
        assert manager.get_value("nonexistent.key") is None
        assert manager.get_value("nonexistent.key", "default") == "default"

    def test_set_value(self):
        """Test setting specific configuration values."""
        manager = ConfigManager()
        config = manager.load_config()

        # Set a value
        manager.set_value("app_name", "modified-app")
        manager.set_value("cache.enabled", False)
        manager.set_value("server.port", 9000)

        # Verify values were set
        assert manager.get_value("app_name") == "modified-app"
        assert manager.get_value("cache.enabled") is False
        assert manager.get_value("server.port") == 9000


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_config_function(self):
        """Test get_config convenience function."""
        config = get_config()

        assert isinstance(config, GenomeMCPConfig)
        assert config.app_name == "genome-mcp"
        assert config.version == "0.1.0"

    def test_create_default_config_json(self):
        """Test creating default configuration file (JSON)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            # Delete the file so we can test creation
            os.unlink(temp_file)

            create_default_config(temp_file)

            # Verify file was created
            assert Path(temp_file).exists()

            # Verify content
            with open(temp_file, "r") as f:
                config_data = json.load(f)

            assert config_data["app_name"] == "genome-mcp"
            assert config_data["version"] == "0.1.0"
        finally:
            if Path(temp_file).exists():
                os.unlink(temp_file)

    def test_create_default_config_yaml(self):
        """Test creating default configuration file (YAML)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_file = f.name

        try:
            # Delete the file so we can test creation
            os.unlink(temp_file)

            create_default_config(temp_file)

            # Verify file was created
            assert Path(temp_file).exists()

            # Verify content
            with open(temp_file, "r") as f:
                config_data = yaml.safe_load(f)

            assert config_data["app_name"] == "genome-mcp"
            assert config_data["version"] == "0.1.0"
        finally:
            if Path(temp_file).exists():
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__])
