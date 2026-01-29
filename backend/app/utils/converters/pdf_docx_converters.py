"""
PDF ↔ DOCX Conversion Converters
Bidirectional conversion between PDF and Word documents
"""
from pypdf import PdfReader
from docx import Document
from docx.shared import Pt, Inches
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from typing import List
import io

from backend.app.utils.base_converter import BaseConverter, ConversionError


class PDFToDocxConverter(BaseConverter):
    """Convert PDF to DOCX by extracting text and formatting"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['pdf']
    
    @property
    def target_formats(self) -> List[str]:
        return ['docx']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert PDF to DOCX
        Extracts text and creates a formatted Word document
        """
        try:
            self.ensure_directory(output_path)
            
            # Read PDF
            reader = PdfReader(input_path)
            
            if len(reader.pages) == 0:
                raise ConversionError("PDF has no pages")
            
            # Create new Word document
            doc = Document()
            
            # Set default style
            style = doc.styles['Normal']
            font = style.font
            font.name = 'Arial'
            font.size = Pt(11)
            
            # Extract text from each page
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                
                if text and text.strip():
                    # Add page number header if multiple pages
                    if len(reader.pages) > 1:
                        doc.add_heading(f'Página {page_num}', level=2)
                    
                    # Add paragraphs
                    paragraphs = text.split('\n\n')
                    for para_text in paragraphs:
                        if para_text.strip():
                            doc.add_paragraph(para_text.strip())
                    
                    # Add page break if not last page
                    if page_num < len(reader.pages):
                        doc.add_page_break()
            
            # Save document
            doc.save(output_path)
            return True
            
        except Exception as e:
            raise ConversionError(f"PDF to DOCX conversion failed: {str(e)}")


class DocxToPDFConverter(BaseConverter):
    """Convert DOCX to PDF using ReportLab"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['docx']
    
    @property
    def target_formats(self) -> List[str]:
        return ['pdf']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert DOCX to PDF
        Extracts content and creates a formatted PDF
        """
        try:
            self.ensure_directory(output_path)
            
            # Read DOCX
            doc = Document(input_path)
            
            # Create PDF
            pdf = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Get styles
            styles = getSampleStyleSheet()
            normal_style = styles['Normal']
            heading_style = styles['Heading1']
            
            # Extract content from DOCX
            for para in doc.paragraphs:
                if para.text.strip():
                    # Determine if it's a heading (basic heuristic)
                    if para.style.name.startswith('Heading'):
                        p = Paragraph(para.text, heading_style)
                    else:
                        p = Paragraph(para.text, normal_style)
                    
                    elements.append(p)
                    elements.append(Spacer(1, 12))
            
            # Build PDF
            pdf.build(elements)
            return True
            
        except Exception as e:
            raise ConversionError(f"DOCX to PDF conversion failed: {str(e)}")
