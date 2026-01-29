"""
Modular document conversion system
Uses plugin architecture for easy extensibility

DEPRECATED FUNCTIONS (kept for backward compatibility):
- Old standalone functions still work but use new converters internally
"""
from backend.app.utils.base_converter import ConversionError, registry
from backend.app.utils import converters  # Auto-registers all converters

# Export ConversionError for backward compatibility
__all__ = ['ConversionError', 'convert_file', 'get_supported_conversions']


def convert_file(input_path: str, output_path: str, source_format: str, target_format: str) -> bool:
    """
    Main conversion function - uses modular converter system
    
    Args:
        input_path: Path to input file
        output_path: Path to output file
        source_format: Source format (e.g., 'png', 'pdf', 'docx')
        target_format: Target format (e.g., 'pdf', 'png', 'txt')
    
    Returns:
        bool: True if conversion successful
    
    Raises:
        ConversionError: If conversion fails or format not supported
    """
    # Normalize formats
    source = source_format.lower().replace('.', '')
    target = target_format.lower().replace('.', '')
    
    # Get appropriate converter from registry
    converter = registry.get_converter(source, target)
    
    # Perform conversion
    return converter.convert(input_path, output_path)


def get_supported_conversions() -> dict:
    """
    Return dictionary of supported conversions from registry
    Dynamically generated from registered converters
    """
    return registry.get_all_conversions()
