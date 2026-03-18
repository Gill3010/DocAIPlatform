import { API_URL } from './config';
import { apiRequest } from './request';
import { getToken } from '../storageService';
import { apiErrorFromResponse } from './errors';

export async function formatManuscript(file: File): Promise<Blob> {
    const token = getToken();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('style', 'standard');

    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_URL}/manuscript/format`, {
        method: 'POST',
        headers,
        body: formData,
    });

    if (!response.ok) await apiErrorFromResponse(response, 'Format failed');
    return response.blob();
}

export async function getManuscriptHistory(limit: number = 20): Promise<any[]> {
    return apiRequest<any[]>(`/manuscript/history?limit=${limit}`);
}

export async function downloadFormattedManuscript(formatId: number): Promise<Blob> {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_URL}/manuscript/download/${formatId}`, { headers });
    if (!response.ok) throw new Error('Download failed');
    return response.blob();
}
