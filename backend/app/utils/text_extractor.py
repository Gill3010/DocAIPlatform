from pathlib import Path
import docx
import fitz # PyMuPDF
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(file_path: Path) -> str:
    """Extrae el contenido de texto de varios formatos de archivo."""
    if not file_path.exists():
        return ""

    suffix = file_path.suffix.lower()
    
    try:
        if suffix == ".docx":
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        
        elif suffix == ".pdf":
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
            
        elif suffix in [".txt", ".html", ".htm", ".xml"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        
        # Fallback para otros formatos: intentar leer como texto
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
                
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return f"Error al extraer contenido: {str(e)}"
