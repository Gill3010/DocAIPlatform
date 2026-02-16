import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../../services/api';
import { useAppStore } from '../../stores/appStore';
import { AuthProviderIcon } from '../../components/AuthProviderIcon/AuthProviderIcon';
import './Admin.css';

type AdminUserItem = {
    id: number;
    email: string;
    full_name: string | null;
    is_active: boolean;
    is_superuser: boolean;
    can_access_admin_panel: boolean;
    can_view_payments: boolean;
    auth_provider: string | null;
    created_at: string | null;
};

export const Admin = () => {
    const { user: currentUser } = useAppStore();
    const [stats, setStats] = useState<{
        users: { total: number; active: number };
        conversions: { total: number; completed: number };
    } | null>(null);
    const [users, setUsers] = useState<{ items: AdminUserItem[]; total: number; page: number; size: number; pages: number } | null>(null);
    const [page, setPage] = useState(1);
    const [emailFilter, setEmailFilter] = useState('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        apiService
            .getAdminStats()
            .then(setStats)
            .catch((err) => setError(err instanceof Error ? err.message : 'Error al cargar estadísticas'));
    }, []);

    useEffect(() => {
        apiService
            .getAdminUsers({ page, size: 15, email: emailFilter || undefined })
            .then(setUsers)
            .catch(() => setUsers(null));
    }, [page, emailFilter]);

    const canSeePayments = currentUser?.is_superuser || currentUser?.can_view_payments;

    return (
        <div className="admin-page">
            <h1>Panel de administración</h1>
            <p className="admin-nav-links">
                <Link to="/dashboard">← Volver al dashboard</Link>
                <span className="admin-nav-sep">·</span>
                <Link to="/admin/conversions">Conversiones</Link>
                {canSeePayments && (
                    <>
                        <span className="admin-nav-sep">·</span>
                        <Link to="/admin/payments">Pagos</Link>
                    </>
                )}
                <span className="admin-nav-sep">·</span>
                <Link to="/admin/activity">Actividad</Link>
            </p>
            {error && <p className="admin-error">{error}</p>}
            {stats && (
                <section className="admin-section admin-section--resumen">
                    <h2 className="admin-section__title">Resumen</h2>
                    <div className="admin-stats">
                        <div className="admin-stat-card admin-stat-card--primary">
                            <h3>Usuarios totales</h3>
                            <span className="admin-stat-card__value">{stats.users.total}</span>
                        </div>
                        <div className="admin-stat-card admin-stat-card--success">
                            <h3>Usuarios activos</h3>
                            <span className="admin-stat-card__value">{stats.users.active}</span>
                        </div>
                        <div className="admin-stat-card admin-stat-card--info">
                            <h3>Conversiones totales</h3>
                            <span className="admin-stat-card__value">{stats.conversions.total}</span>
                        </div>
                        <div className="admin-stat-card admin-stat-card--warning">
                            <h3>Conversiones completadas</h3>
                            <span className="admin-stat-card__value">{stats.conversions.completed}</span>
                        </div>
                    </div>
                </section>
            )}
            <section className="admin-section admin-section--users">
                <h2 className="admin-section__title">Usuarios</h2>
                <div className="admin-users-toolbar">
                    <input
                        type="text"
                        placeholder="Filtrar por email"
                        value={emailFilter}
                        onChange={(e) => { setEmailFilter(e.target.value); setPage(1); }}
                        className="admin-filter-input"
                    />
                </div>
                {users && (
                    <>
                        <div className="admin-table-wrap">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Email</th>
                                        <th>Nombre</th>
                                        <th>Estado</th>
                                        <th>Registro</th>
                                        <th>Admin</th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.items.map((u) => (
                                        <tr key={u.id}>
                                            <td className="admin-table__id">{u.id}</td>
                                            <td>{u.email}</td>
                                            <td>{u.full_name ?? '—'}</td>
                                            <td>{u.is_active ? 'Activo' : 'Inactivo'}</td>
                                            <td><AuthProviderIcon provider={u.auth_provider} size={18} /></td>
                                            <td>{u.is_superuser ? 'Superadmin' : u.can_access_admin_panel ? 'Sí' : 'No'}</td>
                                            <td>
                                                <Link to={`/admin/users/${u.id}`} className="admin-link">Ver detalle</Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        <div className="admin-pagination">
                            <button
                                type="button"
                                disabled={page <= 1}
                                onClick={() => setPage((p) => p - 1)}
                            >
                                Anterior
                            </button>
                            <span>Página {page} de {users.pages || 1}</span>
                            <button
                                type="button"
                                disabled={page >= users.pages}
                                onClick={() => setPage((p) => p + 1)}
                            >
                                Siguiente
                            </button>
                        </div>
                    </>
                )}
            </section>
        </div>
    );
};
