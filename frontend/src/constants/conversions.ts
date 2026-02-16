import {
    FileText,
    File,
    Image,
    Globe,
    Ruler,
    GraduationCap,
    Presentation,
    Table,
    Merge,
    Split,
    Shrink,
    PenLine,
    PenTool,
    Droplets,
    RotateCw,
    LockOpen,
    Lock,
    ArrowUpDown,
    FileCheck,
    Wrench,
    Hash,
    Scan,
    ScanSearch,
    GitCompare,
    Eraser,
    Crop,
    type LucideIcon
} from 'lucide-react';

/**
 * Fuente única de verdad para conversiones.
 * Usado por Convert (selector de formatos) y Dashboard (cards por tipo).
 */

export const SOURCE_LABELS: Record<string, string> = {
    docx: 'Word',
    pdf: 'PDF',
    txt: 'TXT',
    xml: 'XML',
    html: 'HTML',
    htm: 'HTML',
    png: 'PNG',
    jpg: 'JPG',
    jpeg: 'JPEG',
    dxf: 'DXF',
    dwg: 'DWG',
    pptx: 'PowerPoint',
    xlsx: 'Excel'
};

/** Etiquetas cortas para formato destino (hints en página Convertir). */
export const TARGET_LABELS: Record<string, string> = {
    pdf: 'PDF',
    docx: 'Word',
    txt: 'TXT',
    xml: 'XML',
    html: 'HTML',
    png: 'PNG',
    jpg: 'JPG',
    jpeg: 'JPEG',
    dxf: 'DXF',
    dwg: 'DWG',
    pptx: 'PowerPoint',
    xlsx: 'Excel'
};

export const CONVERSION_MAP: Record<string, Array<{ id: string; name: string; icon: LucideIcon }>> = {
    png: [
        { id: 'pdf', name: 'PDF', icon: FileText },
        { id: 'dxf', name: 'DXF', icon: Ruler },
        { id: 'dwg', name: 'DWG', icon: Ruler }
    ],
    jpg: [
        { id: 'pdf', name: 'PDF', icon: FileText },
        { id: 'dxf', name: 'DXF', icon: Ruler },
        { id: 'dwg', name: 'DWG', icon: Ruler }
    ],
    jpeg: [
        { id: 'pdf', name: 'PDF', icon: FileText },
        { id: 'dxf', name: 'DXF', icon: Ruler },
        { id: 'dwg', name: 'DWG', icon: Ruler }
    ],
    pdf: [
        { id: 'docx', name: 'Word', icon: File },
        { id: 'png', name: 'PNG', icon: Image },
        { id: 'jpg', name: 'JPG', icon: Image },
        { id: 'jpeg', name: 'JPEG', icon: Image },
        { id: 'txt', name: 'TXT', icon: FileText },
        { id: 'pptx', name: 'PowerPoint', icon: Presentation },
        { id: 'xlsx', name: 'Excel', icon: Table }
    ],
    txt: [
        { id: 'docx', name: 'Word', icon: File }
    ],
    docx: [
        { id: 'pdf', name: 'PDF', icon: FileText },
        { id: 'txt', name: 'TXT', icon: FileText },
        { id: 'xml', name: 'XML', icon: GraduationCap }
    ],
    xml: [
        { id: 'html', name: 'HTML', icon: Globe },
        { id: 'docx', name: 'Word', icon: File }
    ],
    html: [
        { id: 'xml', name: 'XML', icon: FileText }
    ],
    htm: [
        { id: 'xml', name: 'XML', icon: FileText }
    ],
    dxf: [
        { id: 'png', name: 'PNG', icon: Image },
        { id: 'jpg', name: 'JPG', icon: Image },
        { id: 'jpeg', name: 'JPEG', icon: Image }
    ],
    dwg: [
        { id: 'png', name: 'PNG', icon: Image },
        { id: 'jpg', name: 'JPG', icon: Image },
        { id: 'jpeg', name: 'JPEG', icon: Image }
    ],
    pptx: [
        { id: 'pdf', name: 'PDF', icon: FileText }
    ],
    xlsx: [
        { id: 'pdf', name: 'PDF', icon: FileText }
    ]
};

