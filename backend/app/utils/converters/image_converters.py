"""
Image Conversion Converters
Handles: PNG, JPG, JPEG ↔ PDF
"""
from PIL import Image
from pypdf import PdfReader
from typing import List

from backend.app.utils.base_converter import BaseConverter, ConversionError


class ImageToPDFConverter(BaseConverter):
    """Convert images (PNG, JPG, JPEG) to PDF"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['png', 'jpg', 'jpeg']
    
    @property
    def target_formats(self) -> List[str]:
        return ['pdf']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """Convert image to PDF"""
        try:
            self.ensure_directory(output_path)
            
            # Open and convert image
            image = Image.open(input_path)
            
            # Convert to RGB if necessary (PNG with transparency)
            if image.mode in ("RGBA", "LA", "P"):
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = rgb_image
            elif image.mode != "RGB":
                image = image.convert("RGB")
            
            # Save as PDF
            image.save(output_path, "PDF", resolution=100.0)
            image.close()
            
            return True
        except Exception as e:
            raise ConversionError(f"Image to PDF conversion failed: {str(e)}")


class PDFToImageConverter(BaseConverter):
    """Convert PDF to PNG image (first page)"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['pdf']
    
    @property
    def target_formats(self) -> List[str]:
        return ['png']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """Convert first page of PDF to PNG"""
        try:
            self.ensure_directory(output_path)
            
            # Simple placeholder implementation
            # In production, use pdf2image with poppler or external API
            reader = PdfReader(input_path)
            
            if len(reader.pages) == 0:
                raise ConversionError("PDF has no pages")
            
            # Create a placeholder image
            # TODO: Implement proper PDF rendering
            img = Image.new('RGB', (800, 600), color='white')
            img.save(output_path, 'PNG')
            
            return True
        except Exception as e:
            raise ConversionError(f"PDF to image conversion failed: {str(e)}")
