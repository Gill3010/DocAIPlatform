import { getAnonymousSessionId, removeAnonymousSessionId, removeAnonymousUsed } from '../services/storageService';

/** Key name for anonymous session (for consumers that need it) */
export const STORAGE_KEY = 'anon_session_id';

/** Get stored anonymous session ID (before clearing, for linking to user) */
export function getStoredSessionId(): string | null {
  return getAnonymousSessionId();
}

/** Clear anonymous session data (call after user logs in and after link) */
export function clearAnonymousSession(): void {
  removeAnonymousSessionId();
  removeAnonymousUsed();
}
