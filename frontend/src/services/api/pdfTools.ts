import { API_URL } from './config';
import { getToken } from '../storageService';
import { apiErrorFromResponse } from './errors';

/**
 * Herramienta PDF: POST multipart al endpoint indicado.
 * Mismos límites que conversiones: anónimo 3, registrado 5 (compartidos con IA).
 * Devuelve el blob y, si el backend lo envía, créditos restantes.
 */
export async function pdfTool(
    endpoint: string,
    formData: FormData,
    options?: { anonymousSessionId?: string }
): Promise<{ blob: Blob; creditsRemaining?: number }> {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (options?.anonymousSessionId) headers['X-Anonymous-Session-Id'] = options.anonymousSessionId;
    const response = await fetch(`${API_URL}/pdf-tools/${endpoint}`, {
        method: 'POST',
        headers,
        body: formData,
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Error en la herramienta PDF');
    const blob = await response.blob();
    const creditsHeader = response.headers.get('X-Credits-Remaining');
    const creditsRemaining =
        creditsHeader !== null && creditsHeader !== '' ? parseInt(creditsHeader, 10) : undefined;
    if (creditsRemaining !== undefined && Number.isNaN(creditsRemaining)) {
        return { blob };
    }
    return { blob, creditsRemaining };
}
