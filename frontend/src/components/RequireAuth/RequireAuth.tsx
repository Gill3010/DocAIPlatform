import { useLocation, useNavigate } from 'react-router-dom';
import { useAppStore } from '../../stores/appStore';
import { LoginOverlay } from '../LoginOverlay/LoginOverlay';
import './RequireAuth.css';

interface RequireAuthProps {
    children: React.ReactNode;
}

/** Shows login overlay when not authenticated; protected content when authenticated */
export const RequireAuth = ({ children }: RequireAuthProps) => {
    const { token } = useAppStore();
    const location = useLocation();
    const navigate = useNavigate();

    if (!token) {
        return (
            <>
                <div className="auth-gate-placeholder" aria-live="polite">
                    <p>Inicia sesión para acceder a esta sección</p>
                </div>
                <LoginOverlay
                    from={location.pathname}
                    onClose={() => navigate('/dashboard', { replace: true })}
                />
            </>
        );
    }

    return <>{children}</>;
};
