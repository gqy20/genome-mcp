# Genome MCP - Model Context Protocol Server for Genomic Data

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Publish](https://github.com/gqy20/genome-mcp/workflows/Publish/badge.svg)](https://github.com/gqy20/genome-mcp/actions/workflows/publish.yml)
[![Code Quality](https://github.com/gqy20/genome-mcp/workflows/Quality/badge.svg)](https://github.com/gqy20/genome-mcp/actions/workflows/quality.yml)
[![PyPI version](https://badge.fury.io/py/genome-mcp.svg)](https://badge.fury.io/py/genome-mcp)

A Model Context Protocol (MCP) server that provides unified access to genomic databases through a standardized API interface. Built with async architecture and designed for AI-tool integration using the FastMCP framework.

## Features

- **MCP Server Architecture**: Built on Model Context Protocol for seamless AI-tool integration
- **NCBI Database Integration**: Full access to NCBI Gene database via EUtils API
- **Async Performance**: High-performance async/await architecture
- **Rate Limiting & Caching**: Built-in request optimization and response caching
- **Type Safety**: Full type hints with Pydantic models
- **FastMCP Framework**: Built on FastMCP for standardized MCP protocol implementation
- **Modern Python**: Uses uv for dependency management and modern packaging

## Installation

### Using uv (Recommended)

```bash
# Install with uv
uv add genome-mcp

# Or run directly without installation
uv run genome-mcp --help
```

### Using pip

```bash
pip install genome-mcp
```

## Quick Start

### Running as MCP Server

```bash
# Run as stdio MCP server (for AI tools like Claude Desktop)
genome-mcp --transport stdio

# Run as SSE server (for web applications)
genome-mcp --transport sse --host localhost --port 8080

# Run as Streamable HTTP server (for API integration)
genome-mcp --transport streamable-http --host localhost --port 8080
```

### Python API

```python
import asyncio
from main import get_gene_info, search_genes

async def main():
    # Get gene information
    gene_info = await get_gene_info("7157")  # TP53
    print(f"Gene: {gene_info['info']['name']}")
    print(f"Description: {gene_info['info']['description']}")
    
    # Search for genes
    search_results = await search_genes("cancer", species="human")
    print(f"Found {len(search_results['results'])} genes")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

### Environment Variables

```bash
# NCBI API key (optional but recommended for higher rate limits)
export NCBI_API_KEY="your_ncbi_api_key"

# Email for NCBI API (required for some operations)
export NCBI_EMAIL="your_email@example.com"
```

### Project Configuration

The project includes a comprehensive configuration file (`project_config.json`) that defines:

- Server settings and capabilities
- Rate limiting and caching configuration
- Logging and monitoring settings
- Development and deployment options

### Configuration File

Create a configuration file at `~/.genome_mcp/config.json`:

```json
{
  "servers": {
    "ncbi_gene": {
      "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
      "rate_limit": {
        "requests_per_second": 3,
        "burst_limit": 10
      },
      "cache": {
        "enabled": true,
        "ttl": 3600
      }
    }
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/genome-mcp.git
cd genome-mcp

# Install with uv
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_ncbi_gene_server.py
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Sort imports
uv run isort src/ tests/

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/ tests/
```

## Project Structure

```
genome-mcp/
  main.py                  # FastMCP server entry point
  src/                     # Source code
    servers/               # MCP server implementations
      base.py            # Base MCP server class
      ncbi/              # NCBI server implementations
        gene.py         # NCBI Gene server
    configuration.py       # Configuration management
    http_utils/            # HTTP utilities
    data/                  # Data processing
    core/                  # Core utilities
    exceptions.py          # Exception definitions
  tests/                   # Test code
  docs/                    # Documentation
  examples/               # Example code
  .github/                # GitHub Actions workflows
  project_config.json      # Project configuration
```

## Architecture

### FastMCP Server Architecture

- **FastMCP Framework**: Built on the FastMCP framework for MCP protocol implementation
- **NCBIGeneServer**: Implementation for NCBI Gene database access
- **MCP Tools**: Expose genomic data functions as MCP tools
- **Async Design**: Full async/await support for high performance
- **Rate Limiting**: Built-in request rate limiting with Token Bucket algorithm
- **Caching**: Optional response caching to improve performance
- **Error Handling**: Comprehensive error handling and logging

### Key Components

- **main.py**: FastMCP server entry point with tool decorators
- **NCBIGeneServer**: NCBI Gene database access implementation
- **MCP Transport**: Support for stdio, SSE, and Streamable HTTP transports
- **Request Execution**: Support for single and batch requests
- **Configuration Management**: JSON-based configuration system

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use Genome MCP in your research, please cite:

```bibtex
@software{genome_mcp,
  title={Genome MCP: Model Context Protocol Server for Genomic Data},
  author={gqy20},
  year={2025},
  url={https://github.com/gqy20/genome-mcp}
}
```

## Support

- **Documentation**: [https://github.com/gqy20/genome-mcp#readme](https://github.com/gqy20/genome-mcp#readme)
- **Issues**: [https://github.com/gqy20/genome-mcp/issues](https://github.com/gqy20/genome-mcp/issues)
- **Discussions**: [https://github.com/gqy20/genome-mcp/discussions](https://github.com/gqy20/genome-mcp/discussions)

## Acknowledgments

- [NCBI](https://www.ncbi.nlm.nih.gov/) for providing comprehensive genomic databases
- [Model Context Protocol](https://modelcontextprotocol.io/) for enabling AI-tool integration
- [FastMCP](https://github.com/gofastmcp/fastmcp) for the MCP framework implementation
- [uv](https://github.com/astral-sh/uv) for modern Python package management