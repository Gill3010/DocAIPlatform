import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../../services/api';
import './Admin.css';

type PaymentItem = {
    id: number;
    user_id: number;
    user_email: string | null;
    provider: string;
    transaction_id: string | null;
    amount: number;
    currency: string;
    status: string;
    plan_id: string | null;
    created_at: string | null;
};

const PayPalLogo = () => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <img src="/paypal-icon.webp" alt="PayPal" style={{ width: '100px', height: 'auto', display: 'block' }} />
    </div>
);

export const AdminPayments = () => {
    const [data, setData] = useState<{
        items: PaymentItem[];
        total: number;
        page: number;
        size: number;
        pages: number;
    } | null>(null);
    const [page, setPage] = useState(1);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        apiService
            .getAdminPayments({ page, size: 20 })
            .then(setData)
            .catch((err) => {
                setError(err instanceof Error ? err.message : 'Error al cargar pagos');
                setData(null);
            });
    }, [page]);

    return (
        <div className="admin-page">
            <h1>Pagos y Membresías</h1>
            <p className="admin-nav-links">
                <Link to="/admin">← Panel</Link>
                <span className="admin-nav-sep">·</span>
                <Link to="/admin">Usuarios</Link>
                <span className="admin-nav-sep">·</span>
                <Link to="/admin/conversions">Conversiones</Link>
            </p>
            {error && <p className="admin-error">{error}</p>}

            <section className="admin-section">
                {data && (
                    <>
                        <div className="admin-table-wrap">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Usuario</th>
                                        <th>Plan</th>
                                        <th>Monto</th>
                                        <th>Estado</th>
                                        <th>Proveedor</th>
                                        <th>ID Transacción</th>
                                        <th>Fecha</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.items.length > 0 ? (
                                        data.items.map((p) => (
                                            <tr key={p.id}>
                                                <td>{p.id}</td>
                                                <td title={p.user_email || ''}>
                                                    {p.user_email || `ID: ${p.user_id}`}
                                                </td>
                                                <td>
                                                    <span className={`plan-badge plan-${p.plan_id?.toLowerCase()}`}>
                                                        {p.plan_id}
                                                    </span>
                                                </td>
                                                <td>{p.amount} {p.currency}</td>
                                                <td>
                                                    <span className={`status-badge status-${p.status}`}>
                                                        {p.status}
                                                    </span>
                                                </td>
                                                <td>
                                                    {p.provider === 'paypal' ? <PayPalLogo /> : p.provider}
                                                </td>
                                                <td className="transaction-id">{p.transaction_id || '—'}</td>
                                                <td>{p.created_at ? new Date(p.created_at).toLocaleString() : '—'}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={8} style={{ textAlign: 'center', padding: '2rem' }}>
                                                No se han encontrado pagos registrados.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {data.pages > 1 && (
                            <div className="admin-pagination">
                                <button
                                    type="button"
                                    disabled={page <= 1}
                                    onClick={() => setPage((p) => p - 1)}
                                >
                                    Anterior
                                </button>
                                <span>Página {page} de {data.pages} ({data.total} total)</span>
                                <button
                                    type="button"
                                    disabled={page >= data.pages}
                                    onClick={() => setPage((p) => p + 1)}
                                >
                                    Siguiente
                                </button>
                            </div>
                        )}
                    </>
                )}
            </section>
        </div>
    );
};