export type ConversionCategory = 'document' | 'image' | 'web';

export const CATEGORY_BY_SOURCE: Record<string, ConversionCategory> = {
    docx: 'document',
    pdf: 'document',
    txt: 'document',
    xml: 'web',
    html: 'web',
    htm: 'web',
    png: 'image',
    jpg: 'image',
    jpeg: 'image',
    dxf: 'image',
    dwg: 'image',
    pptx: 'document',
    xlsx: 'document'
};

export interface DashboardConversionType {
    id: string;
    sourceKey: string;
    sourceLabel: string;
    targetId: string;
    targetLabel: string;
    category: ConversionCategory;
    icon: LucideIcon;
    /** Primer formato de origen para link (ej. docx, pdf). Para imagen unificado como "png". */
    primarySourceFormat: string;
    /** Tooltip informativo que explica qué hace esta conversión */
    tooltip?: string;
}

/** Formatos de imagen: cada uno tiene su propia card explícita. */
const IMAGE_SOURCES = ['png', 'jpg', 'jpeg'];

function alreadyEmitted(
    emitted: Set<string>,
    sourceKey: string,
    targetId: string
): boolean {
    const key = sourceKey + '->' + targetId;
    if (emitted.has(key)) return true;
    emitted.add(key);
    return false;
}

/**
 * Tooltips informativos para cada conversión
 */
export const CONVERSION_TOOLTIPS: Record<string, string> = {
    'pdf-docx': 'Convierte archivos PDF en documentos Word editables, manteniendo el formato original',
    'docx-pdf': 'Convierte documentos Word en PDF listos para compartir o imprimir',
    'xlsx-pdf': 'Convierte hojas de cálculo Excel en documentos PDF para fácil distribución',
    'pptx-pdf': 'Convierte presentaciones PowerPoint en documentos PDF portátiles',
    'pdf-xlsx': 'Extrae tablas y datos de PDF a formato Excel editable',
    'pdf-pptx': 'Convierte páginas PDF en diapositivas PowerPoint editables',
    'pdf-txt': 'Extrae TXT de archivos PDF para análisis o edición simple',
    'docx-txt': 'Convierte documentos Word a TXT sin formato',
    'txt-docx': 'Convierte archivos TXT en documentos Word con formato básico',
    'docx-xml': 'Convierte documentos Word al formato JATS XML para publicación académica',
    'png-pdf': 'Convierte imágenes PNG en documentos PDF de alta calidad',
    'jpg-pdf': 'Convierte imágenes JPG en documentos PDF de alta calidad',
    'jpeg-pdf': 'Convierte imágenes JPEG en documentos PDF de alta calidad',
    'pdf-png': 'Convierte páginas PDF en imágenes PNG de alta resolución',
    'pdf-jpg': 'Convierte páginas PDF en imágenes JPG',
    'pdf-jpeg': 'Convierte páginas PDF en imágenes JPEG',
    'png-dxf': 'Convierte imágenes PNG a formato DXF para software CAD',
    'png-dwg': 'Convierte imágenes PNG a formato DWG (requiere ODA File Converter)',
    'jpg-dxf': 'Convierte imágenes JPG a formato DXF para software CAD',
    'jpg-dwg': 'Convierte imágenes JPG a formato DWG (requiere ODA File Converter)',
    'jpeg-dxf': 'Convierte imágenes JPEG a formato DXF para software CAD',
    'jpeg-dwg': 'Convierte imágenes JPEG a formato DWG (requiere ODA File Converter)',
    'dxf-png': 'Convierte dibujos técnicos DXF en imágenes PNG',
    'dxf-jpg': 'Convierte dibujos técnicos DXF en imágenes JPG',
    'dxf-jpeg': 'Convierte dibujos técnicos DXF en imágenes JPEG',
    'dwg-png': 'Convierte dibujos DWG en imágenes PNG (requiere ODA File Converter)',
    'dwg-jpg': 'Convierte dibujos DWG en imágenes JPG (requiere ODA File Converter)',
    'dwg-jpeg': 'Convierte dibujos DWG en imágenes JPEG (requiere ODA File Converter)',
    'xml-html': 'Convierte documentos XML en páginas HTML navegables',
    'html-xml': 'Convierte páginas HTML a formato XML estructurado',
    'xml-docx': 'Convierte archivos JATS XML en documentos Word editables'
};

