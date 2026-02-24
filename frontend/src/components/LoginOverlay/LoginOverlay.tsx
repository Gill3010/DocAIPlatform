import { useEffect, useRef, useCallback, useState } from 'react';
import { X } from 'lucide-react';
import { LoginForm } from '../LoginForm/LoginForm';
import { ForgotPasswordForm } from '../ForgotPasswordForm/ForgotPasswordForm';
import { getStoredSessionId } from '../../utils/anonymousSession';
import './LoginOverlay.css';

type OverlayView = 'login' | 'register' | 'forgot-password';

const CONTEXT_MESSAGES: Record<string, string> = {
    '/history': 'Inicia sesión para ver tu historial de conversiones',
    '/documents': 'Inicia sesión para acceder a tus documentos',
    '/settings': 'Inicia sesión para editar tu perfil',
    '/pricing': 'Inicia sesión para elegir tu plan',
};

function getContextMessage(pathname: string, mode: 'login' | 'register' | 'forgot-password'): string {
    if (mode === 'register') {
        if (CONTEXT_MESSAGES[pathname]) return CONTEXT_MESSAGES[pathname].replace('Inicia sesión', 'Crea una cuenta');
        if (pathname.startsWith('/collab/')) return 'Crea una cuenta para acceder a este documento';
        return 'Crea una cuenta para continuar';
    }
    if (mode === 'forgot-password') {
        return 'Ingresa tu correo y te enviaremos un enlace para restablecer tu contraseña.';
    }
    if (CONTEXT_MESSAGES[pathname]) return CONTEXT_MESSAGES[pathname];
    if (pathname.startsWith('/collab/')) return 'Inicia sesión para acceder a este documento';
    return 'Inicia sesión para continuar';
}

interface LoginOverlayProps {
    /** Path the user was trying to access */
    from: string;
    onClose: () => void;
    /** 'login' | 'register' - defaults to 'login' */
    initialMode?: 'login' | 'register';
    /** Called after successful login (e.g. to close overlay) */
    onSuccess?: () => void;
}

export const LoginOverlay = ({ from, onClose, initialMode = 'login', onSuccess }: LoginOverlayProps) => {
    const modalRef = useRef<HTMLDivElement>(null);
    const [view, setView] = useState<OverlayView>(initialMode === 'register' ? 'register' : 'login');

    const handleClose = useCallback(() => {
        onClose();
    }, [onClose]);

    const showForgotPassword = useCallback(() => setView('forgot-password'), []);
    const showLogin = useCallback(() => setView('login'), []);

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') handleClose();
        };
        window.addEventListener('keydown', handleEscape);
        return () => window.removeEventListener('keydown', handleEscape);
    }, [handleClose]);

    useEffect(() => {
        const modal = modalRef.current;
        if (!modal) return;
        const focusable = modal.querySelectorAll<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const first = focusable[0];
        if (first) {
            const t = setTimeout(() => first.focus(), 100);
            return () => clearTimeout(t);
        }
    }, []);

    useEffect(() => {
        const prev = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = prev;
        };
    }, []);

    return (
        <div
            className="login-overlay-backdrop"
            onClick={handleClose}
            role="presentation"
        >
            <div
                ref={modalRef}
                className="login-overlay-modal"
                onClick={(e) => e.stopPropagation()}
                role="dialog"
                aria-labelledby="login-overlay-title"
                aria-describedby="login-overlay-desc"
                aria-modal="true"
            >
                <p id="login-overlay-desc" className="visually-hidden">
                    {getContextMessage(from, view)}
                </p>
                <h2 id="login-overlay-title" className="visually-hidden">
                    {view === 'forgot-password' ? 'Restablecer contraseña' : 'Iniciar sesión'}
                </h2>
                <div className="login-overlay-card">
                    <button
                        type="button"
                        className="login-overlay-close"
                        onClick={handleClose}
                        aria-label="Cerrar y continuar sin iniciar sesión"
                    >
                        <X size={22} aria-hidden />
                    </button>
                    <p className="login-overlay-hint">{getContextMessage(from, view)}</p>
                    {view === 'forgot-password' ? (
                        <ForgotPasswordForm idPrefix="login-overlay-forgot" onBack={showLogin} />
                    ) : (
                        <LoginForm
                            idPrefix="login-overlay"
                            initialMode={view}
                            anonymousSessionId={getStoredSessionId()}
                            onSuccessRedirect={false}
                            onSuccess={onSuccess ?? (() => {})}
                            onForgotPasswordClick={showForgotPassword}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};
