import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { apiService } from '../../services/api';
import { useAppStore } from '../../stores/appStore';
import { setToken as setStorageToken, getPendingAnonymousSessionId, removePendingAnonymousSessionId, getCheckoutIntent } from '../../services/storageService';
import { clearAnonymousSession, getStoredSessionId } from '../../utils/anonymousSession';
import './AuthCallback.css';

/**
 * Página que recibe el redirect de Facebook OAuth.
 * Lee code y state de la URL, los envía al backend y redirige al dashboard.
 */
export const AuthCallbackFacebook = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { setToken, setUser } = useAppStore();
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const errorParam = searchParams.get('error');

        if (errorParam) {
            if (errorParam === 'access_denied') {
                setError('Cancelaste el inicio de sesión. Intenta de nuevo.');
            } else {
                setError('Ocurrió un error con Facebook. Intenta de nuevo.');
            }
            return;
        }

        if (!code || !state) {
            setError('Faltan datos de autorización. Vuelve a intentar.');
            return;
        }

        const redirectUri = `${window.location.origin}/auth/callback/facebook`;

        apiService
            .facebookAuth({ code, state, redirect_uri: redirectUri })
            .then(async (response) => {
                setToken(response.access_token);
                setStorageToken(response.access_token);

                const sessionId = getPendingAnonymousSessionId() ?? getStoredSessionId();
                if (sessionId) {
                    try {
                        await apiService.linkAnonymousSession(sessionId);
                    } catch {
                        // ignore
                    }
                }
                clearAnonymousSession();
                removePendingAnonymousSessionId();

                apiService
                    .getProfile()
                    .then((profile) => setUser(profile))
                    .catch(() => {});
                const hasCheckoutIntent = getCheckoutIntent() !== null;
                navigate(hasCheckoutIntent ? '/pricing' : '/dashboard', { replace: true });
            })
            .catch((err) => {
                const msg = err instanceof Error ? err.message : 'Error al iniciar sesión con Facebook';
                setError(msg);
            });
    }, [searchParams, setToken, setUser, navigate]);

    if (error) {
        return (
            <div className="auth-callback auth-callback--error">
                <div className="auth-callback-card">
                    <p className="auth-callback-message">{error}</p>
                    <button
                        type="button"
                        className="auth-callback-retry"
                        onClick={() => navigate('/login', { replace: true })}
                    >
                        Volver al inicio de sesión
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="auth-callback">
            <div className="auth-callback-card">
                <div className="auth-callback-spinner" aria-hidden />
                <p className="auth-callback-message">Iniciando sesión con Facebook...</p>
            </div>
        </div>
    );
};