/**
 * Orden óptimo de conversiones por categoría basado en popularidad de uso
 * Las conversiones más utilizadas aparecen primero dentro de cada categoría
 */
const CONVERSION_ORDER_BY_CATEGORY: Record<ConversionCategory, Array<{ source: string; target: string }>> = {
    document: [
        // Top tier - Más utilizadas globalmente
        { source: 'pdf', target: 'docx' },      // #1 PDF → Word
        { source: 'docx', target: 'pdf' },      // #2 Word → PDF
        { source: 'xlsx', target: 'pdf' },      // #3 Excel → PDF
        { source: 'pptx', target: 'pdf' },      // #4 PowerPoint → PDF
        { source: 'pdf', target: 'xlsx' },      // #5 PDF → Excel
        { source: 'pdf', target: 'pptx' },      // #6 PDF → PowerPoint
        // Mid tier - Conversiones de texto
        { source: 'pdf', target: 'txt' },       // #7 PDF → Texto
        { source: 'docx', target: 'txt' },      // #8 Word → Texto
        { source: 'txt', target: 'docx' }       // #9 Texto → Word
    ],
    image: [
        // Imagen → PDF
        { source: 'png', target: 'pdf' },
        { source: 'jpg', target: 'pdf' },
        { source: 'jpeg', target: 'pdf' },
        // PDF → Imagen
        { source: 'pdf', target: 'png' },
        { source: 'pdf', target: 'jpg' },
        { source: 'pdf', target: 'jpeg' },
        // Imagen → CAD
        { source: 'png', target: 'dxf' },
        { source: 'png', target: 'dwg' },
        { source: 'jpg', target: 'dxf' },
        { source: 'jpg', target: 'dwg' },
        { source: 'jpeg', target: 'dxf' },
        { source: 'jpeg', target: 'dwg' },
        // CAD → Imagen
        { source: 'dxf', target: 'png' },
        { source: 'dxf', target: 'jpg' },
        { source: 'dxf', target: 'jpeg' },
        { source: 'dwg', target: 'png' },
        { source: 'dwg', target: 'jpg' },
        { source: 'dwg', target: 'jpeg' },
    ],
    web: [
        { source: 'xml', target: 'html' },      // #1 XML → HTML
        { source: 'html', target: 'xml' },      // #2 HTML → XML
        { source: 'xml', target: 'docx' },      // #3 XML → Word
        { source: 'docx', target: 'xml' }       // #4 Word → XML (JATS)
    ]
};

/**
 * Lista de tipos de conversión para el dashboard.
 * Derivada de CONVERSION_MAP; sin duplicados (PNG/JPG/JPEG unificados como "Imagen").
 * Ordenada por popularidad dentro de cada categoría.
 */
