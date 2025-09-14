"""
Configuration management for Genome MCP.

This module provides configuration management functionality for the Genome MCP system,
including environment-based configuration, validation, and settings management.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class LogLevel(str, Enum):
    """Log levels for the application."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _yaml_enum_representer(dumper, data):
    """Custom YAML representer for enum values."""
    return dumper.represent_str(data.value)


# Configure YAML to handle enums properly
yaml.add_representer(LogLevel, _yaml_enum_representer)


class CacheConfig(BaseModel):
    """Cache configuration settings."""

    enabled: bool = Field(True, description="Enable caching")
    ttl: int = Field(3600, ge=60, le=86400, description="Cache TTL in seconds")
    max_size: int = Field(1000, ge=100, le=10000, description="Maximum cache entries")
    backend: str = Field("memory", description="Cache backend (memory, redis, file)")


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = Field(True, description="Enable rate limiting")
    requests_per_minute: int = Field(
        60, ge=1, le=1000, description="Requests per minute"
    )
    requests_per_hour: int = Field(
        3600, ge=1, le=100000, description="Requests per hour"
    )
    burst_size: int = Field(10, ge=1, le=100, description="Burst request limit")


class APIConfig(BaseModel):
    """API endpoint configurations."""

    timeout: int = Field(30, ge=1, le=300, description="API timeout in seconds")
    retry_attempts: int = Field(3, ge=0, le=10, description="Number of retry attempts")
    retry_delay: float = Field(
        1.0, ge=0.1, le=10.0, description="Delay between retries in seconds"
    )
    user_agent: str = Field("Genome-MCP/1.0.0", description="User agent string")


class NCBIConfig(BaseModel):
    """NCBI-specific configuration."""

    base_url: str = Field(
        "https://api.ncbi.nlm.nih.gov", description="NCBI API base URL"
    )
    api_key: Optional[str] = Field(None, description="NCBI API key")
    max_batch_size: int = Field(
        100, ge=1, le=500, description="Maximum batch size for requests"
    )
    rate_limit_delay: float = Field(
        0.1, ge=0.0, le=1.0, description="Rate limit delay in seconds"
    )


class EnsemblConfig(BaseModel):
    """Ensembl-specific configuration."""

    base_url: str = Field(
        "https://rest.ensembl.org", description="Ensembl API base URL"
    )
    server_url: str = Field("https://www.ensembl.org", description="Ensembl server URL")
    max_batch_size: int = Field(
        1000, ge=1, le=5000, description="Maximum batch size for requests"
    )
    rate_limit_delay: float = Field(
        0.05, ge=0.0, le=1.0, description="Rate limit delay in seconds"
    )


class DataSourceConfig(BaseModel):
    """Data source specific configurations."""

    ncbi: NCBIConfig = Field(default_factory=NCBIConfig)
    ensembl: EnsemblConfig = Field(default_factory=EnsemblConfig)


class ServerConfig(BaseModel):
    """MCP server configuration."""

    host: str = Field("localhost", description="Server host")
    port: int = Field(8080, ge=1, le=65535, description="Server port")
    debug: bool = Field(False, description="Enable debug mode")
    cors_enabled: bool = Field(True, description="Enable CORS")
    cors_origins: List[str] = Field(["*"], description="Allowed CORS origins")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(LogLevel.INFO, description="Log level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format"
    )
    file_path: Optional[str] = Field(None, description="Log file path")
    max_file_size: int = Field(
        10485760, ge=1048576, le=104857600, description="Max log file size in bytes"
    )
    backup_count: int = Field(5, ge=1, le=20, description="Number of backup log files")


