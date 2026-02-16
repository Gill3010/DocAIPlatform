import { API_URL } from './config';
import { apiRequest } from './request';
import { getToken } from '../storageService';
import { apiErrorFromResponse } from './errors';

export async function uploadAndConvert(
    file: File,
    targetFormat: string,
    options?: { anonymousSessionId?: string }
): Promise<any> {
    const token = getToken();
    const formData = new FormData();
    formData.append('file', file);
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (options?.anonymousSessionId) headers['X-Anonymous-Session-Id'] = options.anonymousSessionId;
    const endpoint = token
        ? `/convert/upload?target_format=${targetFormat}`
        : `/convert/upload-anonymous?target_format=${targetFormat}`;
    const response = await fetch(`${API_URL}${endpoint}`, { method: 'POST', headers, body: formData });
    if (!response.ok) await apiErrorFromResponse(response, 'Upload failed');
    return response.json();
}

export async function downloadConvertedFile(
    conversionId: number,
    options?: { anonymousSessionId?: string }
): Promise<Blob> {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (options?.anonymousSessionId) headers['X-Anonymous-Session-Id'] = options.anonymousSessionId;
    const endpoint = token
        ? `/convert/download/${conversionId}`
        : `/convert/download-anonymous/${conversionId}`;
    const response = await fetch(`${API_URL}${endpoint}`, { headers });
    if (!response.ok) throw new Error('Download failed');
    return response.blob();
}

export async function getConversionHistory(limit: number = 20): Promise<any[]> {
    return apiRequest<any[]>(`/convert/history?limit=${limit}`);
}

export async function getConversionStatus(
    conversionId: number,
    options?: { anonymousSessionId?: string }
): Promise<any> {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (options?.anonymousSessionId) headers['X-Anonymous-Session-Id'] = options.anonymousSessionId;
    const endpoint = token
        ? `/convert/status/${conversionId}`
        : `/convert/status-anonymous/${conversionId}`;
    return apiRequest<any>(endpoint, { headers });
}

export async function getSupportedFormats(): Promise<any> {
    return apiRequest<any>('/convert/supported-formats');
}
