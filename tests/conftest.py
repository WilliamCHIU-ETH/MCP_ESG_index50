"""Shared pytest setup for the Claude ESG MCP server.

Keep repository-wide fixtures and import path setup here. Unit tests should mock
external dependencies; integration and smoke tests opt into broader boundaries
with pytest markers.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
