import { useState, useCallback, useEffect } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Download, RefreshCw, XCircle, Clock, CheckCircle, Calendar } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import { UpgradeModal } from '../../components/UpgradeModal/UpgradeModal';
import { apiService } from '../../services/api';
import './FormatManuscript.css';
import '../History/History.css';

interface ManuscriptRecord {
    id: number;
    original_filename: string;
    file_size: number;
    status: string;
    error_message?: string;
    created_at: string;
}

export const FormatManuscript = () => {
    const { user } = useAppStore();

    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [showUpgradeModal, setShowUpgradeModal] = useState(false);
    const [isFormatting, setIsFormatting] = useState(false);

    // History state
    const [history, setHistory] = useState<ManuscriptRecord[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [historyError, setHistoryError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'upload' | 'history'>('upload');

    const isPro = !!(
        user?.is_superuser ||
        user?.can_access_admin_panel ||
        (user?.is_premium && (user?.premium_plan_id === 'Pro' || user?.premium_plan_id === 'Empresa'))
    );

    // Load history when tab switches to 'history'
    useEffect(() => {
        if (activeTab === 'history' && isPro) {
            loadHistory();
        }
    }, [activeTab]);

    const loadHistory = async () => {
        try {
            setHistoryLoading(true);
            setHistoryError(null);
            const data = await apiService.getManuscriptHistory(50);
            setHistory(data);
        } catch (err: any) {
            setHistoryError(err.message || 'Error al cargar el historial');
        } finally {
            setHistoryLoading(false);
        }
    };

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) setSelectedFile(files[0]);
    }, []);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) setSelectedFile(files[0]);
    };

    const handleRemoveFile = () => setSelectedFile(null);

    const formatFileSize = (mb: number) => `${mb.toFixed(2)} MB`;

    const formatFileSizeBytes = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    };

    const formatDate = (dateString: string) =>
        new Date(dateString).toLocaleDateString('es-ES', {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });

    const handleFormat = async () => {
        if (!isPro) { setShowUpgradeModal(true); return; }
        if (!selectedFile) return;

        setIsFormatting(true);
        try {
            const blob = await apiService.formatManuscript(selectedFile);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `formateado_${selectedFile.name}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            // Refresh history after successful format
            setHistory([]);
        } catch (error: any) {
            alert(error.message || 'Hubo un error al procesar tu documento');
        } finally {
            setIsFormatting(false);
        }
    };

    const handleDownloadHistory = async (record: ManuscriptRecord) => {
        try {
            const blob = await apiService.downloadFormattedManuscript(record.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `formateado_${record.original_filename}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch {
            alert('Error al descargar el archivo. Puede que ya no esté disponible en el servidor.');
        }
    };

    const getStatusIcon = (s: string) => {
        if (s === 'completed') return <CheckCircle className="status-icon success" size={20} />;
        if (s === 'failed') return <XCircle className="status-icon error" size={20} />;
        return <Clock className="status-icon processing" size={20} />;
    };

    const stats = {
        total: history.length,
        completed: history.filter(r => r.status === 'completed').length,
        failed: history.filter(r => r.status === 'failed').length,
    };

    return (
        <div className="format-manuscript-page">
            <UpgradeModal
                isOpen={showUpgradeModal}
                onClose={() => setShowUpgradeModal(false)}
                title="Esta función requiere el Plan Pro"
                description="El formateo de manuscritos es una herramienta avanzada disponible exclusivamente para usuarios Pro y Empresa."
            />

            {/* Header */}
            <div className="format-header">
                <div>
                    <h2>Formateador de Manuscritos</h2>
                    <p>Estandariza tu documento .docx para compatibilidad con el conversor JATS XML</p>
                </div>
                <span className="status-badge coming-soon">Beta Pro</span>
            </div>

            {/* Tabs */}
            <div className="fm-tabs">
                <button
                    className={`fm-tab ${activeTab === 'upload' ? 'active' : ''}`}
                    onClick={() => setActiveTab('upload')}
                >
                    <FileText size={16} />
                    Formatear
                </button>
                <button
                    className={`fm-tab ${activeTab === 'history' ? 'active' : ''}`}
                    onClick={() => setActiveTab('history')}
                >
                    <Calendar size={16} />
                    Historial
                </button>
            </div>

            {/* ── UPLOAD TAB ── */}
            {activeTab === 'upload' && (
                <div className="format-upload-section">
                    {!selectedFile ? (
                        <div
                            className={`upload-zone ${isDragging ? 'dragging' : ''}`}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                        >
                            <Upload className="upload-icon" size={64} />
                            <h3>Selecciona tu manuscrito</h3>
                            <p>Arrastra y suelta tu archivo aquí, o haz clic para seleccionar</p>
                            <div className="supported-formats">
                                <span className="format-badge">DOCX</span>
                            </div>
                            <input
                                type="file"
                                id="file-input"
                                accept=".docx"
                                onChange={handleFileSelect}
                                className="file-input-hidden"
                            />
                            <label htmlFor="file-input" className="upload-btn">
                                Seleccionar Archivo
                            </label>
                        </div>
                    ) : (
                        <div className="file-selected-container">
                            <div className="file-selected-card">
                                <div className="file-icon-container">
                                    <FileText size={48} />
                                </div>
                                <div className="file-details">
                                    <h4>{selectedFile.name}</h4>
                                    <p className="file-size">{formatFileSizeBytes(selectedFile.size)}</p>
                                    <div className="file-status">
                                        <CheckCircle2 size={20} className="status-icon success" />
                                        <span>Archivo listo para formatear</span>
                                    </div>
                                </div>
                                <button onClick={handleRemoveFile} className="remove-file-btn">✕</button>
                            </div>

                            <div className="format-options-placeholder">
                                <div className="placeholder-icon">
                                    <AlertCircle size={32} />
                                </div>
                                <h3>Normalización automática</h3>
                                <p>El formateador aplicará las siguientes reglas al documento</p>
                                <div className="placeholder-items">
                                    <div className="placeholder-item">📄 Estilos de encabezados (Heading 1/2)</div>
                                    <div className="placeholder-item">📝 Alineación de título y autores</div>
                                    <div className="placeholder-item">📑 Secciones JATS (Introducción, Metodología…)</div>
                                    <div className="placeholder-item">📊 Normalización de captions (Figura/Tabla)</div>
                                </div>
                            </div>

                            <button className="manuscript-action-btn" onClick={handleFormat} disabled={isFormatting}>
                                <FileText size={20} />
                                {isFormatting ? 'Formateando...' : 'Formatear Manuscrito'}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* ── HISTORY TAB ── */}
            {activeTab === 'history' && (
                <div className="fm-history">
                    {/* Stats */}
                    <div className="history-stats">
                        <div className="stat-card">
                            <div className="stat-value">{stats.total}</div>
                            <div className="stat-label">Total</div>
                        </div>
                        <div className="stat-card success">
                            <div className="stat-value">{stats.completed}</div>
                            <div className="stat-label">Completados</div>
                        </div>
                        <div className="stat-card error">
                            <div className="stat-value">{stats.failed}</div>
                            <div className="stat-label">Fallidos</div>
                        </div>
                        <div className="stat-card">
                            <button onClick={loadHistory} className="refresh-btn" style={{ width: '100%', height: '100%' }}>
                                <RefreshCw size={18} />
                                Actualizar
                            </button>
                        </div>
                    </div>

                    {historyLoading && (
                        <div className="loading-container">
                            <RefreshCw className="loading-spinner" size={40} />
                            <p>Cargando historial...</p>
                        </div>
                    )}

                    {historyError && (
                        <div className="error-container">
                            <XCircle size={48} className="error-icon" />
                            <h3>Error al cargar</h3>
                            <p>{historyError}</p>
                            <button onClick={loadHistory} className="retry-btn">
                                <RefreshCw size={18} /> Reintentar
                            </button>
                        </div>
                    )}

                    {!historyLoading && !historyError && history.length === 0 && (
                        <div className="empty-state">
                            <FileText size={64} className="empty-icon" />
                            <h3>Sin historial aún</h3>
                            <p>Formatea un manuscrito para verlo aquí</p>
                        </div>
                    )}

                    {!historyLoading && !historyError && history.length > 0 && (
                        <div className="conversions-list">
                            {history.map((record) => (
                                <div key={record.id} className="conversion-card">
                                    <div className="conversion-info">
                                        <div className="conversion-icon">
                                            <FileText size={32} />
                                        </div>
                                        <div className="conversion-details">
                                            <h4>{record.original_filename}</h4>
                                            <div className="conversion-meta">
                                                <span className="format-badge">DOCX → DOCX (formateado)</span>
                                                <span className="file-size">{formatFileSize(record.file_size)}</span>
                                                <span className="conversion-date">
                                                    <Calendar size={14} />
                                                    {formatDate(record.created_at)}
                                                </span>
                                            </div>
                                            {record.error_message && (
                                                <div className="error-message">{record.error_message}</div>
                                            )}
                                        </div>
                                    </div>
                                    <div className="conversion-actions">
                                        <div className="conversion-status">
                                            {getStatusIcon(record.status)}
                                            <span className={`status-text ${record.status}`}>
                                                {record.status === 'completed' ? 'Completado' :
                                                    record.status === 'failed' ? 'Fallido' : 'Procesando'}
                                            </span>
                                        </div>
                                        {record.status === 'completed' && (
                                            <button
                                                onClick={() => handleDownloadHistory(record)}
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
            )}
        </div>
    );
};
