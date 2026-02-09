import React, { useState, useEffect } from 'react';
import { X, Search, UserPlus, Shield, Check, Loader2, Trash2 } from 'lucide-react';
import { apiService } from '../../services/api';
import './ShareModal.css';

interface ShareModalProps {
    documentId: number;
    onClose: () => void;
}

export const ShareModal: React.FC<ShareModalProps> = ({ documentId, onClose }) => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<any[]>([]);
    const [collaborators, setCollaborators] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [loadingCollabs, setLoadingCollabs] = useState(true);
    const [sharing, setSharing] = useState<number | null>(null);
    const [removing, setRemoving] = useState<number | null>(null);
    const [success, setSuccess] = useState<number | null>(null);

    useEffect(() => {
        fetchCollaborators();
    }, [documentId]);

    const fetchCollaborators = async () => {
        try {
            const data = await apiService.getDocumentPermissions(documentId);
            // We need to fetch user details for these permissions or if the endpoint returns user objects inside
            // For now assuming endpoint returns list of { user_id, role, user?: { email, full_name, avatar_url } }
            // If the endpoint only returns user_id, we might need to adjust.
            // Based on previous code, we might need a way to get user info.
            // Let's assume for now we can get the list and we'll see.
            // Actually, my backend implementation returns DocumentPermission objects.
            // I should probably update the backend to Include the User relationship in the response.
            // Valid point. Let's start by listing them.
            setCollaborators(data);
        } catch (err) {
            console.error('Error fetching collaborators:', err);
        } finally {
            setLoadingCollabs(false);
        }
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            if (query.length >= 2) {
                searchUsers();
            } else {
                setResults([]);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [query]);

    const searchUsers = async () => {
        setLoading(true);
        try {
            const data = await apiService.searchUsers(query);
            // Filter out users who are already collaborators
            const collaboratorIds = new Set(collaborators.map(c => c.user_id));
            setResults(data.filter(u => !collaboratorIds.has(u.id)));
        } catch (err) {
            console.error('Error searching users:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleShare = async (userId: number, role: 'viewer' | 'editor') => {
        setSharing(userId);
        try {
            await apiService.addDocumentPermission(documentId, userId, role);
            setSuccess(userId);
            // Refresh collaborators list
            await fetchCollaborators();
            // Remove from search results
            setResults(prev => prev.filter(u => u.id !== userId));
            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            console.error('Error sharing document:', err);
            alert('No se pudo compartir el documento.');
        } finally {
            setSharing(null);
        }
    };

    const handleRemove = async (userId: number) => {
        if (!window.confirm('¿Estás seguro de que quieres eliminar el acceso de este usuario?')) return;
        setRemoving(userId);
        try {
            await apiService.removeDocumentPermission(documentId, userId);
            setCollaborators(prev => prev.filter(c => c.user_id !== userId));
        } catch (err) {
            console.error('Error removing permission:', err);
            alert('No se pudo eliminar el acceso.');
        } finally {
            setRemoving(null);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="share-modal" onClick={(e) => e.stopPropagation()}>
                <header className="share-header">
                    <h3>Compartir documento</h3>
                    <button className="close-btn" onClick={onClose}><X size={20} /></button>
                </header>

                <div className="share-section">
                    <h4>Agregar personas</h4>
                    <div className="share-search">
                        <div className="search-input-wrapper">
                            <Search size={18} className="search-icon" />
                            <input
                                type="text"
                                placeholder="Buscar por email..."
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                autoFocus
                            />
                        </div>
                    </div>

                    <div className="share-results">
                        {loading && <div className="results-loading"><Loader2 className="spin" /> Buscando...</div>}
                        {!loading && query.length >= 2 && results.length === 0 && (
                            <div className="no-results">No se encontraron usuarios o ya tienen acceso.</div>
                        )}
                        {results.map((user) => (
                            <div key={user.id} className="user-result">
                                <div className="user-info">
                                    <div className="user-avatar">
                                        {user.avatar_url ? (
                                            <img src={user.avatar_url} alt={user.full_name} />
                                        ) : (
                                            <div className="avatar-placeholder">{user.email[0].toUpperCase()}</div>
                                        )}
                                    </div>
                                    <div className="user-details">
                                        <p className="user-name">{user.full_name || 'Usuario'}</p>
                                        <p className="user-email">{user.email}</p>
                                    </div>
                                </div>
                                <div className="share-actions">
                                    {success === user.id ? (
                                        <div className="success-badge"><Check size={16} /> Compartido</div>
                                    ) : (
                                        <>
                                            <button
                                                className="share-btn reader"
                                                disabled={sharing === user.id}
                                                onClick={() => handleShare(user.id, 'viewer')}
                                            >
                                                <Shield size={14} /> Lector
                                            </button>
                                            <button
                                                className="share-btn writer"
                                                disabled={sharing === user.id}
                                                onClick={() => handleShare(user.id, 'editor')}
                                            >
                                                <UserPlus size={14} /> Editor
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="share-section collaborators-section">
                    <h4>Personas con acceso</h4>
                    {loadingCollabs ? (
                        <div className="results-loading"><Loader2 className="spin" /> Cargando...</div>
                    ) : collaborators.length === 0 ? (
                        <p className="no-collabs">Solo tú tienes acceso a este documento.</p>
                    ) : (
                        <div className="collaborators-list">
                            {collaborators.map((collab) => (
                                <div key={collab.user_id} className="user-result">
                                    <div className="user-info">
                                        <div className="user-avatar">
                                            {collab.user?.avatar_url ? (
                                                <img src={collab.user.avatar_url} alt={collab.user.full_name} />
                                            ) : (
                                                <div className="avatar-placeholder">
                                                    {(collab.user?.email?.[0] || '?').toUpperCase()}
                                                </div>
                                            )}
                                        </div>
                                        <div className="user-details">
                                            <p className="user-name">{collab.user?.full_name || collab.user?.email || `Usuario #${collab.user_id}`}</p>
                                            <div className="user-meta">
                                                <span className="user-email">{collab.user?.email}</span>
                                                <span className={`role-badge ${collab.role}`}>
                                                    {collab.role === 'viewer' ? 'Lector' : 'Editor'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="share-actions">
                                        <button
                                            className="remove-btn"
                                            disabled={removing === collab.user_id}
                                            onClick={() => handleRemove(collab.user_id)}
                                            title="Eliminar acceso"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