export function getDashboardConversions(): DashboardConversionType[] {
    const emitted = new Set<string>();
    const result: DashboardConversionType[] = [];

    // Procesar conversiones en el orden definido por categoría
    (['document', 'image', 'web'] as ConversionCategory[]).forEach((category) => {
        const orderedPairs = CONVERSION_ORDER_BY_CATEGORY[category];
        
        orderedPairs.forEach(({ source: sourceKey, target: targetId }) => {
            // Verificar que la conversión existe en CONVERSION_MAP
            const targets = CONVERSION_MAP[sourceKey];
            if (!targets) return;
            
            const targetInfo = targets.find((t) => t.id === targetId);
            if (!targetInfo) return;
            
            // Evitar duplicados (importante para formatos de imagen unificados)
            if (alreadyEmitted(emitted, sourceKey, targetId)) return;
            
            const sourceLabel = SOURCE_LABELS[sourceKey] || sourceKey.toUpperCase();
            const primarySourceFormat = sourceKey;
            
            result.push({
                id: `${sourceKey}-${targetId}`,
                sourceKey,
                sourceLabel,
                targetId: targetInfo.id,
                targetLabel: targetInfo.name,
                category,
                icon: targetInfo.icon,
                primarySourceFormat,
                tooltip: CONVERSION_TOOLTIPS[`${sourceKey}-${targetId}`] || `Convierte ${sourceLabel} a ${targetInfo.name}`
            });
        });
    });

    return result;
}

export const CONVERSION_CATEGORY_LABELS: Record<ConversionCategory, string> = {
    document: 'Documentos',
    image: 'Imágenes y CAD',
    web: 'Web y XML'
};

/** Herramientas y procesos PDF: lista única, sin duplicar con las conversiones de formato. */
export const PDF_TOOLS_LABEL = 'Herramientas y procesos PDF';

export interface PdfToolItem {
    id: string;
    name: string;
    icon: LucideIcon;
    tooltip?: string;
}

/** Tool id → endpoint backend (las 18 herramientas tienen backend). */
export const PDF_TOOL_ENDPOINT: Record<string, string> = {
    'unir-pdf': 'merge',
    'dividir-pdf': 'split',
    'comprimir-pdf': 'compress',
    'rotar-pdf': 'rotate',
    'marca-agua': 'watermark',
    'proteger-pdf': 'protect',
    'desbloquear-pdf': 'unlock',
    'ordenar-pdf': 'order',
    'pdf-a': 'pdfa',
    'reparar-pdf': 'repair',
    'numeros-pagina': 'page-numbers',
    'recortar-pdf': 'crop',
    'comparar-pdf': 'compare',
    'editar-pdf': 'edit',
    'firmar-pdf': 'sign',
    'ocr-pdf': 'ocr',
    'escanear-pdf': 'scan',
    'censurar-pdf': 'redact'
};

/** IDs de herramientas PDF operativas (las 18). */
export const PDF_TOOLS_OPERATIONAL: string[] = Object.keys(PDF_TOOL_ENDPOINT);

/**
 * Tooltips informativos para herramientas PDF
 */
export const PDF_TOOLS_TOOLTIPS: Record<string, string> = {
    'unir-pdf': 'Combina múltiples archivos PDF en un solo documento',
    'comprimir-pdf': 'Reduce el tamaño del archivo PDF sin perder calidad significativa',
    'dividir-pdf': 'Separa un PDF en múltiples archivos por páginas o rangos',
    'rotar-pdf': 'Gira las páginas del PDF en cualquier dirección (90°, 180°, 270°)',
    'proteger-pdf': 'Agrega contraseña y permisos de seguridad a tu PDF',
    'desbloquear-pdf': 'Elimina la protección con contraseña de archivos PDF',
    'marca-agua': 'Añade marca de agua personalizada (texto o imagen) a las páginas',
    'pdf-a': 'Convierte PDF estándar a formato PDF/A para archivo de largo plazo',
    'ordenar-pdf': 'Reorganiza el orden de las páginas de un documento PDF',
    'recortar-pdf': 'Recorta márgenes o áreas específicas de las páginas PDF',
    'numeros-pagina': 'Agrega numeración automática a las páginas del documento',
    'comparar-pdf': 'Compara dos versiones de PDF y resalta las diferencias',
    'reparar-pdf': 'Intenta reparar archivos PDF corruptos o dañados',
    'editar-pdf': 'Edita texto, imágenes y elementos dentro del PDF',
    'firmar-pdf': 'Añade firma digital o manuscrita a documentos PDF',
    'ocr-pdf': 'Reconoce y extrae texto de PDFs escaneados o imágenes',
    'escanear-pdf': 'Convierte documentos escaneados en archivos PDF',
    'censurar-pdf': 'Oculta o elimina permanentemente información sensible del PDF'
};

