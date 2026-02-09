"""Patrón Strategy para herramientas PDF: base, estrategias y registro."""
from app.utils.pdf_tool_strategies.base import PDFToolStrategy, ToolResult
from app.utils.pdf_tool_strategies.strategies import REGISTRY

__all__ = ["PDFToolStrategy", "ToolResult", "REGISTRY"]
