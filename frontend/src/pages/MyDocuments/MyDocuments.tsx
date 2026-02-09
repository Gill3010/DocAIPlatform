import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Clock, ChevronRight, Plus, Trash2, Shield } from 'lucide-react';
import { apiService } from '../../services/api';
import { ShareModal } from '../../components/ShareModal/ShareModal';
import './MyDocuments.css';

interface DocumentInfo {
    id: number;
    title: string;
    original_format: string;
    created_at: string;
    updated_at: string | null;
}

export const MyDocuments = () => {
    const [documents, setDocuments] = useState<DocumentInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [shareDocId, setShareDocId] = useState<number | null>(null);
    const navigate = useNavigate();

    const handleDelete = async (e: React.MouseEvent, id: number) => {
        e.stopPropagation();
        if (!window.confirm('¿Estás seguro de que quieres eliminar este documento? Esta acción no se puede deshacer.')) {
            return;
        }

        try {
            await apiService.deleteDocument(id);
            setDocuments(prev => prev.filter(doc => doc.id !== id));
        } catch (err) {
            console.error('Error deleting document:', err);
            alert('No se pudo eliminar el documento.');
        }
    };

    useEffect(() => {
        const fetchDocs = async () => {
            try {
                const data = await apiService.getDocuments();
                setDocuments(data);
                setLoading(false);
            } catch (err) {
                console.error('Error fetching documents:', err);
                setError('No se pudieron cargar tus documentos.');
                setLoading(false);
            }
        };

        fetchDocs();
    }, []);

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('es-ES', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    };

    if (loading) {
        return (
            <div className="docs-loading">
                <div className="spinner"></div>
                <p>Cargando tus documentos...</p>
            </div>
        );
    }

    return (
        <div className="my-documents-page">
            <header className="docs-header">
                <div>
                    <h1>Mis Documentos</h1>
                    <p>Gestiona tus archivos colaborativos y ediciones recientes.</p>
                </div>
                <button className="create-new-btn" onClick={() => navigate('/convert')}>
                    <Plus size={18} />
                    Nueva Conversión
                </button>
            </header>

            {error && <div className="docs-error">{error}</div>}

            <div className="docs-grid">
                {documents.length === 0 ? (
                    <div className="no-docs">
                        <FileText size={48} />
                        <h3>Aún no tienes documentos</h3>
                        <p>Convierte un archivo y ábrelo en el editor para que aparezca aquí.</p>
                        <button onClick={() => navigate('/convert')}>Empezar ahora</button>
                    </div>
                ) : (
                    documents.map((doc) => (
                        <div key={doc.id} className="doc-card" onClick={() => navigate(`/collab/${doc.id}`)}>
                            <div className="doc-icon">
                                <FileText size={24} />
                                <span className="format-tag">{doc.original_format}</span>
                            </div>
                            <div className="doc-info">
                                <h3>{doc.title}</h3>
                                <div className="doc-meta">
                                    <span>
                                        <Clock size={14} />
                                        {formatDate(doc.updated_at || doc.created_at)}
                                    </span>
                                </div>
                            </div>
                            <div className="doc-actions">
                                <button title="Permisos" onClick={(e) => { e.stopPropagation(); setShareDocId(doc.id); }}>
                                    <Shield size={18} />
                                </button>
                                <button title="Eliminar" className="delete-btn" onClick={(e) => handleDelete(e, doc.id)}>
                                    <Trash2 size={18} />
                                </button>
                                <button className="go-btn">
                                    <ChevronRight size={20} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {shareDocId && (
                <ShareModal
                    documentId={shareDocId}
                    onClose={() => setShareDocId(null)}
                />
            )}
        </div>
    );
};
