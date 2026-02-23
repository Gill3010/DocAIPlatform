import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Pencil, Trash2 } from 'lucide-react';
import './ChatHistoryView.css';

export interface ChatSessionItem {
    id: string;
    title: string | null;
    created_at: string;
    updated_at: string;
}

interface ChatHistoryViewProps {
    sessions: ChatSessionItem[];
    onSelectSession: (id: string) => void;
    onRename?: (id: string, title: string) => Promise<void>;
    onDelete?: (id: string) => Promise<void>;
    loading?: boolean;
}

export function ChatHistoryView({
    sessions,
    onSelectSession,
    onRename,
    onDelete,
    loading = false,
}: ChatHistoryViewProps) {
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editingValue, setEditingValue] = useState('');
    const editInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (editingId && editInputRef.current) {
            editInputRef.current.focus();
            editInputRef.current.select();
        }
    }, [editingId]);
    const formatDate = (iso: string) => {
        try {
            const d = new Date(iso);
            const now = new Date();
            const sameDay = d.toDateString() === now.toDateString();
            if (sameDay) {
                return d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
            }
            return d.toLocaleDateString('es-ES', {
                day: '2-digit',
                month: 'short',
                year: d.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
            });
        } catch {
            return '';
        }
    };

    const startEdit = (s: ChatSessionItem) => {
        setEditingId(s.id);
        setEditingValue(s.title || 'Nuevo chat');
    };

    const saveEdit = async () => {
        if (!editingId || !onRename) return;
        const trimmed = editingValue.trim() || 'Nuevo chat';
        try {
            await onRename(editingId, trimmed);
        } catch (err) {
            console.error('Failed to rename:', err);
        }
        setEditingId(null);
    };

    const cancelEdit = () => setEditingId(null);

    const handleDelete = async (s: ChatSessionItem) => {
        if (!onDelete) return;
        if (!window.confirm('¿Eliminar esta conversación? No se puede deshacer.')) return;
        try {
            await onDelete(s.id);
        } catch (err) {
            console.error('Failed to delete:', err);
        }
    };

    return (
        <div className="ai-chat-history-view">
            <div className="ai-chat-history-header">
                <h4>Conversaciones</h4>
            </div>
            <div className="ai-chat-history-list">
                {loading ? (
                    <div className="ai-chat-history-loading">Cargando conversaciones…</div>
                ) : sessions.length === 0 ? (
                    <div className="ai-chat-history-empty">
                        <MessageSquare size={40} strokeWidth={1.5} />
                        <p>No hay conversaciones</p>
                        <span>Inicia una nueva para empezar</span>
                    </div>
                ) : (
                    sessions.map((s) => (
                        <div
                            key={s.id}
                            className="ai-chat-history-item"
                            onClick={() => !editingId && onSelectSession(s.id)}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => {
                                if (editingId) return;
                                if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault();
                                    onSelectSession(s.id);
                                }
                            }}
                        >
                            <MessageSquare size={20} className="ai-chat-history-item-icon" />
                            <div className="ai-chat-history-item-content">
                                {editingId === s.id ? (
                                    <input
                                        ref={editInputRef}
                                        type="text"
                                        className="ai-chat-history-item-edit"
                                        value={editingValue}
                                        onChange={(e) => setEditingValue(e.target.value)}
                                        onBlur={saveEdit}
                                        onKeyDown={(e) => {
                                            e.stopPropagation();
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                saveEdit();
                                            } else if (e.key === 'Escape') {
                                                cancelEdit();
                                            }
                                        }}
                                        onClick={(e) => e.stopPropagation()}
                                        aria-label="Nuevo nombre"
                                    />
                                ) : (
                                    <span className="ai-chat-history-item-title">
                                        {s.title || 'Nuevo chat'}
                                    </span>
                                )}
                                <span className="ai-chat-history-item-date">
                                    {formatDate(s.updated_at || s.created_at)}
                                </span>
                            </div>
                            {(onRename || onDelete) && (
                                <div
                                    className="ai-chat-history-item-actions"
                                    onClick={(e) => e.stopPropagation()}
                                    role="group"
                                    aria-label="Acciones"
                                >
                                    {onRename && (
                                        <button
                                            type="button"
                                            className="ai-chat-history-item-btn"
                                            onClick={() => startEdit(s)}
                                            aria-label="Renombrar"
                                        >
                                            <Pencil size={14} />
                                        </button>
                                    )}
                                    {onDelete && (
                                        <button
                                            type="button"
                                            className="ai-chat-history-item-btn ai-chat-history-item-btn--delete"
                                            onClick={() => handleDelete(s)}
                                            aria-label="Eliminar"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
