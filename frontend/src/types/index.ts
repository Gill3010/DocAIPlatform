export interface User {
    id: number;
    email: string;
    full_name: string | null;
    is_active: boolean;
    free_conversion_count: number;
    monthly_conversion_count?: number;
    last_billing_reset?: string | null;
    is_superuser?: boolean;
    is_premium?: boolean;
    premium_plan_id?: string | null;
    can_access_admin_panel?: boolean;
    can_view_payments?: boolean;
    created_at?: string;
    auth_provider?: string;
    avatar_url?: string | null;
}

export interface ProfileUpdate {
    full_name?: string;
    password?: string;
}

export interface LoginCredentials {
    username: string;
    password: string;
    turnstile_token?: string | null;
}

export interface RegisterData {
    email: string;
    password: string;
    full_name?: string;
    turnstile_token?: string | null;
}

export interface AuthToken {
    access_token: string;
    token_type: string;
}

export interface RegisterResponse {
    message?: string;
    email?: string;
    verification_url?: string;  // Solo cuando SES no configurado (para pruebas)
    user?: User;
    access_token?: string;
    token_type?: string;
}

export interface ConversionJob {
    id: string;
    from_format: string;
    to_format: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    created_at: string;
    file_name: string;
}

export type Theme = 'light' | 'dark';