/** 
 * 18 herramientas PDF ordenadas por popularidad de uso
 * Las más utilizadas aparecen primero
 */
export const PDF_TOOLS: PdfToolItem[] = [
    // Top tier - Más utilizadas
    { id: 'unir-pdf', name: 'Unir PDF', icon: Merge, tooltip: PDF_TOOLS_TOOLTIPS['unir-pdf'] },
    { id: 'comprimir-pdf', name: 'Comprimir PDF', icon: Shrink, tooltip: PDF_TOOLS_TOOLTIPS['comprimir-pdf'] },
    { id: 'dividir-pdf', name: 'Dividir PDF', icon: Split, tooltip: PDF_TOOLS_TOOLTIPS['dividir-pdf'] },
    { id: 'rotar-pdf', name: 'Rotar PDF', icon: RotateCw, tooltip: PDF_TOOLS_TOOLTIPS['rotar-pdf'] },
    { id: 'proteger-pdf', name: 'Proteger PDF', icon: Lock, tooltip: PDF_TOOLS_TOOLTIPS['proteger-pdf'] },
    { id: 'desbloquear-pdf', name: 'Desbloquear PDF', icon: LockOpen, tooltip: PDF_TOOLS_TOOLTIPS['desbloquear-pdf'] },
    { id: 'marca-agua', name: 'Marca de agua', icon: Droplets, tooltip: PDF_TOOLS_TOOLTIPS['marca-agua'] },
    // Mid tier - Uso moderado
    { id: 'pdf-a', name: 'PDF → PDF/A', icon: FileCheck, tooltip: PDF_TOOLS_TOOLTIPS['pdf-a'] },
    { id: 'ordenar-pdf', name: 'Ordenar PDF', icon: ArrowUpDown, tooltip: PDF_TOOLS_TOOLTIPS['ordenar-pdf'] },
    { id: 'recortar-pdf', name: 'Recortar PDF', icon: Crop, tooltip: PDF_TOOLS_TOOLTIPS['recortar-pdf'] },
    { id: 'numeros-pagina', name: 'Números de página', icon: Hash, tooltip: PDF_TOOLS_TOOLTIPS['numeros-pagina'] },
    { id: 'comparar-pdf', name: 'Comparar PDF', icon: GitCompare, tooltip: PDF_TOOLS_TOOLTIPS['comparar-pdf'] },
    { id: 'reparar-pdf', name: 'Reparar PDF', icon: Wrench, tooltip: PDF_TOOLS_TOOLTIPS['reparar-pdf'] },
    // Lower tier - Uso especializado
    { id: 'editar-pdf', name: 'Editar PDF', icon: PenLine, tooltip: PDF_TOOLS_TOOLTIPS['editar-pdf'] },
    { id: 'firmar-pdf', name: 'Firmar PDF', icon: PenTool, tooltip: PDF_TOOLS_TOOLTIPS['firmar-pdf'] },
    { id: 'ocr-pdf', name: 'OCR PDF', icon: ScanSearch, tooltip: PDF_TOOLS_TOOLTIPS['ocr-pdf'] },
    { id: 'escanear-pdf', name: 'Escanear a PDF', icon: Scan, tooltip: PDF_TOOLS_TOOLTIPS['escanear-pdf'] },
    { id: 'censurar-pdf', name: 'Censurar PDF', icon: Eraser, tooltip: PDF_TOOLS_TOOLTIPS['censurar-pdf'] }
];
