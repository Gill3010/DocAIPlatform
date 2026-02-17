"""
Converters Package - Auto-discovery and registration of document converters.

Converters are discovered from all modules in this package (except __init__).
To add a new converter: create a class inheriting from BaseConverter in any
*_converters.py module and it will be registered on import.
"""
import importlib
import pkgutil
from typing import List, Type

from app.utils.base_converter import BaseConverter, registry


def _get_converter_module_paths() -> List[str]:
    """Return full module paths for all converter modules in this package."""
    pkg = importlib.import_module("app.utils.converters")
    prefix = pkg.__name__ + "."
    return [prefix + name for _, name, _ in pkgutil.iter_modules(pkg.__path__) if not name.startswith("_")]


def _discover_converter_classes(module_path: str) -> List[Type[BaseConverter]]:
    """Import module and return list of BaseConverter subclasses (excluding BaseConverter itself)."""
    converters: List[Type[BaseConverter]] = []
    try:
        module = importlib.import_module(module_path)
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseConverter)
                and obj is not BaseConverter
            ):
                converters.append(obj)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Could not load converters from %s: %s", module_path, e)
    return converters


def register_all_converters() -> None:
    """Discover and register all available converters from converter modules."""
    for module_path in _get_converter_module_paths():
        for converter_cls in _discover_converter_classes(module_path):
            registry.register(converter_cls())


# Auto-register on import
register_all_converters()

__all__ = ["register_all_converters", "registry"]
