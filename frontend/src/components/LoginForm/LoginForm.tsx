import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, LogIn, UserPlus } from 'lucide-react';
import { apiService, ApiError } from '../../services/api';
import { useAppStore } from '../../stores/appStore';
import {
    setPendingAnonymousSessionId,
    getPendingAnonymousSessionId,
    removePendingAnonymousSessionId,
    setToken as setStorageToken,
} from '../../services/storageService';
import { clearAnonymousSession, getStoredSessionId } from '../../utils/anonymousSession';
import '../../pages/Login/Login.css';

const FacebookIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="#1877F2" aria-hidden>
        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
    </svg>
);

const GoogleIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden>
        <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        />
        <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
    </svg>
);

const PASSWORD_REQUIREMENTS = ['Mínimo 8 caracteres', 'Al menos una letra'];

const TURNSTILE_SITE_KEY = typeof import.meta !== 'undefined' ? (import.meta.env?.VITE_TURNSTILE_SITE_KEY as string | undefined) : undefined;

export interface LoginFormProps {
    /** 'login' | 'register' */
    initialMode?: 'login' | 'register';
    /** Anonymous session ID to link after login (e.g. from ConversionLimitModal) */
    anonymousSessionId?: string | null;
    /** Route to navigate on success. If false, no navigation (e.g. modal mode). */
    onSuccessRedirect?: string | false;
    /** Called after successful login when onSuccessRedirect is false */
    onSuccess?: () => void;
    /** Prefix for form control ids (avoids duplicates when form is in overlay) */
    idPrefix?: string;
    /** Called when user switches between login/register (e.g. for container styling) */
    onModeChange?: (isLogin: boolean) => void;
    /** Show "Ir al Dashboard" link in register mode (full page only, not overlay) */
    showBackToDashboard?: boolean;
}

