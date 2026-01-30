import type { LoginCredentials, RegisterData, AuthToken, User } from '../types';

// Usa el mismo host que la página (funciona con localhost o IP pública)
const API_URL = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

class ApiService {
    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const token = localStorage.getItem('token');

        const headers: HeadersInit = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (token && !endpoint.includes('/auth/')) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const error = await response.text();
            throw new Error(error || 'Request failed');
        }

        return response.json();
    }

    async login(credentials: LoginCredentials): Promise<AuthToken> {
        const formData = new URLSearchParams();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        return response.json();
    }

    async register(data: RegisterData): Promise<User> {
        return this.request<User>('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getCurrentUser(): Promise<User> {
        return this.request<User>('/users/me');
    }

    async uploadAndConvert(file: File, targetFormat: string): Promise<any> {
        const token = localStorage.getItem('token');
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/convert/upload?target_format=${targetFormat}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return response.json();
    }

    async downloadConvertedFile(conversionId: number): Promise<Blob> {
        const token = localStorage.getItem('token');

        const response = await fetch(`${API_URL}/convert/download/${conversionId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Download failed');
        }

        return response.blob();
    }

    async getConversionHistory(limit: number = 20): Promise<any[]> {
        return this.request<any[]>(`/convert/history?limit=${limit}`);
    }

    async getSupportedFormats(): Promise<any> {
        return this.request<any>('/convert/supported-formats');
    }

    async getUserStats(): Promise<any> {
        return this.request<any>('/users/me/stats');
    }

    async sendChatMessage(message: string): Promise<any> {
        return this.request<any>('/ai/chat', {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
    }

    async getAICredits(): Promise<any> {
        return this.request<any>('/ai/credits');
    }
}

export const apiService = new ApiService();
