import { API_URL } from './config';
import { getToken } from '../storageService';
import { apiErrorFromResponse } from './errors';

export async function sendChatMessage(message: string, anonymousSessionId?: string): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (anonymousSessionId) {
        headers['X-Anonymous-Session-Id'] = anonymousSessionId;
    } else {
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_URL}/ai/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message }),
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Request failed');
    return response.json();
}

export async function getAICredits(anonymousSessionId?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (anonymousSessionId) {
        headers['X-Anonymous-Session-Id'] = anonymousSessionId;
    } else {
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_URL}/ai/credits`, { headers });
    if (!response.ok) await apiErrorFromResponse(response, 'Request failed');
    return response.json();
}
