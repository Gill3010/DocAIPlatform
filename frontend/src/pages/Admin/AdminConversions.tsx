import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../../services/api';
import './Admin.css';

type ConversionItem = {
    id: number;
    user_id: number | null;
    anonymous_session_id: string | null;
    original_filename: string;
    original_format: string;
    target_format: string;
    status: string;
    file_size: number | null;
    created_at: string | null;
    completed_at: string | null;
};

export const AdminConversions = () => {
    const [data, setData] = useState<{
        items: ConversionItem[];
        total: number;
        page: number;
        size: number;
        pages: number;
    } | null>(null);
    const [page, setPage] = useState(1);
    const [statusFilter, setStatusFilter] = useState('');
    const [userIdFilter, setUserIdFilter] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const params: Parameters<typeof apiService.getAdminConversions>[0] = {
            page,
            size: 20,
        };
        if (statusFilter) params.status = statusFilter;
        const uid = parseInt(userIdFilter, 10);
        if (userIdFilter && !Number.isNaN(uid)) params.user_id = uid;
        if (dateFrom) params.date_from = dateFrom;
        if (dateTo) params.date_to = dateTo;
        apiService
            .getAdminConversions(params)
            .then(setData)
            .catch((err) => {
                setError(err instanceof Error ? err.message : 'Error');
                setData(null);
            });
    }, [page, statusFilter, userIdFilter, dateFrom, dateTo]);

    return (
        <div className="admin-page">
            <h1>Conversiones</h1>
            <p className="admin-nav-links">
                <Link to="/admin">← Panel</Link>
                <span className="admin-nav-sep">·</span>
                <Link to="/admin/activity">Actividad</Link>
            </p>
            {error && <p className="admin-error">{error}</p>}
            <section className="admin-section">
            <div className="admin-users-toolbar">
                <input
                    type="text"
                    placeholder="User ID"
                    value={userIdFilter}
                    onChange={(e) => { setUserIdFilter(e.target.value); setPage(1); }}
                    className="admin-filter-input"
                    style={{ width: '100px' }}
                />
                <select
                    value={statusFilter}
                    onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                    className="admin-filter-input"
                    style={{ width: '140px' }}
                >
                    <option value="">Todos los estados</option>
                    <option value="pending">pending</option>
                    <option value="processing">processing</option>
                    <option value="completed">completed</option>
                    <option value="failed">failed</option>
                </select>
                <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
                    className="admin-filter-input"
                />
                <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
                    className="admin-filter-input"
                />
            </div>
            {data && (
                <>
                    <div className="admin-table-wrap">
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Usuario</th>
                                    <th>Archivo</th>
                                    <th>Formato</th>
                                    <th>Estado</th>
                                    <th>Fecha</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.items.map((c) => (
                                    <tr key={c.id}>
                                        <td>{c.id}</td>
                                        <td>{c.user_id ?? 'anónimo'}</td>
                                        <td>{c.original_filename}</td>
                                        <td>{c.original_format} → {c.target_format}</td>
                                        <td>{c.status}</td>
                                        <td>{c.created_at ? new Date(c.created_at).toLocaleString() : '—'}</td>
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
