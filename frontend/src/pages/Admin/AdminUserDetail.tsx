import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { apiService } from '../../services/api';
import { AuthProviderIcon } from '../../components/AuthProviderIcon/AuthProviderIcon';
import './Admin.css';

type UserDetail = {
    id: number;
    email: string;
    full_name: string | null;
    is_active: boolean;
    is_superuser: boolean;
    can_access_admin_panel: boolean;
    can_view_payments: boolean;
    auth_provider: string | null;
    created_at: string | null;
    free_conversion_count: number;
    ai_message_count: number;
    avatar_url: string | null;
    last_conversions: Array<{
        id: number;
        original_filename: string;
        original_format: string;
        target_format: string;
        status: string;
        created_at: string | null;
    }> | null;
};

export const AdminUserDetail = () => {
    const { id } = useParams<{ id: string }>();
    const [user, setUser] = useState<UserDetail | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        const numId = parseInt(id, 10);
        if (Number.isNaN(numId)) return;
        apiService
            .getAdminUser(numId)
            .then(setUser)
            .catch((err) => setError(err instanceof Error ? err.message : 'Error al cargar usuario'));
    }, [id]);

    const handleToggleActive = async () => {
        if (!user || user.is_superuser) return;
        setSaving(true);
        setMessage(null);
        try {
            const updated = await apiService.patchAdminUser(user.id, { is_active: !user.is_active });
            setUser(updated);
            setMessage(updated.is_active ? 'Usuario activado.' : 'Usuario desactivado.');
        } catch (err) {
            setMessage(err instanceof Error ? err.message : 'Error al actualizar');
        } finally {
            setSaving(false);
        }
    };

    const handleToggleAdminPanel = async () => {
        if (!user || user.is_superuser) return;
        setSaving(true);
        setMessage(null);
        try {
            const updated = await apiService.patchAdminUser(user.id, { can_access_admin_panel: !user.can_access_admin_panel });
            setUser(updated);
            setMessage(updated.can_access_admin_panel ? 'Acceso al panel admin concedido.' : 'Acceso al panel admin revocado.');
        } catch (err) {
            setMessage(err instanceof Error ? err.message : 'Error al actualizar');
        } finally {
            setSaving(false);
        }
    };

    const handleTogglePayments = async () => {
        if (!user || user.is_superuser) return;
        setSaving(true);
        setMessage(null);
        try {
            const updated = await apiService.patchAdminUser(user.id, { can_view_payments: !user.can_view_payments });
            setUser(updated);
            setMessage(updated.can_view_payments ? 'Permiso para ver pagos concedido.' : 'Permiso para ver pagos revocado.');
        } catch (err) {
            setMessage(err instanceof Error ? err.message : 'Error al actualizar');
        } finally {
            setSaving(false);
        }
    };

    if (!id) return <div className="admin-page"><p>ID no válido.</p></div>;
    if (error) return <div className="admin-page"><p className="admin-error">{error}</p><Link to="/admin">← Volver al panel</Link></div>;
    if (!user) return <div className="admin-page"><p>Cargando…</p></div>;

    return (
        <div className="admin-page">
            <h1>Detalle de usuario</h1>
            <p>
                <Link to="/admin">← Volver al panel</Link>
            </p>
            {message && <p className="admin-message">{message}</p>}
            <section className="admin-section admin-detail-section">
                <dl className="admin-detail-dl">
                    <dt>Email</dt>
                    <dd>{user.email}</dd>
                    <dt>Nombre</dt>
                    <dd>{user.full_name ?? '—'}</dd>
                    <dt>Estado</dt>
                    <dd>{user.is_active ? 'Activo' : 'Inactivo'}</dd>
                    <dt>Método de registro</dt>
                    <dd><AuthProviderIcon provider={user.auth_provider} size={20} /></dd>
                    <dt>Superadmin</dt>
                    <dd>{user.is_superuser ? 'Sí' : 'No'}</dd>
                    <dt>Acceso panel admin</dt>
                    <dd>{user.can_access_admin_panel ? 'Sí' : 'No'}</dd>
                    <dt>Ver pagos</dt>
                    <dd>{user.can_view_payments ? 'Sí' : 'No'}</dd>
                    <dt>Créditos conversión usados</dt>
                    <dd>{user.free_conversion_count}</dd>
                    <dt>Mensajes IA usados</dt>
                    <dd>{user.ai_message_count}</dd>
                    <dt>Registro</dt>
                    <dd>{user.created_at ? new Date(user.created_at).toLocaleString() : '—'}</dd>
                </dl>
                {!user.is_superuser && (
                    <div className="admin-detail-actions">
                        <button
                            type="button"
                            onClick={handleToggleActive}
                            disabled={saving}
                            className="admin-btn"
                        >
                            {user.is_active ? 'Desactivar usuario' : 'Activar usuario'}
                        </button>
                        <button
                            type="button"
                            onClick={handleToggleAdminPanel}
                            disabled={saving}
                            className="admin-btn"
                        >
                            {user.can_access_admin_panel ? 'Revocar acceso admin' : 'Dar acceso al panel admin'}
                        </button>
                        <button
                            type="button"
                            onClick={handleTogglePayments}
                            disabled={saving}
                            className="admin-btn"
                        >
                            {user.can_view_payments ? 'Quitar permiso pagos' : 'Permitir ver pagos'}
                        </button>
                    </div>
                )}
            </section>
            {user.last_conversions && user.last_conversions.length > 0 && (
                <section className="admin-section">
                    <h2>Últimas conversiones</h2>
                    <div className="admin-table-wrap">
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>Archivo</th>
                                    <th>Formato</th>
                                    <th>Estado</th>
                                    <th>Fecha</th>
                                </tr>
                            </thead>
                            <tbody>
                                {user.last_conversions.map((c) => (
                                    <tr key={c.id}>
                                        <td>{c.original_filename}</td>
                                        <td>{c.original_format} → {c.target_format}</td>
                                        <td>{c.status}</td>
                                        <td>{c.created_at ? new Date(c.created_at).toLocaleString() : '—'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            )}
        </div>
    );
};
