export interface User {
    id: number;
    email: string;
    full_name: string | null;
    is_active: boolean;
    free_conversion_count: number;
}

export interface LoginCredentials {
    username: string;
    password: string;
}

export interface RegisterData {
    email: string;
    password: string;
    full_name?: string;
}

export interface AuthToken {
    access_token: string;
    token_type: string;
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
