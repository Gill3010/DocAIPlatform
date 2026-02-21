import type { LoginCredentials, RegisterData, AuthToken, User, RegisterResponse } from '../../types';
import { API_URL } from './config';
import { apiRequest } from './request';
import { getToken } from '../storageService';
import { apiErrorFromResponse } from './errors';

export async function login(credentials: LoginCredentials): Promise<AuthToken> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    if (credentials.turnstile_token) {
        formData.append('turnstile_token', credentials.turnstile_token);
    }
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

export async function register(data: RegisterData): Promise<RegisterResponse> {
    const body: Record<string, unknown> = {
        email: data.email,
        password: data.password,
        full_name: data.full_name ?? '',
    };
    if (data.turnstile_token) {
        body.turnstile_token = data.turnstile_token;
    }
    return apiRequest<RegisterResponse>('/auth/register', { method: 'POST', body: JSON.stringify(body) });
}

export async function verifyEmail(token: string): Promise<{ verified: boolean; email: string; message: string }> {
    return apiRequest<{ verified: boolean; email: string; message: string }>('/auth/verify-email', {
        method: 'POST',
        body: JSON.stringify({ token }),
    });
}

export async function forgotPassword(email: string): Promise<{ message: string }> {
    return apiRequest<{ message: string }>('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email }),
    });
}

export async function resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
    return apiRequest<{ message: string }>('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ token, new_password: newPassword }),
    });
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
