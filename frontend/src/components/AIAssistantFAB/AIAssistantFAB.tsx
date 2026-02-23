import { useState, useEffect, useRef } from 'react';
import { Send, X, Minimize2, Maximize2, Loader, Paperclip, Plus, History, MessageCircle, Sparkles } from 'lucide-react';
import { apiService } from '../../services/api';
import { useAppStore } from '../../stores/appStore';
import { useAnonymousSession } from '../../hooks/useAnonymousSession';
import { ConversionLimitModal } from '../ConversionLimitModal/ConversionLimitModal';
import { UpgradeModal } from '../UpgradeModal/UpgradeModal';
import { ChatHistoryView } from './ChatHistoryView';
import { MarkdownMessage } from './MarkdownMessage';
import './AIAssistantFAB.css';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

interface AIAssistantFABProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
}

const WELCOME_MESSAGE: Message = {
    id: 'welcome',
    role: 'assistant',
    content: '👋 ¡Hola! Soy tu Asistente de IA. ¿En qué puedo ayudarte?',
    timestamp: new Date(),
};

const WELCOME_SUGGESTIONS: { label: string; prompt: string }[] = [
    { label: 'Cómo usar la aplicación', prompt: 'Explícame cómo usar la aplicación DocAI Platform' },
    { label: 'Consejos de conversión', prompt: 'Dame consejos para convertir archivos correctamente' },
    { label: 'Recomendaciones de formato', prompt: '¿Qué formatos recomiendas y cuándo usarlos? Incluye enlaces.' },
    { label: 'Preguntas sobre mis documentos', prompt: 'Tengo preguntas sobre mis documentos y formatos' },
];

