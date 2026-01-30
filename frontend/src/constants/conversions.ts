import {
    FileText,
    File,
    Image,
    Globe,
    Ruler,
    GraduationCap,
    type LucideIcon
} from 'lucide-react';

/**
 * Fuente única de verdad para conversiones.
 * Usado por Convert (selector de formatos) y Dashboard (cards por tipo).
 */

export const SOURCE_LABELS: Record<string, string> = {
    docx: 'Word',
    pdf: 'PDF',
    txt: 'Texto',
    xml: 'XML',
    html: 'HTML',
    htm: 'HTML',
    png: 'Imagen (PNG/JPG)',
    jpg: 'Imagen (PNG/JPG)',
    jpeg: 'Imagen (PNG/JPG)',
    dxf: 'DXF (CAD)'
};

/** Etiquetas cortas para formato destino (hints en página Convertir). */
export const TARGET_LABELS: Record<string, string> = {
    pdf: 'PDF',
    docx: 'Word',
    txt: 'Texto',
    xml: 'XML',
    html: 'HTML',
    png: 'PNG',
    dxf: 'DXF'
};

export const CONVERSION_MAP: Record<string, Array<{ id: string; name: string; icon: LucideIcon }>> = {
    png: [
        { id: 'pdf', name: 'Documento PDF', icon: FileText },
        { id: 'dxf', name: 'Archivo DXF (CAD)', icon: Ruler }
    ],
    jpg: [
        { id: 'pdf', name: 'Documento PDF', icon: FileText },
        { id: 'dxf', name: 'Archivo DXF (CAD)', icon: Ruler }
    ],
    jpeg: [
        { id: 'pdf', name: 'Documento PDF', icon: FileText },
        { id: 'dxf', name: 'Archivo DXF (CAD)', icon: Ruler }
    ],
    pdf: [
        { id: 'docx', name: 'Documento Word', icon: File },
        { id: 'png', name: 'Imagen PNG', icon: Image },
        { id: 'txt', name: 'Texto Plano', icon: FileText }
    ],
    txt: [
        { id: 'docx', name: 'Documento Word', icon: File }
    ],
    docx: [
        { id: 'pdf', name: 'Documento PDF', icon: FileText },
        { id: 'txt', name: 'Texto Plano', icon: FileText },
        { id: 'xml', name: 'XML', icon: GraduationCap }
    ],
    xml: [
        { id: 'html', name: 'Página HTML', icon: Globe },
        { id: 'docx', name: 'Documento Word', icon: File }
    ],
    html: [
        { id: 'xml', name: 'Archivo XML', icon: FileText }
    ],
    htm: [
        { id: 'xml', name: 'Archivo XML', icon: FileText }
    ],
    dxf: [
        { id: 'png', name: 'Imagen PNG', icon: Image }
    ]
};

export type ConversionCategory = 'document' | 'image' | 'web';

const CATEGORY_BY_SOURCE: Record<string, ConversionCategory> = {
    docx: 'document',
    pdf: 'document',
    txt: 'document',
    xml: 'web',
    html: 'web',
    htm: 'web',
    png: 'image',
    jpg: 'image',
    jpeg: 'image',
    dxf: 'image'
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
}

/**
 * Agrupa formatos de imagen para no duplicar cards (PNG/JPG/JPEG → un solo card "Imagen → X").
 */
const IMAGE_SOURCES = ['png', 'jpg', 'jpeg'];

function canonicalSourceKey(sourceKey: string): string {
    return IMAGE_SOURCES.includes(sourceKey) ? 'image' : sourceKey;
}

function alreadyEmitted(
    emitted: Set<string>,
    sourceKey: string,
    targetId: string
): boolean {
    const key = canonicalSourceKey(sourceKey) + '->' + targetId;
    if (emitted.has(key)) return true;
    emitted.add(key);
    return false;
}

/**
 * Lista de tipos de conversión para el dashboard.
 * Derivada de CONVERSION_MAP; sin duplicados (PNG/JPG/JPEG unificados como "Imagen").
 */
export function getDashboardConversions(): DashboardConversionType[] {
    const emitted = new Set<string>();
    const result: DashboardConversionType[] = [];

    const processSource = (sourceKey: string) => {
        const targets = CONVERSION_MAP[sourceKey];
        if (!targets) return;
        const sourceLabel = SOURCE_LABELS[sourceKey] || sourceKey.toUpperCase();
        const category = CATEGORY_BY_SOURCE[sourceKey] || 'document';
        const primarySourceFormat = IMAGE_SOURCES.includes(sourceKey) ? 'png' : sourceKey;

        for (const t of targets) {
            if (alreadyEmitted(emitted, sourceKey, t.id)) continue;
            result.push({
                id: `${canonicalSourceKey(sourceKey)}-${t.id}`,
                sourceKey,
                sourceLabel,
                targetId: t.id,
                targetLabel: t.name,
                category,
                icon: t.icon,
                primarySourceFormat
            });
        }
    };

    // Orden estable: document, image, web. Para imagen solo procesar 'png' (jpg/jpeg dan mismos destinos).
    const order: Record<ConversionCategory, string[]> = {
        document: ['docx', 'pdf', 'txt'],
        image: ['png', 'dxf'].filter((k) => k in CONVERSION_MAP),
        web: ['xml', 'html', 'htm'].filter((k) => k in CONVERSION_MAP)
    };
    (['document', 'image', 'web'] as ConversionCategory[]).forEach((cat) => {
        order[cat].forEach((sourceKey) => processSource(sourceKey));
    });

    return result;
}

export const CONVERSION_CATEGORY_LABELS: Record<ConversionCategory, string> = {
    document: 'Documentos',
    image: 'Imágenes y CAD',
    web: 'Web y XML'
};
