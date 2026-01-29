import type { LoginCredentials, RegisterData, AuthToken, User } from '../types';

const API_URL = 'http://localhost:8000/api/v1';

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
}

export const apiService = new ApiService();
