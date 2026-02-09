import { apiRequest } from './request';

export async function createDocumentFromConversion(conversionId: number): Promise<any> {
    return apiRequest<any>(`/documents/from-conversion/${conversionId}`, { method: 'POST' });
}

export async function getDocuments(): Promise<any[]> {
    return apiRequest<any[]>('/documents/');
}

export async function getDocument(id: number): Promise<any> {
    return apiRequest<any>(`/documents/${id}`);
}

export async function deleteDocument(id: number): Promise<void> {
    return apiRequest<void>(`/documents/${id}`, { method: 'DELETE' });
}

export async function getDocumentPermissions(documentId: number): Promise<any[]> {
    return apiRequest<any[]>(`/documents/${documentId}/permissions`);
}

export async function addDocumentPermission(
    documentId: number,
    userId: number,
    role: 'viewer' | 'editor'
): Promise<any> {
    return apiRequest<any>(`/documents/${documentId}/permissions`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, role }),
    });
}

export async function removeDocumentPermission(documentId: number, userId: number): Promise<void> {
    return apiRequest<void>(`/documents/${documentId}/permissions/${userId}`, { method: 'DELETE' });
}
