"""
Text and Document Conversion Converters
Handles: TXT ↔ DOCX, PDF ↔ TXT
"""
from pypdf import PdfReader
from docx import Document
from typing import List

from backend.app.utils.base_converter import BaseConverter, ConversionError


class TextToDocxConverter(BaseConverter):
    """Convert plain text to DOCX"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['txt']
    
    @property
    def target_formats(self) -> List[str]:
        return ['docx']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """Convert text file to DOCX"""
        try:
            self.ensure_directory(output_path)
            
            # Read text file
            with open(input_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            # Create DOCX
            doc = Document()
            
            # Add paragraphs
            for paragraph in text_content.split('\n\n'):
                if paragraph.strip():
                    doc.add_paragraph(paragraph.strip())
            
            doc.save(output_path)
            return True
        except Exception as e:
            raise ConversionError(f"Text to DOCX conversion failed: {str(e)}")


class DocxToTextConverter(BaseConverter):
    """Convert DOCX to plain text"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['docx']
    
    @property
    def target_formats(self) -> List[str]:
        return ['txt']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """Convert DOCX to text file"""
        try:
            self.ensure_directory(output_path)
            
            doc = Document(input_path)
            
            # Extract all text
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            
            # Write to text file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(full_text))
            
            return True
        except Exception as e:
            raise ConversionError(f"DOCX to text conversion failed: {str(e)}")


class PDFToTextConverter(BaseConverter):
    """Extract text from PDF"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['pdf']
    
    @property
    def target_formats(self) -> List[str]:
        return ['txt']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """Extract text from PDF"""
        try:
            self.ensure_directory(output_path)
            
            reader = PdfReader(input_path)
            
            # Extract text from all pages
            full_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
            
            # Write to text file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(full_text))
            
            return True
        except Exception as e:
            raise ConversionError(f"PDF to text conversion failed: {str(e)}")
