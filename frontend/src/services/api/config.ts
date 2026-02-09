/**
 * Base URL del backend.
 * En build: usa VITE_API_URL si está definido (ej. en .env: VITE_API_URL=http://localhost:8000).
 * Si no, mismo host y puerto 8000.
 */
const defaultBase =
  typeof window !== 'undefined'
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : 'http://localhost:8000';
const envBase =
  typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL?.trim();
export const API_BASE = envBase || defaultBase;
export const API_URL = `${API_BASE}/api/v1`;

/** URL absoluta para avatar (ruta estática del backend) */
export function getAvatarUrl(avatarPath: string | null | undefined): string | null {
    if (!avatarPath) return null;
    return avatarPath.startsWith('http') ? avatarPath : `${API_BASE}${avatarPath}`;
}
