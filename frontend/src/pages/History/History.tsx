import { useState, useEffect } from 'react';
import { Download, FileText, Calendar, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react';
import { apiService } from '../../services/api';
import './History.css';

interface Conversion {
    id: number;
    original_filename: string;
    original_format: string;
    target_format: string;
    file_size: number;
    status: string;
    error_message?: string;
    created_at: string;
    completed_at?: string;
}

export const History = () => {
    const [conversions, setConversions] = useState<Conversion[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<'all' | 'completed' | 'failed'>('all');

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await apiService.getConversionHistory(50);
            setConversions(data);
        } catch (err: any) {
            console.error('Error loading history:', err);
            setError(err.message || 'Error al cargar el historial de conversiones');
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async (conversionId: number, filename: string, targetFormat: string) => {
        try {
            const blob = await apiService.downloadConvertedFile(conversionId);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename.split('.')[0]}_converted.${targetFormat}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            console.error('Download failed:', err);
            alert('Error al descargar el archivo. Por favor intenta de nuevo.');
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="status-icon success" size={20} />;
            case 'failed':
                return <XCircle className="status-icon error" size={20} />;
            case 'processing':
                return <Clock className="status-icon processing" size={20} />;
            default:
                return <Clock className="status-icon" size={20} />;
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatFileSize = (bytes: number) => {
        return (bytes).toFixed(2) + ' MB';
    };

    const filteredConversions = conversions.filter(conv => {
        if (filter === 'all') return true;
        return conv.status === filter;
    });

    const stats = {
        total: conversions.length,
        completed: conversions.filter(c => c.status === 'completed').length,
        failed: conversions.filter(c => c.status === 'failed').length,
        processing: conversions.filter(c => c.status === 'processing').length
    };

    if (loading) {
        return (
            <div className="history-page">
                <div className="history-header">
                    <h2>Historial de Conversiones</h2>
                </div>
                <div className="loading-container">
                    <RefreshCw className="loading-spinner" size={40} />
                    <p>Cargando tu historial de conversiones...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="history-page">
                <div className="history-header">
                    <h2>Historial de Conversiones</h2>
                </div>
                <div className="error-container">
                    <XCircle size={48} className="error-icon" />
                    <h3>Error al Cargar Historial</h3>
                    <p>{error}</p>
                    <button onClick={loadHistory} className="retry-btn">
                        <RefreshCw size={18} />
                        Reintentar
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="history-page">
            <div className="history-header">
                <div>
                    <h2>Historial de Conversiones</h2>
                    <p>Visualiza y descarga tus conversiones anteriores</p>
                </div>
                <button onClick={loadHistory} className="refresh-btn">
                    <RefreshCw size={18} />
                    Actualizar
                </button>
            </div>

            {/* Statistics */}
            <div className="history-stats">
                <div className="stat-card">
                    <div className="stat-value">{stats.total}</div>
                    <div className="stat-label">Total</div>
                </div>
                <div className="stat-card success">
                    <div className="stat-value">{stats.completed}</div>
                    <div className="stat-label">Completadas</div>
                </div>
                <div className="stat-card error">
                    <div className="stat-value">{stats.failed}</div>
                    <div className="stat-label">Fallidas</div>
                </div>
                <div className="stat-card processing">
                    <div className="stat-value">{stats.processing}</div>
                    <div className="stat-label">Procesando</div>
                </div>
            </div>

            {/* Filters */}
            <div className="history-filters">
                <button
                    className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                    onClick={() => setFilter('all')}
                >
                    Todas ({conversions.length})
                </button>
                <button
                    className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
                    onClick={() => setFilter('completed')}
                >
                    Completadas ({stats.completed})
                </button>
                <button
                    className={`filter-btn ${filter === 'failed' ? 'active' : ''}`}
                    onClick={() => setFilter('failed')}
                >
                    Fallidas ({stats.failed})
                </button>
            </div>

            {/* Conversions List */}
            {filteredConversions.length === 0 ? (
                <div className="empty-state">
                    <FileText size={64} className="empty-icon" />
                    <h3>No hay conversiones aún</h3>
                    <p>Comienza a convertir archivos para verlos aquí</p>
                </div>
            ) : (
                <div className="conversions-list">
                    {filteredConversions.map((conversion) => (
                        <div key={conversion.id} className="conversion-card">
                            <div className="conversion-info">
                                <div className="conversion-icon">
                                    <FileText size={32} />
                                </div>
                                <div className="conversion-details">
                                    <h4>{conversion.original_filename}</h4>
                                    <div className="conversion-meta">
                                        <span className="format-badge">
                                            {conversion.original_format.toUpperCase()} → {conversion.target_format.toUpperCase()}
                                        </span>
                                        <span className="file-size">
                                            {formatFileSize(conversion.file_size)}
                                        </span>
                                        <span className="conversion-date">
                                            <Calendar size={14} />
                                            {formatDate(conversion.created_at)}
                                        </span>
                                    </div>
                                    {conversion.error_message && (
                                        <div className="error-message">
                                            {conversion.error_message}
                                        </div>
                                    )}
                                </div>
                            </div>
                            <div className="conversion-actions">
                                <div className="conversion-status">
                                    {getStatusIcon(conversion.status)}
                                    <span className={`status-text ${conversion.status}`}>
                                        {conversion.status.charAt(0).toUpperCase() + conversion.status.slice(1)}
                                    </span>
                                </div>
                                {conversion.status === 'completed' && (
                                    <button
                                        onClick={() => handleDownload(
                                            conversion.id,
                                            conversion.original_filename,
                                            conversion.target_format
                                        )}
                                        className="download-btn-small"
                                    >
                                        <Download size={18} />
                                        Descargar
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
