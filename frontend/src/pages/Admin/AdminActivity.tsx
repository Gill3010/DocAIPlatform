import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../../services/api';
import './Admin.css';

type ActivityItem = {
    id: number;
    admin_user_id: number;
    action: string;
    resource_type: string;
    resource_id: string | null;
    details: string | null;
    created_at: string | null;
};

export const AdminActivity = () => {
    const [data, setData] = useState<{
        items: ActivityItem[];
        total: number;
        page: number;
        size: number;
        pages: number;
    } | null>(null);
    const [page, setPage] = useState(1);
    const [actionFilter, setActionFilter] = useState('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        apiService
            .getAdminActivity({ page, size: 25, action: actionFilter || undefined })
            .then(setData)
            .catch((err) => {
                setError(err instanceof Error ? err.message : 'Error');
                setData(null);
            });
    }, [page, actionFilter]);

    return (
        <div className="admin-page">
            <h1>Actividad del panel</h1>
            <p className="admin-nav-links">
                <Link to="/admin">← Panel</Link>
                <span className="admin-nav-sep">·</span>
                <Link to="/admin/conversions">Conversiones</Link>
            </p>
            {error && <p className="admin-error">{error}</p>}
            <section className="admin-section">
            <div className="admin-users-toolbar">
                <select
                    value={actionFilter}
                    onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
                    className="admin-filter-input"
                    style={{ width: '180px' }}
                >
                    <option value="">Todas las acciones</option>
                    <option value="user_activate">user_activate</option>
                    <option value="user_deactivate">user_deactivate</option>
                    <option value="admin_assign">admin_assign</option>
                    <option value="admin_revoke">admin_revoke</option>
                </select>
            </div>
            {data && (
                <>
                    <div className="admin-table-wrap">
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Admin user ID</th>
                                    <th>Acción</th>
                                    <th>Recurso</th>
                                    <th>Detalles</th>
                                    <th>Fecha</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.items.map((log) => (
                                    <tr key={log.id}>
                                        <td>{log.id}</td>
                                        <td>{log.admin_user_id}</td>
                                        <td>{log.action}</td>
                                        <td>{log.resource_type}{log.resource_id ? ` #${log.resource_id}` : ''}</td>
                                        <td>{log.details ?? '—'}</td>
                                        <td>{log.created_at ? new Date(log.created_at).toLocaleString() : '—'}</td>
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
                        <span>Página {page} de {data.pages || 1} ({data.total} total)</span>
                        <button
                            type="button"
                            disabled={page >= data.pages}
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
