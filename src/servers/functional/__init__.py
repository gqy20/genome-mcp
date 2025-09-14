"""
Functional Genomics Servers module.

This module contains MCP server implementations for functional genomics databases.
"""

from .go import GOntologyServer
from .kegg import KEGGServer

__all__ = ["GOntologyServer", "KEGGServer"]