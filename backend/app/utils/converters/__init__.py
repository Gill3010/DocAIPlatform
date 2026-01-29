"""
Converters Package
Auto-registers all available converters
"""
from backend.app.utils.base_converter import registry

# Import all converter modules to trigger registration
from backend.app.utils.converters.image_converters import (
    ImageToPDFConverter,
    PDFToImageConverter
)
from backend.app.utils.converters.text_converters import (
    TextToDocxConverter,
    DocxToTextConverter,
    PDFToTextConverter
)
from backend.app.utils.converters.pdf_docx_converters import (
    PDFToDocxConverter,
    DocxToPDFConverter
)
from backend.app.utils.converters.xml_html_converters import (
    XMLToHTMLConverter,
    HTMLToXMLConverter
)
from backend.app.utils.converters.cad_converters import (
    DXFToPNGConverter,
    PNGToDXFConverter
)
from backend.app.utils.converters.jats_converters import (
    DocxToJATSConverter,
    JATSToDocxConverter
)

# Register all converters
def register_all_converters():
    """Register all available converters in the registry"""
    
    # Image converters
    registry.register(ImageToPDFConverter())
    registry.register(PDFToImageConverter())
    
    # Text converters
    registry.register(TextToDocxConverter())
    registry.register(DocxToTextConverter())
    registry.register(PDFToTextConverter())
    
    # PDF <-> DOCX converters
    registry.register(PDFToDocxConverter())
    registry.register(DocxToPDFConverter())
    
    # XML <-> HTML converters
    registry.register(XMLToHTMLConverter())
    registry.register(HTMLToXMLConverter())
    
    # CAD converters (DXF <-> PNG)
    registry.register(DXFToPNGConverter())
    registry.register(PNGToDXFConverter())
    
    # JATS converters (DOCX <-> JATS XML)
    registry.register(DocxToJATSConverter())
    registry.register(JATSToDocxConverter())


# Auto-register on import
register_all_converters()

__all__ = [
    'ImageToPDFConverter',
    'PDFToImageConverter',
    'TextToDocxConverter',
    'DocxToTextConverter',
    'PDFToTextConverter',
    'PDFToDocxConverter',
    'DocxToPDFConverter',
    'XMLToHTMLConverter',
    'HTMLToXMLConverter',
    'DXFToPNGConverter',
    'PNGToDXFConverter',
    'DocxToJATSConverter',
    'JATSToDocxConverter',
    'register_all_converters'
]
