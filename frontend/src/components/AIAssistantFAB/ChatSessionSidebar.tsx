import { useState, useRef } from 'react';
import { Plus, MessageSquare } from 'lucide-react';
import './ChatSessionSidebar.css';

export interface ChatSessionItem {
    id: string;
    title: string | null;
    created_at: string;
    updated_at: string;
}

interface ChatSessionSidebarProps {
    sessions: ChatSessionItem[];
    activeSessionId: string | null;
    onSelectSession: (id: string) => void;
    onNewChat: () => void;
    loading?: boolean;
}

export function ChatSessionSidebar({
    sessions,
    activeSessionId,
    onSelectSession,
    onNewChat,
    loading = false,
}: ChatSessionSidebarProps) {
    const [tooltip, setTooltip] = useState<{ text: string; top: number; left: number } | null>(null);
    const tooltipTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const showTooltip = (el: HTMLElement, text: string) => {
        tooltipTimerRef.current = setTimeout(() => {
            const rect = el.getBoundingClientRect();
            setTooltip({
                text,
                top: rect.top,
                left: rect.left + rect.width / 2,
            });
        }, 200);
    };

    const hideTooltip = () => {
        if (tooltipTimerRef.current) {
            clearTimeout(tooltipTimerRef.current);
            tooltipTimerRef.current = null;
        }
        setTooltip(null);
    };

    return (
        <div className="ai-chat-sidebar">
            <button
                type="button"
                className="ai-chat-sidebar-new"
                onClick={onNewChat}
                onMouseEnter={(e) => showTooltip(e.currentTarget, 'Nuevo chat')}
                onMouseLeave={hideTooltip}
                aria-label="Nuevo chat"
            >
                <Plus size={18} />
                <span>Nuevo chat</span>
            </button>
            <div className="ai-chat-sidebar-list">
                {loading ? (
                    <div className="ai-chat-sidebar-loading">Cargando…</div>
                ) : sessions.length === 0 ? (
                    <div className="ai-chat-sidebar-empty">Sin conversaciones</div>
                ) : (
                    sessions.map((s) => (
                        <button
                            key={s.id}
                            type="button"
                            className={`ai-chat-sidebar-item ${activeSessionId === s.id ? 'active' : ''}`}
                            onClick={() => onSelectSession(s.id)}
                            onMouseEnter={(e) => showTooltip(e.currentTarget, s.title || 'Chat')}
                            onMouseLeave={hideTooltip}
                            aria-label={s.title || 'Chat'}
                        >
                            <MessageSquare size={16} />
                            <span className="ai-chat-sidebar-item-title">
                                {s.title || 'Nuevo chat'}
                            </span>
                        </button>
                    ))
                )}
            </div>
            {tooltip && (
                <div
                    className="ai-chat-tooltip"
                    style={{ left: tooltip.left, top: tooltip.top }}
                    role="tooltip"
                >
                    {tooltip.text}
                </div>
            )}
        </div>
    );
}
