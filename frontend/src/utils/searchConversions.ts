import type { DashboardConversionType } from '../constants/conversions';
import { CONVERSION_CATEGORY_LABELS } from '../constants/conversions';
import type { ConversionCategory } from '../constants/conversions';

/** Normaliza texto para búsqueda: minúsculas y sin acentos. */
function normalizeForSearch(s: string): string {
    return s
        .toLowerCase()
        .normalize('NFD')
        .replace(/\p{Diacritic}/gu, '')
        .trim();
}

/**
 * Extrae palabras buscables de una conversión (origen, destino, categoría, claves).
 * Cada palabra se normaliza para comparar por prefijo.
 */
function getSearchableWords(conv: DashboardConversionType): string[] {
    const categoryLabel = CONVERSION_CATEGORY_LABELS[conv.category as ConversionCategory];
    const raw = [
        conv.sourceLabel,
        conv.targetLabel,
        categoryLabel,
        conv.sourceKey,
        conv.targetId
    ].join(' ');
    const words = raw.split(/\s+/).filter(Boolean);
    const normalized = words.map((w) => normalizeForSearch(w));
    return [...new Set(normalized)];
}

/**
 * Filtra conversiones por query en tiempo real.
 * Cada token del query debe ser prefijo de al menos una palabra del origen, destino o categoría.
 * Ej: "H" → HTML, "P" → PDF, "W" → Word; no muestra todos los resultados con una letra.
 */
export function filterConversionsByQuery(
    conversions: DashboardConversionType[],
    query: string
): DashboardConversionType[] {
    const trimmed = query.trim();
    if (!trimmed) return conversions;

    const tokens = normalizeForSearch(trimmed)
        .split(/\s+/)
        .filter(Boolean);
    if (tokens.length === 0) return conversions;

    return conversions.filter((conv) => {
        const words = getSearchableWords(conv);
        return tokens.every((token) =>
            words.some((word) => word.startsWith(token))
        );
    });
}