class GenomeMCPConfig(BaseModel):
    """Main configuration for Genome MCP."""

    # Core settings
    app_name: str = Field("genome-mcp", description="Application name")
    version: str = Field("1.0.0", description="Application version")
    debug: bool = Field(False, description="Enable debug mode")

    # Feature flags
    enable_ncbi: bool = Field(True, description="Enable NCBI data source")
    enable_ensembl: bool = Field(True, description="Enable Ensembl data source")
    enable_caching: bool = Field(True, description="Enable caching")
    enable_rate_limiting: bool = Field(True, description="Enable rate limiting")

    # Component configurations
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    data_sources: DataSourceConfig = Field(default_factory=DataSourceConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate version format."""
        if not v:
            raise ValueError("Version cannot be empty")
        # Simple semantic version validation
        parts = v.split(".")
        if len(parts) < 2 or len(parts) > 4:
            raise ValueError("Version must be in format major.minor[.patch[.build]]")
        for part in parts:
            if not part.isdigit():
                raise ValueError("Version parts must be numeric")
        return v

    model_config = ConfigDict(use_enum_values=True)


class ConfigManager:
    """Configuration manager for Genome MCP."""

    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """Initialize configuration manager.

        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        self.config_file = Path(config_file) if config_file else None
        self._config: Optional[GenomeMCPConfig] = None
        self._env_prefix = "GENOME_MCP_"

    def load_config(self) -> GenomeMCPConfig:
        """Load configuration from file and environment variables.

        Returns:
            GenomeMCPConfig: Loaded configuration

        Raises:
            FileNotFoundError: If config file is specified but not found
            ValueError: If config file format is invalid
        """
        # Start with default configuration
        config_data = {}

        # Load from file if specified
        if self.config_file:
            if not self.config_file.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {self.config_file}"
                )

            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    if self.config_file.suffix.lower() in [".yaml", ".yml"]:
                        file_config = yaml.safe_load(f)
                    elif self.config_file.suffix.lower() == ".json":
                        file_config = json.load(f)
                    else:
                        raise ValueError(
                            f"Unsupported config file format: {self.config_file.suffix}"
                        )

                if file_config:
                    config_data.update(file_config)

            except Exception as e:
                raise ValueError(f"Error loading configuration file: {e}")

        # Override with environment variables
        env_config = self._load_from_env()
        if env_config:
            config_data.update(env_config)

        # Create configuration object
        self._config = GenomeMCPConfig(**config_data)
        return self._config

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Returns:
            Dict[str, Any]: Configuration from environment variables
        """
        config = {}

        # Map environment variables to config keys
        env_mappings = {
            "APP_NAME": "app_name",
            "VERSION": "version",
            "DEBUG": "debug",
            "ENABLE_NCBI": "enable_ncbi",
            "ENABLE_ENSEMBL": "enable_ensembl",
            "ENABLE_CACHING": "enable_caching",
            "ENABLE_RATE_LIMITING": "enable_rate_limiting",
            "LOG_LEVEL": "logging.level",
            "LOG_FILE": "logging.file_path",
            "SERVER_HOST": "server.host",
            "SERVER_PORT": "server.port",
            "CACHE_ENABLED": "cache.enabled",
            "CACHE_TTL": "cache.ttl",
            "CACHE_MAX_SIZE": "cache.max_size",
            "RATE_LIMIT_ENABLED": "rate_limit.enabled",
            "RATE_LIMIT_RPM": "rate_limit.requests_per_minute",
            "RATE_LIMIT_RPH": "rate_limit.requests_per_hour",
            "API_TIMEOUT": "api.timeout",
            "API_RETRY_ATTEMPTS": "api.retry_attempts",
            "NCBI_API_KEY": "data_sources.ncbi.api_key",
            "NCBI_BASE_URL": "data_sources.ncbi.base_url",
            "ENSEMBL_BASE_URL": "data_sources.ensembl.base_url",
        }

        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(f"{self._env_prefix}{env_var}")
            if env_value is not None:
                # Convert string values to appropriate types
                value = self._convert_env_value(env_value)
                self._set_nested_value(config, config_key, value)

        return config

    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type.

        Args:
            value: Environment variable value as string

        Returns:
            Converted value
        """
        # Boolean conversion
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        elif value.lower() in ("false", "0", "no", "off"):
            return False

        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass

        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested value in configuration dictionary.

        Args:
            config: Configuration dictionary
            key: Dot-separated key (e.g., 'cache.enabled')
            value: Value to set
        """
        keys = key.split(".")
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def get_config(self) -> GenomeMCPConfig:
        """Get current configuration.

        Returns:
            GenomeMCPConfig: Current configuration

        Raises:
            ValueError: If configuration has not been loaded
        """
        if self._config is None:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._config

    def save_config(self, config: Optional[GenomeMCPConfig] = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save. If None, uses current config.

        Raises:
            ValueError: If no config file was specified or config not loaded
        """
        if not self.config_file:
            raise ValueError("No config file specified for saving")

        if config is None:
            config = self.get_config()

        try:
            # Create directory if it doesn't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dictionary and save
            config_dict = config.model_dump()

            with open(self.config_file, "w", encoding="utf-8") as f:
                if self.config_file.suffix.lower() in [".yaml", ".yml"]:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                elif self.config_file.suffix.lower() == ".json":
                    json.dump(config_dict, f, indent=2)
                else:
                    raise ValueError(
                        f"Unsupported config file format: {self.config_file.suffix}"
                    )

        except Exception as e:
            raise ValueError(f"Error saving configuration file: {e}")

    def reload_config(self) -> GenomeMCPConfig:
        """Reload configuration from file and environment.

        Returns:
            GenomeMCPConfig: Reloaded configuration
        """
        return self.load_config()

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value.

        Args:
            key: Dot-separated key (e.g., 'cache.enabled')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        config = self.get_config()
        config_dict = config.model_dump()

        keys = key.split(".")
        current = config_dict

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def set_value(self, key: str, value: Any) -> None:
        """Set a specific configuration value.

        Args:
            key: Dot-separated key (e.g., 'cache.enabled')
            value: Value to set
        """
        config_dict = self.get_config().dict()
        self._set_nested_value(config_dict, key, value)

        # Recreate config object
        self._config = GenomeMCPConfig(**config_dict)


def get_config(config_file: Optional[Union[str, Path]] = None) -> GenomeMCPConfig:
    """Convenience function to get configuration.

    Args:
        config_file: Path to configuration file

    Returns:
        GenomeMCPConfig: Loaded configuration
    """
    manager = ConfigManager(config_file)
    return manager.load_config()


def create_default_config(config_file: Union[str, Path]) -> None:
    """Create a default configuration file.

    Args:
        config_file: Path where to create the configuration file
    """
    config = GenomeMCPConfig()
    manager = ConfigManager(config_file)
    manager.save_config(config)
