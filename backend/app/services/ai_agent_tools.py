"""
Definición de herramientas disponibles para el AI Agent (conversiones y PDF tools).
Usado por ai_agent_service para construir el system prompt con Smart Links.
"""

# Conversiones: source -> [(target, desc)]
# Formato URL: /convert?from={source}&to={target}
CONVERSION_TOOLS = [
    ("pdf", "docx", "Convierte PDF a Word editable"),
    ("pdf", "xlsx", "Extrae tablas de PDF a Excel"),
    ("pdf", "pptx", "Convierte PDF a PowerPoint"),
    ("pdf", "txt", "Extrae texto plano de PDF"),
    ("pdf", "png", "Convierte páginas PDF a imágenes PNG"),
    ("pdf", "jpg", "Convierte páginas PDF a imágenes JPG"),
    ("docx", "pdf", "Convierte Word a PDF"),
    ("docx", "txt", "Convierte Word a texto plano"),
    ("docx", "xml", "Convierte Word a JATS XML (publicación académica)"),
    ("xlsx", "pdf", "Convierte Excel a PDF"),
    ("pptx", "pdf", "Convierte PowerPoint a PDF"),
    ("txt", "docx", "Convierte TXT a Word"),
    ("png", "pdf", "Convierte imagen PNG a PDF"),
    ("jpg", "pdf", "Convierte imagen JPG a PDF"),
    ("jpeg", "pdf", "Convierte imagen JPEG a PDF"),
    ("xml", "html", "Convierte XML a HTML"),
    ("xml", "docx", "Convierte JATS XML a Word"),
    ("html", "xml", "Convierte HTML a XML"),
]

# Herramientas PDF: id -> (nombre, descripción)
# Formato URL: /pdf-tools?tool={id}
PDF_TOOLS = [
    ("unir-pdf", "Unir PDF", "Combina múltiples archivos PDF en un solo documento"),
    ("comprimir-pdf", "Comprimir PDF", "Reduce el tamaño del archivo PDF sin perder calidad"),
    ("dividir-pdf", "Dividir PDF", "Separa un PDF en múltiples archivos por páginas"),
    ("rotar-pdf", "Rotar PDF", "Gira las páginas del PDF (90°, 180°, 270°)"),
    ("proteger-pdf", "Proteger PDF", "Agrega contraseña y permisos de seguridad"),
    ("desbloquear-pdf", "Desbloquear PDF", "Elimina la protección con contraseña"),
    ("marca-agua", "Marca de agua", "Añade marca de agua personalizada"),
    ("pdf-a", "PDF → PDF/A", "Convierte a formato PDF/A para archivo de largo plazo"),
    ("ordenar-pdf", "Ordenar PDF", "Reorganiza el orden de las páginas"),
    ("recortar-pdf", "Recortar PDF", "Recorta márgenes o áreas específicas"),
    ("numeros-pagina", "Números de página", "Agrega numeración automática"),
    ("comparar-pdf", "Comparar PDF", "Compara dos versiones y resalta diferencias"),
    ("reparar-pdf", "Reparar PDF", "Intenta reparar archivos PDF corruptos"),
    ("editar-pdf", "Editar PDF", "Edita texto e imágenes dentro del PDF"),
    ("firmar-pdf", "Firmar PDF", "Añade firma digital o manuscrita"),
    ("ocr-pdf", "OCR PDF", "Reconoce texto de PDFs escaneados"),
    ("escanear-pdf", "Escanear a PDF", "Convierte documentos escaneados en PDF"),
    ("censurar-pdf", "Censurar PDF", "Oculta o elimina información sensible"),
]


def build_tools_section() -> str:
    """Construye la sección de herramientas para el system prompt."""
    lines = []
    lines.append("## HERRAMIENTAS DISPONIBLES")
    lines.append("")
    lines.append("### Conversiones de formato")
    lines.append("Para cada conversión, la URL es: /convert?from={origen}&to={destino}")
    for src, tgt, desc in CONVERSION_TOOLS:
        lines.append(f"- {src} → {tgt}: {desc}. URL: /convert?from={src}&to={tgt}")
    lines.append("")
    lines.append("### Herramientas PDF")
    lines.append("Para cada herramienta, la URL es: /pdf-tools?tool={id}")
    for tool_id, name, desc in PDF_TOOLS:
        lines.append(f"- {name} ({tool_id}): {desc}. URL: /pdf-tools?tool={tool_id}")
    lines.append("")
    lines.append("### Otras páginas útiles")
    lines.append("- Dashboard: /dashboard")
    lines.append("- Historial de conversiones: /history")
    lines.append("- Mis documentos: /documents")
    lines.append("- Formatear manuscrito (JATS): /format-manuscript")
    lines.append("- Precios y planes: /pricing")
    return "\n".join(lines)