export const AIAssistantFAB = ({ isOpen, onOpenChange }: AIAssistantFABProps) => {
    const { token, user } = useAppStore();
    const isAdminUnlimited = user?.is_superuser === true || user?.can_access_admin_panel === true || user?.is_premium === true;
    const { sessionId, syncFromCreditsRemaining } = useAnonymousSession();
    const [isMinimized, setIsMinimized] = useState(false);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
    const [credits, setCredits] = useState(10);
    const [showLimitModal, setShowLimitModal] = useState(false);
    const [showUpgradeModal, setShowUpgradeModal] = useState(false);
    const [sessions, setSessions] = useState<{ id: string; title: string | null; created_at: string; updated_at: string }[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(() => {
        try {
            if (typeof window === 'undefined') return null;
            if (!token) return null;
            return localStorage.getItem('docai-assistant-active-session');
        } catch {
            return null;
        }
    });
    const hasRestoredRef = useRef(false);
    const [sessionsLoading, setSessionsLoading] = useState(false);
    const [attachments, setAttachments] = useState<{ id: string; filename: string }[]>([]);
    const [uploading, setUploading] = useState(false);
    const [view, setView] = useState<'chat' | 'historial'>('chat');
    const [tooltip, setTooltip] = useState<{ text: string; top: number; left: number } | null>(null);
    const tooltipTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

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

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (isOpen && !isMinimized && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen, isMinimized]);

    useEffect(() => {
        const loadCredits = async () => {
            try {
                if (token) {
                    const stats = await apiService.getUserStats();
                    setCredits(isAdminUnlimited ? 999999 : stats.credits.remaining);
                } else {
                    const data = await apiService.getAICredits(sessionId);
                    setCredits(data.credits_remaining);
                }
            } catch (error) {
                console.error('Failed to load credits:', error);
                if (!token) setCredits(0);
            }
        };
        loadCredits();
    }, [token, sessionId, isAdminUnlimited]);

    const loadSessions = async () => {
        setSessionsLoading(true);
        try {
            const list = await apiService.getChatSessions(sessionId);
            setSessions(list);
        } catch (error) {
            console.error('Failed to load sessions:', error);
        } finally {
            setSessionsLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen && token) {
            loadSessions();
        }
    }, [isOpen, token]);

    useEffect(() => {
        if (!token) return;
        try {
            if (activeSessionId) {
                localStorage.setItem('docai-assistant-active-session', activeSessionId);
            } else {
                localStorage.removeItem('docai-assistant-active-session');
            }
        } catch {
            /* ignore */
        }
    }, [activeSessionId, token]);

    useEffect(() => {
        if (!isOpen || !activeSessionId || hasRestoredRef.current) return;
        const isWelcomeOnly = messages.length === 1 && messages[0].id === 'welcome';
        if (!isWelcomeOnly) return;
        hasRestoredRef.current = true;
        let cancelled = false;
        apiService
            .getChatSession(activeSessionId, sessionId)
            .then((detail) => {
                if (cancelled) return;
                setMessages(
                    detail.messages.map((m) => ({
                        id: m.id,
                        role: m.role as 'user' | 'assistant',
                        content: m.content,
                        timestamp: new Date(m.created_at),
                    }))
                );
                setView('chat');
            })
            .catch((err) => {
                if (cancelled) return;
                console.error('Failed to restore session:', err);
                setActiveSessionId(null);
                setMessages([WELCOME_MESSAGE]);
                try {
                    localStorage.removeItem('docai-assistant-active-session');
                } catch {
                    /* ignore */
                }
            });
        return () => {
            cancelled = true;
        };
    }, [isOpen, activeSessionId, sessionId, messages]);

    const handleNewChat = () => {
        setActiveSessionId(null);
        setMessages([WELCOME_MESSAGE]);
        setAttachments([]);
        setView('chat');
    };

    const handleSelectSession = async (id: string) => {
        setActiveSessionId(id);
        try {
            const detail = await apiService.getChatSession(id, sessionId);
            setMessages(
                detail.messages.map((m) => ({
                    id: m.id,
                    role: m.role as 'user' | 'assistant',
                    content: m.content,
                    timestamp: new Date(m.created_at),
                }))
            );
            setView('chat');
        } catch (error) {
            console.error('Failed to load session:', error);
        }
    };

    const handleRenameSession = async (id: string, title: string) => {
        try {
            await apiService.updateChatSession(id, title, sessionId);
            const updated = await apiService.getChatSessions(sessionId);
            setSessions(updated);
        } catch (error) {
            console.error('Failed to rename session:', error);
            throw error;
        }
    };

    const handleDeleteSession = async (id: string) => {
        try {
            await apiService.deleteChatSession(id, sessionId);
            setSessions((prev) => prev.filter((s) => s.id !== id));
            if (activeSessionId === id) {
                setActiveSessionId(null);
                setMessages([WELCOME_MESSAGE]);
                setView('chat');
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
            throw error;
        }
    };

    const handleClose = () => {
        onOpenChange(false);
        setIsMinimized(false);
    };

    const toggleMinimize = () => {
        setIsMinimized(!isMinimized);
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files?.length) return;
        setUploading(true);
        try {
            for (let i = 0; i < Math.min(files.length, 2); i++) {
                const file = files[i];
                const ext = (file.name || '').toLowerCase().slice(-5);
                if (!['.pdf', '.docx', '.doc', '.txt'].some((x) => ext.endsWith(x))) continue;
                const res = await apiService.uploadChatAttachment(file, sessionId);
                setAttachments((prev) => [...prev, { id: res.attachment_id, filename: res.filename || file.name }]);
            }
        } catch (err) {
            console.error('Upload failed:', err);
        } finally {
            setUploading(false);
            e.target.value = '';
        }
    };

    const removeAttachment = (id: string) => {
        setAttachments((prev) => prev.filter((a) => a.id !== id));
    };

    const submitMessage = async (content: string) => {
        if (!content.trim() || loading) return;
        if (!token && credits <= 0) {
            setShowLimitModal(true);
            return;
        }
        if (token && credits <= 0) {
            setShowUpgradeModal(true);
            return;
        }

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: content.trim(),
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        const attachmentIds = attachments.map((a) => a.id);
        setAttachments([]);
        setLoading(true);

        try {
            const response = await apiService.sendChatMessage(
                userMessage.content,
                sessionId,
                {
                    sessionId: activeSessionId ?? undefined,
                    attachmentIds: attachmentIds.length ? attachmentIds : undefined,
                }
            );

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.message,
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
            setCredits(response.credits_remaining);
            if (response.session_id) {
                setActiveSessionId(response.session_id);
                loadSessions();
            }
            if (!token && response.credits_remaining !== undefined) {
                syncFromCreditsRemaining(response.credits_remaining);
            }
        } catch (error: unknown) {
            const msg = (error as { message?: string })?.message || '';
            const friendly =
                msg === 'anonymous_limit_reached'
                    ? 'No quedan créditos. Regístrate para obtener más.'
                    : msg || 'Lo siento, encontré un error. Por favor intenta de nuevo.';
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: `❌ ${friendly}`,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
            if (msg === 'anonymous_limit_reached') {
                setCredits(0);
                syncFromCreditsRemaining(0);
                setShowLimitModal(true);
            } else if (msg.includes('exhausted') || msg.includes('upgrade') || msg === 'auth_limit_reached') {
                setCredits(0);
                setShowUpgradeModal(true);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;
        await submitMessage(input.trim());
    };

    const handleSuggestionClick = (prompt: string) => {
        submitMessage(prompt);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e as unknown as React.FormEvent);
        }
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <>
            <ConversionLimitModal
                isOpen={showLimitModal}
                onClose={() => setShowLimitModal(false)}
                anonymousSessionId={token ? undefined : sessionId}
                title="Has usado tus 3 consultas de prueba"
                description="Regístrate o inicia sesión para obtener 2 consultas más gratis."
            />
            <UpgradeModal
                isOpen={showUpgradeModal}
                onClose={() => setShowUpgradeModal(false)}
                title="Has completado tus 5 consultas gratuitas"
                description="Pásate a Premium para seguir usando el asistente de IA sin límites y acceder a más funciones."
            />
            <div
                className={`ai-chat-panel ai-chat-panel--docked ${isOpen ? 'ai-chat-panel--open' : ''} ${isMinimized ? 'minimized' : ''}`}
                aria-hidden={!isOpen}
                role="complementary"
                aria-label="Asistente de IA"
            >
                <div className="ai-chat-header">
                    <div className="ai-chat-header-left">
                        <div className="ai-chat-header-badge">
                            <span className="ai-chat-header-badge__icon" aria-hidden>
                                <MessageCircle size={20} strokeWidth={2} />
                                <Sparkles size={12} className="ai-chat-header-badge__sparkle" aria-hidden />
                            </span>
                            <span className="ai-chat-header-badge__label">DocAI</span>
                        </div>
                        <span className="ai-chat-status">
                            En línea • {isAdminUnlimited ? '∞' : `${credits} créditos`}
                        </span>
                    </div>
                    <div className="ai-chat-header-actions">
                        <button
                            type="button"
                            className="ai-chat-header-btn"
                            onClick={handleNewChat}
                            onMouseEnter={(e) => showTooltip(e.currentTarget, 'Nuevo chat')}
                            onMouseLeave={hideTooltip}
                            aria-label="Nuevo chat"
                        >
                            <Plus size={18} />
                        </button>
                        {token && (
                            <button
                                type="button"
                                className={`ai-chat-header-btn ${view === 'historial' ? 'active' : ''}`}
                                onClick={() => setView((v) => (v === 'historial' ? 'chat' : 'historial'))}
                                onMouseEnter={(e) => showTooltip(e.currentTarget, 'Historial')}
                                onMouseLeave={hideTooltip}
                                aria-label="Historial"
                            >
                                <History size={18} />
                            </button>
                        )}
                        <button
                            onClick={toggleMinimize}
                            className="ai-chat-btn"
                            onMouseEnter={(e) => showTooltip(e.currentTarget, isMinimized ? 'Maximizar' : 'Minimizar')}
                            onMouseLeave={hideTooltip}
                            aria-label={isMinimized ? 'Maximizar' : 'Minimizar'}
                        >
                            {isMinimized ? <Maximize2 size={18} /> : <Minimize2 size={18} />}
                        </button>
                        <button
                            onClick={handleClose}
                            className="ai-chat-btn"
                            onMouseEnter={(e) => showTooltip(e.currentTarget, 'Cerrar')}
                            onMouseLeave={hideTooltip}
                            aria-label="Cerrar"
                        >
                            <X size={18} />
                        </button>
                    </div>
                </div>

                {!isMinimized && (
                    <div className="ai-chat-body">
                        {view === 'historial' && token ? (
                            <ChatHistoryView
                                sessions={sessions}
                                onSelectSession={handleSelectSession}
                                onRename={handleRenameSession}
                                onDelete={handleDeleteSession}
                                loading={sessionsLoading}
                            />
                        ) : (
                        <div className="ai-chat-messages-wrap">
                            <div className="ai-chat-messages">
                                {messages.map((message) => (
                                    <div
                                        key={message.id}
                                        className={`ai-chat-message ${message.role}`}
                                    >
                                        <div className="ai-chat-message-content">
                                            {message.role === 'assistant' ? (
                                                <MarkdownMessage content={message.content} />
                                            ) : (
                                                message.content
                                            )}
                                        </div>
                                        <div className="ai-chat-message-time">
                                            {formatTime(message.timestamp)}
                                        </div>
                                    </div>
                                ))}
                                {loading && (
                                    <div className="ai-chat-message assistant">
                                        <div className="ai-chat-message-content">
                                            <Loader className="ai-chat-loader" size={16} />
                                            <span>IA está pensando…</span>
                                        </div>
                                    </div>
                                )}
                                {messages.length === 1 && messages[0].id === 'welcome' && (
                                    <>
                                    {!token && (
                                        <p className="ai-chat-register-hint">
                                            Regístrate para guardar tu historial de conversaciones
                                        </p>
                                    )}
                                    <div className="ai-chat-suggestions">
                                        {WELCOME_SUGGESTIONS.map((s) => (
                                            <button
                                                key={s.prompt}
                                                type="button"
                                                className="ai-chat-suggestion-btn"
                                                onClick={() => handleSuggestionClick(s.prompt)}
                                                disabled={loading || (credits <= 0 && !isAdminUnlimited)}
                                            >
                                                {s.label}
                                            </button>
                                        ))}
                                    </div>
                                    </>
                                )}
                                <div ref={messagesEndRef} />
                            </div>
                            <div className="ai-chat-input-container">
                                {credits <= 0 && !isAdminUnlimited && (
                                    <div className="ai-chat-warning">
                                        ⚠️{' '}
                                        {token
                                            ? 'No quedan créditos. Actualiza para continuar.'
                                            : 'No quedan créditos. Regístrate para obtener más.'}
                                    </div>
                                )}
                                {attachments.length > 0 && (
                                    <div className="ai-chat-attachments">
                                        {attachments.map((a) => (
                                            <span
                                                key={a.id}
                                                className="ai-chat-attachment-tag"
                                                title={a.filename}
                                            >
                                                {a.filename}
                                                <button
                                                    type="button"
                                                    onClick={() => removeAttachment(a.id)}
                                                    aria-label="Quitar"
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                )}
                                <form onSubmit={handleSubmit} className="ai-chat-input-form">
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept=".pdf,.docx,.doc,.txt"
                                        multiple
                                        className="ai-chat-file-input"
                                        onChange={handleFileSelect}
                                        style={{ display: 'none' }}
                                    />
                                    <button
                                        type="button"
                                        className="ai-chat-attach-btn"
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={loading || uploading}
                                        onMouseEnter={(e) => showTooltip(e.currentTarget, 'Adjuntar PDF, Word o TXT')}
                                        onMouseLeave={hideTooltip}
                                        aria-label="Adjuntar PDF, Word o TXT"
                                    >
                                        {uploading ? (
                                            <Loader className="ai-chat-loader" size={18} />
                                        ) : (
                                            <Paperclip size={18} />
                                        )}
                                    </button>
                                    <input
                                        ref={inputRef}
                                        type="text"
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyPress={handleKeyPress}
                                        placeholder="Pregúntame lo que quieras..."
                                        className="ai-chat-input"
                                        disabled={loading}
                                    />
                                    <button
                                        type="submit"
                                        disabled={!input.trim() || loading}
                                        className="ai-chat-send-btn"
                                        onMouseEnter={(e) => showTooltip(e.currentTarget, 'Enviar')}
                                        onMouseLeave={hideTooltip}
                                        aria-label="Enviar"
                                    >
                                        {loading ? (
                                            <Loader className="ai-chat-loader" size={20} />
                                        ) : (
                                            <Send size={20} />
                                        )}
                                    </button>
                                </form>
                            </div>
                        </div>
                        )}
                    </div>
                )}
            </div>

            {/* Tooltip - mismos colores que sidebar y resto del sitio */}
            {tooltip && (
                <div
                    className="ai-chat-tooltip"
                    style={{ left: tooltip.left, top: tooltip.top }}
                    role="tooltip"
                >
                    {tooltip.text}
                </div>
            )}
        </>
    );
};
