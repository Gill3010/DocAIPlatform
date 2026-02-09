import { Navigate, useLocation } from 'react-router-dom';
import { useAppStore } from '../../stores/appStore';

interface RequireAuthProps {
    children: React.ReactNode;
}

/** Redirects to /login if user is not authenticated */
export const RequireAuth = ({ children }: RequireAuthProps) => {
    const { token } = useAppStore();
    const location = useLocation();

    if (!token) {
        return <Navigate to="/login" state={{ from: location.pathname }} replace />;
    }

    return <>{children}</>;
};
