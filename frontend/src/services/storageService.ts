/**
 * Servicio centralizado para localStorage y sessionStorage.
 * Acceso seguro en SSR (typeof window) y claves tipadas para token, sesión anónima, etc.
 */

const TOKEN_KEY = 'token';
const ANON_SESSION_KEY = 'anon_session_id';
const ANON_USED_KEY = 'anon_conversions_used';
const PENDING_ANON_SESSION_KEY = 'pending_anon_session_id';

function getStorage(type: 'local' | 'session'): Storage | null {
    if (typeof window === 'undefined') return null;
    return type === 'local' ? window.localStorage : window.sessionStorage;
}

function getItem(key: string, type: 'local' | 'session' = 'local'): string | null {
    const storage = getStorage(type);
    if (!storage) return null;
    try {
        return storage.getItem(key);
    } catch {
        return null;
    }
}

function setItem(key: string, value: string, type: 'local' | 'session' = 'local'): void {
    const storage = getStorage(type);
    if (!storage) return;
    try {
        storage.setItem(key, value);
    } catch {
        // ignore
    }
}

function removeItem(key: string, type: 'local' | 'session' = 'local'): void {
    const storage = getStorage(type);
    if (!storage) return;
    try {
        storage.removeItem(key);
    } catch {
        // ignore
    }
}

// --- Token (API, logout) ---
/** Returns token from localStorage 'token' or, if null, from Zustand persist key (rehydration). */
export function getToken(): string | null {
    const direct = getItem(TOKEN_KEY, 'local');
    if (direct) return direct;
    if (typeof window === 'undefined') return null;
    try {
        const raw = window.localStorage.getItem('saas-app-storage');
        if (raw) {
            const parsed = JSON.parse(raw) as { state?: { token?: string | null } };
            const t = parsed?.state?.token;
            if (t) return t;
        }
    } catch {
        // ignore
    }
    return null;
}

export function setToken(value: string | null): void {
    if (value == null) removeItem(TOKEN_KEY, 'local');
    else setItem(TOKEN_KEY, value, 'local');
}

export function removeToken(): void {
    removeItem(TOKEN_KEY, 'local');
}

// --- Sesión anónima (conversiones) ---
export function getAnonymousSessionId(): string | null {
    return getItem(ANON_SESSION_KEY, 'local');
}

export function setAnonymousSessionId(value: string): void {
    setItem(ANON_SESSION_KEY, value, 'local');
}

export function removeAnonymousSessionId(): void {
    removeItem(ANON_SESSION_KEY, 'local');
}

export function getAnonymousUsed(): string | null {
    return getItem(ANON_USED_KEY, 'local');
}

export function setAnonymousUsed(value: number): void {
    setItem(ANON_USED_KEY, String(Math.max(0, value)), 'local');
}

export function removeAnonymousUsed(): void {
    removeItem(ANON_USED_KEY, 'local');
}

// --- Pending anon session (Login/OAuth flow, sessionStorage) ---
export function getPendingAnonymousSessionId(): string | null {
    return getItem(PENDING_ANON_SESSION_KEY, 'session');
}

export function setPendingAnonymousSessionId(value: string): void {
    setItem(PENDING_ANON_SESSION_KEY, value, 'session');
}

export function removePendingAnonymousSessionId(): void {
    removeItem(PENDING_ANON_SESSION_KEY, 'session');
}

// --- Genérico (por si se necesita otra clave) ---
export const storageKeys = {
    TOKEN_KEY,
    ANON_SESSION_KEY,
    ANON_USED_KEY,
    PENDING_ANON_SESSION_KEY,
} as const;

export const storageService = {
    getToken,
    setToken,
    removeToken,
    getAnonymousSessionId,
    setAnonymousSessionId,
    removeAnonymousSessionId,
    getAnonymousUsed,
    setAnonymousUsed,
    removeAnonymousUsed,
    getPendingAnonymousSessionId,
    setPendingAnonymousSessionId,
    removePendingAnonymousSessionId,
    getItem: (key: string, type?: 'local' | 'session') => getItem(key, type ?? 'local'),
    setItem: (key: string, value: string, type?: 'local' | 'session') => setItem(key, value, type ?? 'local'),
    removeItem: (key: string, type?: 'local' | 'session') => removeItem(key, type ?? 'local'),
};
