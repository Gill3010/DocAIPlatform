import { API_URL } from './config';
import { useAppStore } from '../../stores/appStore';
import { getToken } from '../storageService';
import { apiErrorFromResponse } from './errors';

/**
 * Petición JSON al API. Añade token si existe; en 401 hace logout.
 * Lanza ApiError con statusCode y detail del backend.
 */
export async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = getToken();
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
    };
    if (token && !endpoint.includes('/auth/')) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
    if (!response.ok) {
        if (response.status === 401) {
            useAppStore.getState().logout();
        }
        await apiErrorFromResponse(response, 'Request failed');
    }
    return response.json();
}
