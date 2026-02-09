import { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAppStore } from '../../stores/appStore';
import { apiService } from '../../services/api';

interface RequireAdminProps {
    children: React.ReactNode;
}

/**
 * Redirige a /login si no hay token; a /dashboard si el usuario no es admin.
 * Si hay token pero user aún no cargado, obtiene el perfil y comprueba is_superuser o can_access_admin_panel.
 */
export const RequireAdmin = ({ children }: RequireAdminProps) => {
    const { token, user, setUser } = useAppStore();
    const location = useLocation();

    useEffect(() => {
        if (!token || user !== null) return;
        apiService
            .getProfile()
            .then((profile) => setUser(profile))
            .catch(() => {});
    }, [token, user, setUser]);

    if (!token) {
        return <Navigate to="/login" state={{ from: location.pathname }} replace />;
    }

    if (token && user === null) {
        return (
            <div className="require-admin-loading" style={{ padding: '2rem', textAlign: 'center' }}>
                Comprobando acceso…
            </div>
        );
    }

    const isAdmin = user?.is_superuser === true || user?.can_access_admin_panel === true;
    if (!isAdmin) {
        return <Navigate to="/dashboard" replace />;
    }

    return <>{children}</>;
};
