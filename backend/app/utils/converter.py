"""
Modular document conversion system
Uses plugin architecture for easy extensibility

DEPRECATED FUNCTIONS (kept for backward compatibility):
- Old standalone functions still work but use new converters internally
"""
import os
import tempfile
from app.utils.base_converter import ConversionError, registry
from app.utils import converters  # Auto-registers all converters

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
    source = source_format.lower().replace('.', '')
    target = target_format.lower().replace('.', '')
    effective_input = input_path
    temp_ocr_path = None

    if source == 'pdf':
        from app.core.config import settings
        if getattr(settings, 'USE_OCR_FOR_SCANNED_PDF', False):
            from app.utils.pdf_ocr import is_pdf_scanned, add_ocr_to_pdf
            if is_pdf_scanned(input_path):
                try:
                    fd, temp_ocr_path = tempfile.mkstemp(suffix='.pdf')
                    os.close(fd)
                    if add_ocr_to_pdf(input_path, temp_ocr_path):
                        effective_input = temp_ocr_path
                except Exception:
                    pass

    try:
        converter = registry.get_converter(source, target)
        return converter.convert(effective_input, output_path)
    finally:
        if temp_ocr_path and os.path.exists(temp_ocr_path):
            try:
                os.unlink(temp_ocr_path)
            except OSError:
                pass


def get_supported_conversions() -> dict:
    """
    Return dictionary of supported conversions from registry
    Dynamically generated from registered converters
    """
    return registry.get_all_conversions()
