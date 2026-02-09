import type { User, ProfileUpdate } from '../../types';
import { API_URL } from './config';
import { apiRequest } from './request';
import { getToken } from '../storageService';
import { apiErrorFromResponse } from './errors';

export async function getCurrentUser(): Promise<User> {
    return apiRequest<User>('/users/me');
}

export async function getProfile(): Promise<User> {
    return apiRequest<User>('/users/me');
}

export async function updateProfile(data: ProfileUpdate): Promise<User> {
    return apiRequest<User>('/users/me', { method: 'PATCH', body: JSON.stringify(data) });
}

export async function uploadAvatar(file: File): Promise<User> {
    const token = getToken();
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_URL}/users/me/avatar`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Error al subir la imagen');
    return response.json();
}

export async function getUserStats(): Promise<any> {
    return apiRequest<any>('/users/me/stats');
}

export async function getAnonymousStats(anonymousSessionId: string): Promise<{
    conversions: { total: number; completed: number };
    success_rate: number;
    avg_processing_time: string;
}> {
    const response = await fetch(`${API_URL}/users/anon-stats`, {
        headers: { 'X-Anonymous-Session-Id': anonymousSessionId },
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Failed to load anonymous stats');
    return response.json();
}

export async function searchUsers(query: string): Promise<any[]> {
    return apiRequest<any[]>(`/users/search?query=${encodeURIComponent(query)}`);
}
