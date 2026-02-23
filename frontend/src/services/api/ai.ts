import { API_URL } from './config';
import { getToken } from '../storageService';
import { apiErrorFromResponse } from './errors';

/** Headers para API de IA: token si existe, y siempre sesión anónima como fallback (evita 401 con token caducado). */
function getAuthHeaders(anonymousSessionId?: string): Record<string, string> {
    const headers: Record<string, string> = {};
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (anonymousSessionId) headers['X-Anonymous-Session-Id'] = anonymousSessionId;
    return headers;
}

/** Envía mensaje al asistente IA (Bedrock). Soporta sesiones y adjuntos. */
export async function sendChatMessage(
    message: string,
    anonymousSessionId?: string,
    options?: { sessionId?: string; attachmentIds?: string[] }
): Promise<{ message: string; credits_remaining: number; session_id?: string }> {
    const headers = { ...getAuthHeaders(anonymousSessionId), 'Content-Type': 'application/json' };
    const body = {
        message,
        session_id: options?.sessionId ?? null,
        attachment_ids: options?.attachmentIds ?? null,
    };
    const response = await fetch(`${API_URL}/ai/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Request failed');
    return response.json();
}

export async function getAICredits(anonymousSessionId?: string): Promise<any> {
    const response = await fetch(`${API_URL}/ai/credits`, { headers: getAuthHeaders(anonymousSessionId) });
    if (!response.ok) await apiErrorFromResponse(response, 'Request failed');
    return response.json();
}

export interface ChatSessionItem {
    id: string;
    title: string | null;
    created_at: string;
    updated_at: string;
}

export async function getChatSessions(anonymousSessionId?: string): Promise<ChatSessionItem[]> {
    const response = await fetch(`${API_URL}/ai/sessions`, { headers: getAuthHeaders(anonymousSessionId) });
    if (!response.ok) await apiErrorFromResponse(response, 'Request failed');
    return response.json();
}

export interface ChatMessageItem {
    id: string;
    role: string;
    content: string;
    created_at: string;
}

export interface ChatSessionDetail {
    id: string;
    title: string | null;
    messages: ChatMessageItem[];
}

export async function getChatSession(
    sessionId: string,
    anonymousSessionId?: string
): Promise<ChatSessionDetail> {
    const response = await fetch(`${API_URL}/ai/sessions/${sessionId}`, {
        headers: getAuthHeaders(anonymousSessionId),
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Request failed');
    return response.json();
}

export async function createChatSession(anonymousSessionId?: string): Promise<{ id: string; title: string | null; created_at: string }> {
    const response = await fetch(`${API_URL}/ai/sessions`, {
        method: 'POST',
        headers: getAuthHeaders(anonymousSessionId),
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Request failed');
    return response.json();
}

export async function updateChatSession(
    sessionId: string,
    title: string,
    anonymousSessionId?: string
): Promise<ChatSessionItem> {
    const response = await fetch(`${API_URL}/ai/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { ...getAuthHeaders(anonymousSessionId), 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title || 'Nuevo chat' }),
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Update failed');
    return response.json();
}

export async function deleteChatSession(
    sessionId: string,
    anonymousSessionId?: string
): Promise<void> {
    const response = await fetch(`${API_URL}/ai/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(anonymousSessionId),
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Delete failed');
}

export async function uploadChatAttachment(
    file: File,
    anonymousSessionId?: string
): Promise<{ attachment_id: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const headers = getAuthHeaders(anonymousSessionId);
    const response = await fetch(`${API_URL}/ai/upload`, {
        method: 'POST',
        headers,
        body: formData,
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Upload failed');
    return response.json();
}
