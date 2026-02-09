import { useCallback, useMemo, useState } from 'react';
import {
  getAnonymousSessionId,
  setAnonymousSessionId,
  getAnonymousUsed,
  setAnonymousUsed as setAnonymousUsedStorage,
  removeAnonymousSessionId,
  removeAnonymousUsed,
} from '../services/storageService';

const ANONYMOUS_LIMIT = 3;

function generateSessionId(): string {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function getStoredSessionId(): string {
  const stored = getAnonymousSessionId();
  if (stored) return stored;
  const id = generateSessionId();
  setAnonymousSessionId(id);
  return id;
}

function readStoredUsed(): number {
  const v = getAnonymousUsed();
  if (v != null) return Math.max(0, parseInt(v, 10) || 0);
  return 0;
}

export function useAnonymousSession() {
  const sessionId = useMemo(getStoredSessionId, []);
  const [anonymousConversionsUsed, setUsedState] = useState(readStoredUsed);

  const setAnonymousUsed = useCallback((used: number) => {
    const val = Math.max(0, used);
    setAnonymousUsedStorage(val);
    setUsedState(val);
  }, []);

  const syncFromCreditsRemaining = useCallback(
    (creditsRemaining: number) => {
      const used = ANONYMOUS_LIMIT - creditsRemaining;
      setAnonymousUsed(Math.max(0, used));
    },
    [setAnonymousUsed]
  );

  const resetOnLogin = useCallback(() => {
    removeAnonymousSessionId();
    removeAnonymousUsed();
    setUsedState(0);
  }, []);

  const isAtLimit = anonymousConversionsUsed >= ANONYMOUS_LIMIT;
  const creditsRemaining = Math.max(0, ANONYMOUS_LIMIT - anonymousConversionsUsed);

  return {
    sessionId,
    anonymousConversionsUsed,
    anonymousLimit: ANONYMOUS_LIMIT,
    creditsRemaining,
    isAtLimit,
    syncFromCreditsRemaining,
    resetOnLogin,
    setAnonymousUsed,
  };
}
