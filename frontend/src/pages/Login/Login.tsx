import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ThemeToggle } from '../../components/ThemeToggle/ThemeToggle';
import { LoginForm } from '../../components/LoginForm/LoginForm';
import { setPendingAnonymousSessionId } from '../../services/storageService';
import './Login.css';

export const Login = () => {
    const location = useLocation();
    const state = location.state as { mode?: string; anonymousSessionId?: string } | null;
    const [displayMode, setDisplayMode] = useState<'login' | 'register'>(state?.mode !== 'register' ? 'login' : 'register');

    useEffect(() => {
        const anonFromState = state?.anonymousSessionId;
        if (anonFromState) setPendingAnonymousSessionId(anonFromState);
    }, [state?.anonymousSessionId]);

    return (
        <div className={`login-container ${displayMode === 'login' ? 'login-mode' : 'register-mode'}`}>
            <div className="theme-toggle-wrapper">
                <ThemeToggle />
            </div>
            <div className="login-card">
                <LoginForm
                    initialMode={state?.mode !== 'register' ? 'login' : 'register'}
                    anonymousSessionId={state?.anonymousSessionId ?? null}
                    onSuccessRedirect="/dashboard"
                    onModeChange={(isLogin) => setDisplayMode(isLogin ? 'login' : 'register')}
                    showBackToDashboard
                />
            </div>
        </div>
    );
};
