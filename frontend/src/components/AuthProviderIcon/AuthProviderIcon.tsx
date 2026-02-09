import { Mail } from 'lucide-react';
import './AuthProviderIcon.css';

type Provider = 'email' | 'google' | 'facebook' | string | null | undefined;

interface AuthProviderIconProps {
    provider: Provider;
    showLabel?: boolean;
    size?: number;
}

/** Icono del método de registro (email, Google, Facebook) para listados admin */
export const AuthProviderIcon = ({ provider: raw, showLabel = true, size = 20 }: AuthProviderIconProps) => {
    const provider = (raw ?? 'email').toLowerCase();

    if (provider === 'google') {
        return (
            <span className="auth-provider auth-provider--google" title="Google">
                <span className="auth-provider__icon" aria-hidden>
                    <svg width={size} height={size} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                </span>
                {showLabel && <span className="auth-provider__label">Google</span>}
            </span>
        );
    }

    if (provider === 'facebook') {
        return (
            <span className="auth-provider auth-provider--facebook" title="Facebook">
                <span className="auth-provider__icon auth-provider__icon--facebook" aria-hidden>
                    <svg width={size} height={size} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" focusable="false">
                        <path fill="#1877F2" d="M12 2C6.477 2 2 6.477 2 12c0 5.01 3.657 9.162 8.438 9.879V14.89h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.989C18.343 21.162 22 17.01 22 12c0-5.523-4.477-10-10-10z" />
                        <path fill="#fff" d="M15.834 14.89l.443-2.89h-2.773v-1.875c0-.791.387-1.562 1.63-1.562h1.26V8.002s-1.144-.195-2.238-.195c-2.285 0-3.777 1.384-3.777 3.89V12h-2.54v2.89h2.54v6.989a10.058 10.058 0 002.5-.312v-6.677h2.33z" />
                    </svg>
                </span>
                {showLabel && <span className="auth-provider__label">Facebook</span>}
            </span>
        );
    }

    return (
        <span className="auth-provider auth-provider--email" title="Email">
            <span className="auth-provider__icon" aria-hidden>
                <Mail size={size} strokeWidth={2} />
            </span>
            {showLabel && <span className="auth-provider__label">Email</span>}
        </span>
    );
};