export const LoginForm = ({
    initialMode = 'login',
    anonymousSessionId: anonFromProp,
    onSuccessRedirect = '/dashboard',
    onSuccess,
    idPrefix = 'login',
    onModeChange,
    showBackToDashboard = false,
}: LoginFormProps) => {
    const navigate = useNavigate();
    const { setToken, setUser } = useAppStore();
    const [isLogin, setIsLogin] = useState(initialMode === 'login');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [googleLoading, setGoogleLoading] = useState(false);
    const [facebookLoading, setFacebookLoading] = useState(false);
    const [googleAvailable, setGoogleAvailable] = useState<boolean | null>(null);
    const [facebookAvailable, setFacebookAvailable] = useState<boolean | null>(null);

    const [confirmPasswordTouched, setConfirmPasswordTouched] = useState(false);
    const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
    const turnstileContainerRef = useRef<HTMLDivElement>(null);
    const turnstileWidgetIdRef = useRef<string | null>(null);

    const passwordsMatch = confirmPassword === password;
    const showPasswordMatchError = !isLogin && confirmPasswordTouched && confirmPassword.length > 0 && !passwordsMatch;
    const showPasswordMatchSuccess = !isLogin && confirmPasswordTouched && confirmPassword.length > 0 && passwordsMatch;

    const sessionId = anonFromProp ?? getPendingAnonymousSessionId() ?? getStoredSessionId();

    useEffect(() => {
        if (anonFromProp) setPendingAnonymousSessionId(anonFromProp);
    }, [anonFromProp]);

    const handleGoogleLogin = async () => {
        setError('');
        setGoogleLoading(true);
        try {
            if (sessionId) {
                try {
                    setPendingAnonymousSessionId(sessionId);
                } catch {
                    // ignore
                }
            }
            const redirectUri = `${window.location.origin}/auth/callback`;
            const { url } = await apiService.getGoogleAuthUrl(redirectUri);
            window.location.href = url;
        } catch (err) {
            setGoogleLoading(false);
            const msg = err instanceof ApiError ? err.detail : err instanceof Error ? err.message : 'Google no está configurado';
            setError(msg);
        }
    };

    const handleFacebookLogin = async () => {
        setError('');
        setFacebookLoading(true);
        try {
            if (sessionId) setPendingAnonymousSessionId(sessionId);
            const redirectUri = `${window.location.origin}/auth/callback/facebook`;
            const { url } = await apiService.getFacebookAuthUrl(redirectUri);
            window.location.href = url;
        } catch (err) {
            setFacebookLoading(false);
            const msg = err instanceof ApiError ? err.detail : err instanceof Error ? err.message : 'Facebook no está configurado';
            setError(msg);
        }
    };

    useEffect(() => {
        if (googleAvailable === null) {
            apiService.getGoogleAuthUrl().then(() => setGoogleAvailable(true)).catch(() => setGoogleAvailable(false));
        }
    }, [googleAvailable]);

    useEffect(() => {
        if (facebookAvailable === null) {
            apiService.getFacebookAuthUrl().then(() => setFacebookAvailable(true)).catch(() => setFacebookAvailable(false));
        }
    }, [facebookAvailable]);

    const switchMode = () => {
        const next = !isLogin;
        setIsLogin(next);
        setError('');
        setConfirmPassword('');
        setShowPassword(false);
        setShowConfirmPassword(false);
        setConfirmPasswordTouched(false);
        setTurnstileToken(null);
        if (TURNSTILE_SITE_KEY && turnstileWidgetIdRef.current != null && typeof window !== 'undefined' && (window as Window & { turnstile?: { reset: (id: string) => void } }).turnstile) {
            (window as Window & { turnstile: { reset: (id: string) => void } }).turnstile.reset(turnstileWidgetIdRef.current);
        }
        onModeChange?.(next);
    };

    useEffect(() => {
        if (!TURNSTILE_SITE_KEY) return;

        const renderTurnstile = (): boolean => {
            const win = window as Window & { turnstile?: { render: (el: HTMLElement, opts: Record<string, unknown>) => string } };
            if (!win.turnstile || !turnstileContainerRef.current) return false;
            const widgetId = win.turnstile.render(turnstileContainerRef.current, {
                sitekey: TURNSTILE_SITE_KEY,
                callback: (token: string) => setTurnstileToken(token),
                'expired-callback': () => setTurnstileToken(null),
                'error-callback': () => setTurnstileToken(null),
            });
            turnstileWidgetIdRef.current = widgetId;
            return true;
        };

        let intervalId: ReturnType<typeof setInterval> | null = null;
        if ((window as Window & { turnstile?: unknown }).turnstile) {
            renderTurnstile();
        } else {
            intervalId = window.setInterval(() => {
                if (renderTurnstile()) {
                    if (intervalId) window.clearInterval(intervalId);
                }
            }, 50);
        }

        return () => {
            if (intervalId) window.clearInterval(intervalId);
            if (turnstileWidgetIdRef.current != null) {
                const win = window as Window & { turnstile?: { remove: (id: string) => void } };
                if (win.turnstile) win.turnstile.remove(turnstileWidgetIdRef.current!);
                turnstileWidgetIdRef.current = null;
            }
        };
    }, []);

    const completeLogin = async () => {
        if (sessionId) {
            try {
                await apiService.linkAnonymousSession(sessionId);
            } catch {
                // link failed, getUserStats will have current state
            }
        }
        clearAnonymousSession();
        removePendingAnonymousSessionId();
        try {
            const profile = await apiService.getProfile();
            setUser(profile);
        } catch (err) {
            console.error('Failed to fetch user data:', err);
        }
        if (onSuccessRedirect !== false) {
            navigate(onSuccessRedirect);
        } else {
            onSuccess?.();
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        if (!isLogin && password !== confirmPassword) {
            setError('Las contraseñas no coinciden');
            setLoading(false);
            return;
        }

        if (TURNSTILE_SITE_KEY && !turnstileToken) {
            setError('Por favor, verifica que eres humano (captcha) antes de continuar.');
            setLoading(false);
            return;
        }

        try {
            const turnstile = turnstileToken || undefined;
            if (isLogin) {
                const response = await apiService.login({ username: email, password, turnstile_token: turnstile });
                setToken(response.access_token);
                setStorageToken(response.access_token);
                await completeLogin();
            } else {
                await apiService.register({ email, password, full_name: fullName, turnstile_token: turnstile });
                const response = await apiService.login({ username: email, password, turnstile_token: turnstile });
                setToken(response.access_token);
                setStorageToken(response.access_token);
                await completeLogin();
            }
        } catch (err) {
            const message = err instanceof ApiError ? err.detail : err instanceof Error ? err.message : 'Ocurrió un error';
            setError(
                message.includes('already registered')
                    ? 'Este correo ya está registrado. Inicia sesión o usa otro email.'
                    : message.includes('Incorrect')
                      ? 'Email o contraseña incorrectos. Verifica tus credenciales.'
                      : message
            );
            setTurnstileToken(null);
            if (TURNSTILE_SITE_KEY && turnstileWidgetIdRef.current != null && typeof window !== 'undefined' && (window as Window & { turnstile?: { reset: (id: string) => void } }).turnstile) {
                (window as Window & { turnstile: { reset: (id: string) => void } }).turnstile.reset(turnstileWidgetIdRef.current);
            }
        } finally {
            setLoading(false);
        }
    };

    const emailId = `${idPrefix}-email`;
    const fullNameId = `${idPrefix}-fullName`;
    const passwordId = `${idPrefix}-password`;
    const confirmPasswordId = `${idPrefix}-confirmPassword`;

    return (
        <div className={`login-form-wrapper ${isLogin ? 'login-mode' : 'register-mode'}`}>
            <div className={`login-header ${isLogin ? 'login-header--login' : 'login-header--register'}`}>
                <div className="login-header-icon">
                    {isLogin ? <LogIn size={40} strokeWidth={2} aria-hidden /> : <UserPlus size={40} strokeWidth={2} aria-hidden />}
                </div>
                <h2 className="login-title">
                    {isLogin ? 'Iniciar sesión' : 'Crear cuenta'}
                </h2>
                <p className="login-description">
                    {isLogin ? 'Ingresa tus credenciales para acceder a tu cuenta' : 'Completa el formulario para registrarte'}
                </p>
            </div>

            {error && (
                <div className="login-error" role="alert">
                    {error}
                </div>
            )}

            {(googleAvailable || facebookAvailable) && (
                <div className="login-social">
                    {googleAvailable && (
                        <button
                            type="button"
                            className="btn-social btn-google"
                            onClick={handleGoogleLogin}
                            disabled={loading || googleLoading || facebookLoading}
                            aria-label="Continuar con Google"
                        >
                            <GoogleIcon />
                            {googleLoading ? 'Redirigiendo...' : 'Continuar con Google'}
                        </button>
                    )}
                    {facebookAvailable && (
                        <button
                            type="button"
                            className="btn-social btn-facebook"
                            onClick={handleFacebookLogin}
                            disabled={loading || googleLoading || facebookLoading}
                            aria-label="Continuar con Facebook"
                        >
                            <FacebookIcon />
                            {facebookLoading ? 'Redirigiendo...' : 'Continuar con Facebook'}
                        </button>
                    )}
                </div>
            )}

            {(googleAvailable || facebookAvailable) && <p className="login-separator">o continúa con email</p>}

            <form onSubmit={handleSubmit} className="login-form" noValidate>
                <div className="form-group">
                    <label htmlFor={emailId}>{isLogin ? 'Email o Usuario' : 'Email'}</label>
                    <input
                        id={emailId}
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="tu@email.com"
                        required
                        autoComplete={isLogin ? 'username' : 'email'}
                        aria-describedby={error ? 'login-error' : undefined}
                    />
                </div>

                {!isLogin && (
                    <div className="form-group">
                        <label htmlFor={fullNameId}>Nombre</label>
                        <input
                            id={fullNameId}
                            type="text"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            placeholder="Tu nombre completo"
                            autoComplete="name"
                        />
                    </div>
                )}

                <div className="form-group">
                    <label htmlFor={passwordId}>Contraseña</label>
                    <div className="password-input-wrapper">
                        <input
                            id={passwordId}
                            type={showPassword ? 'text' : 'password'}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            autoComplete={isLogin ? 'current-password' : 'new-password'}
                        />
                        <button
                            type="button"
                            className="password-toggle"
                            onClick={() => setShowPassword(!showPassword)}
                            tabIndex={-1}
                            title={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                            aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                        >
                            {showPassword ? <EyeOff size={20} aria-hidden /> : <Eye size={20} aria-hidden />}
                        </button>
                    </div>
                </div>

                {!isLogin && (
                    <>
                        <div className="form-group">
                            <label htmlFor={confirmPasswordId}>Confirmar contraseña</label>
                            <div className="password-input-wrapper">
                                <input
                                    id={confirmPasswordId}
                                    type={showConfirmPassword ? 'text' : 'password'}
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    onBlur={() => setConfirmPasswordTouched(true)}
                                    placeholder="••••••••"
                                    required={!isLogin}
                                    autoComplete="new-password"
                                    aria-invalid={showPasswordMatchError}
                                    aria-describedby={
                                        showPasswordMatchError
                                            ? 'confirm-password-error'
                                            : showPasswordMatchSuccess
                                              ? 'confirm-password-success'
                                              : undefined
                                    }
                                />
                                <button
                                    type="button"
                                    className="password-toggle"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    tabIndex={-1}
                                    title={showConfirmPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                                    aria-label={showConfirmPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                                >
                                    {showConfirmPassword ? <EyeOff size={20} aria-hidden /> : <Eye size={20} aria-hidden />}
                                </button>
                            </div>
                            {showPasswordMatchError && (
                                <p id="confirm-password-error" className="form-message form-message--error" role="alert">
                                    Las contraseñas no coinciden
                                </p>
                            )}
                            {showPasswordMatchSuccess && (
                                <p id="confirm-password-success" className="form-message form-message--success">
                                    Las contraseñas coinciden
                                </p>
                            )}
                        </div>

                        <div className="password-requirements">
                            <p className="password-requirements-title">Requisitos de contraseña:</p>
                            <ul>
                                {PASSWORD_REQUIREMENTS.map((req) => (
                                    <li key={req}>{req}</li>
                                ))}
                            </ul>
                        </div>
                    </>
                )}

                {TURNSTILE_SITE_KEY && (
                    <div className="form-group turnstile-container">
                        <div ref={turnstileContainerRef} id={`${idPrefix}-turnstile`} aria-label="Verificación de seguridad" />
                    </div>
                )}

                <button
                    type="submit"
                    className="btn-primary"
                    disabled={loading || (!isLogin && confirmPassword.length > 0 && !passwordsMatch) || (!!TURNSTILE_SITE_KEY && !turnstileToken)}
                >
                    {loading ? 'Por favor espera...' : isLogin ? 'Iniciar sesión' : 'Crear cuenta'}
                </button>
            </form>

            <div className="login-footer">
                <p>
                    {isLogin ? '¿No tienes cuenta? ' : '¿Ya tienes cuenta? '}
                    <button type="button" className="link-button" onClick={switchMode}>
                        {isLogin ? 'Regístrate' : 'Inicia sesión'}
                    </button>
                </p>
                {!isLogin && showBackToDashboard && (
                    <p className="login-footer-back">
                        <Link to="/dashboard" className="link-button link-button--back">
                            ← Volver al Dashboard
                        </Link>
                    </p>
                )}
            </div>
        </div>
    );
};
