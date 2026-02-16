import { apiRequest } from './request';

export async function getAdminMe(): Promise<{
    id: number;
    email: string;
    full_name: string | null;
    is_superuser: boolean;
    can_access_admin_panel: boolean;
}> {
    return apiRequest('/admin/me');
}

export async function getAdminStats(): Promise<{
    users: { total: number; active: number };
    conversions: { total: number; completed: number };
}> {
    return apiRequest('/admin/stats');
}

export async function getAdminUsers(params: {
    page?: number;
    size?: number;
    email?: string;
    is_active?: boolean;
}): Promise<{
    items: Array<{
        id: number;
        email: string;
        full_name: string | null;
        is_active: boolean;
        is_superuser: boolean;
        can_access_admin_panel: boolean;
        can_view_payments: boolean;
        auth_provider: string | null;
        created_at: string | null;
    }>;
    total: number;
    page: number;
    size: number;
    pages: number;
}> {
    const sp = new URLSearchParams();
    if (params.page != null) sp.set('page', String(params.page));
    if (params.size != null) sp.set('size', String(params.size));
    if (params.email) sp.set('email', params.email);
    if (params.is_active !== undefined) sp.set('is_active', String(params.is_active));
    const q = sp.toString();
    return apiRequest(`/admin/users${q ? `?${q}` : ''}`);
}

export async function getAdminUser(userId: number): Promise<any> {
    return apiRequest(`/admin/users/${userId}`);
}

export async function patchAdminUser(
    userId: number,
    body: { is_active?: boolean; can_access_admin_panel?: boolean; can_view_payments?: boolean }
): Promise<any> {
    return apiRequest(`/admin/users/${userId}`, { method: 'PATCH', body: JSON.stringify(body) });
}

export async function getAdminConversions(params: {
    page?: number;
    size?: number;
    user_id?: number;
    status?: string;
    date_from?: string;
    date_to?: string;
}): Promise<{
    items: Array<{
        id: number;
        user_id: number | null;
        anonymous_session_id: string | null;
        original_filename: string;
        original_format: string;
        target_format: string;
        status: string;
        file_size: number | null;
        created_at: string | null;
        completed_at: string | null;
    }>;
    total: number;
    page: number;
    size: number;
    pages: number;
}> {
    const sp = new URLSearchParams();
    if (params.page != null) sp.set('page', String(params.page));
    if (params.size != null) sp.set('size', String(params.size));
    if (params.user_id != null) sp.set('user_id', String(params.user_id));
    if (params.status) sp.set('status', params.status);
    if (params.date_from) sp.set('date_from', params.date_from);
    if (params.date_to) sp.set('date_to', params.date_to);
    const q = sp.toString();
    return apiRequest(`/admin/conversions${q ? `?${q}` : ''}`);
}

export async function getAdminActivity(params: {
    page?: number;
    size?: number;
    action?: string;
}): Promise<{
    items: Array<{
        id: number;
        admin_user_id: number;
        action: string;
        resource_type: string;
        resource_id: string | null;
        details: string | null;
        created_at: string | null;
    }>;
    total: number;
    page: number;
    size: number;
    pages: number;
}> {
    const sp = new URLSearchParams();
    if (params.page != null) sp.set('page', String(params.page));
    if (params.size != null) sp.set('size', String(params.size));
    if (params.action) sp.set('action', params.action);
    const q = sp.toString();
    return apiRequest(`/admin/activity${q ? `?${q}` : ''}`);
}

export async function getAdminPayments(params: {
    page?: number;
    size?: number;
}): Promise<{
    items: Array<{
        id: number;
        user_id: number;
        user_email: string | null;
        provider: string;
        transaction_id: string | null;
        amount: number;
        currency: string;
        status: string;
        plan_id: string | null;
        created_at: string | null;
    }>;
    total: number;
    page: number;
    size: number;
    pages: number;
}> {
    const sp = new URLSearchParams();
    if (params.page != null) sp.set('page', String(params.page));
    if (params.size != null) sp.set('size', String(params.size));
    const q = sp.toString();
    return apiRequest(`/admin/payments${q ? `?${q}` : ''}`);
}
