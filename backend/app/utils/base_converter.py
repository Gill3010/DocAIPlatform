"""
Base Converter Class - Plugin Architecture for Document Conversions
Allows easy extension of conversion capabilities
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple


class ConversionError(Exception):
    """Custom exception for conversion errors"""
    pass


class BaseConverter(ABC):
    """
    Abstract base class for all document converters
    
    Each converter must implement:
    - source_formats: List of supported input formats
    - target_formats: List of supported output formats
    - convert(): Actual conversion logic
    """
    
    @property
    @abstractmethod
    def source_formats(self) -> List[str]:
        """Return list of supported source formats (e.g., ['pdf', 'docx'])"""
        pass
    
    @property
    @abstractmethod
    def target_formats(self) -> List[str]:
        """Return list of supported target formats (e.g., ['png', 'txt'])"""
        pass
    
    @abstractmethod
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Perform the actual conversion
        
        Args:
            input_path: Path to source file
            output_path: Path to output file
            
        Returns:
            bool: True if successful
            
        Raises:
            ConversionError: If conversion fails
        """
        pass
    
    @staticmethod
    def ensure_directory(file_path: str):
        """Ensure the directory for the file exists"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    def supports_conversion(self, source_format: str, target_format: str) -> bool:
        """
        Check if this converter supports the given conversion
        
        Args:
            source_format: Source format (e.g., 'pdf')
            target_format: Target format (e.g., 'docx')
            
        Returns:
            bool: True if conversion is supported
        """
        return (source_format.lower() in self.source_formats and 
                target_format.lower() in self.target_formats)
    
    def get_supported_conversions(self) -> List[Tuple[str, str]]:
        """
        Get all supported conversion pairs for this converter
        
        Returns:
            List of (source, target) tuples
        """
        conversions = []
        for source in self.source_formats:
            for target in self.target_formats:
                conversions.append((source, target))
        return conversions


class ConverterRegistry:
    """
    Registry for managing all available converters
    Automatically discovers and registers converters
    """
    
    def __init__(self):
        self._converters: List[BaseConverter] = []
    
    def register(self, converter: BaseConverter):
        """Register a new converter"""
        self._converters.append(converter)
    
    def get_converter(self, source_format: str, target_format: str) -> BaseConverter:
        """
        Find appropriate converter for the given formats
        
        Args:
            source_format: Source format
            target_format: Target format
            
        Returns:
            BaseConverter instance
            
        Raises:
            ConversionError: If no converter found
        """
        source = source_format.lower().replace('.', '')
        target = target_format.lower().replace('.', '')
        
        for converter in self._converters:
            if converter.supports_conversion(source, target):
                return converter
        
        raise ConversionError(
            f"No converter found for {source_format} → {target_format}. "
            f"Available conversions: {self.get_all_conversions()}"
        )
    
    def get_all_conversions(self) -> dict:
        """
        Get all available conversions organized by source format
        
        Returns:
            Dict mapping source formats to list of target formats
        """
        conversions = {}
        
        for converter in self._converters:
            for source, target in converter.get_supported_conversions():
                if source not in conversions:
                    conversions[source] = []
                if target not in conversions[source]:
                    conversions[source].append(target)
        
        return conversions
    
    def get_target_formats(self, source_format: str) -> List[str]:
        """
        Get available target formats for a given source format
        
        Args:
            source_format: Source format
            
        Returns:
            List of available target formats
        """
        all_conversions = self.get_all_conversions()
        return all_conversions.get(source_format.lower(), [])


# Global registry instance
registry = ConverterRegistry()
