import type { LoginCredentials, RegisterData, AuthToken, User } from '../../types';
import { API_URL } from './config';
import { apiRequest } from './request';
import { getToken } from '../storageService';
import { apiErrorFromResponse } from './errors';

export async function login(credentials: LoginCredentials): Promise<AuthToken> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Login failed');
    return response.json();
}

export async function getGoogleAuthUrl(redirectUri?: string): Promise<{ url: string; state: string }> {
    const params = redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : '';
    return apiRequest<{ url: string; state: string }>(`/auth/google/url${params}`);
}

export async function googleAuth(data: { code: string; state: string; redirect_uri: string }): Promise<AuthToken> {
    const response = await fetch(`${API_URL}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Error al iniciar sesión con Google');
    return response.json();
}

export async function getFacebookAuthUrl(redirectUri?: string): Promise<{ url: string; state: string }> {
    const params = redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : '';
    return apiRequest<{ url: string; state: string }>(`/auth/facebook/url${params}`);
}

export async function facebookAuth(data: { code: string; state: string; redirect_uri: string }): Promise<AuthToken> {
    const response = await fetch(`${API_URL}/auth/facebook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Error al iniciar sesión con Facebook');
    return response.json();
}

export async function register(data: RegisterData): Promise<User> {
    return apiRequest<User>('/auth/register', { method: 'POST', body: JSON.stringify(data) });
}

export async function linkAnonymousSession(anonymousSessionId: string): Promise<{ credits_used: number; credits_remaining: number }> {
    const token = getToken();
    if (!token) throw new Error('No token');
    const response = await fetch(`${API_URL}/auth/link-anonymous-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ anonymous_session_id: anonymousSessionId }),
    });
    if (!response.ok) await apiErrorFromResponse(response, 'Link failed');
    return response.json();
}
