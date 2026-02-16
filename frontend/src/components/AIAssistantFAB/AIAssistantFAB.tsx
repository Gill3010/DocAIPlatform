import { useState, useEffect, useRef } from 'react';
import { Send, X, Minimize2, Maximize2, Loader } from 'lucide-react';
import { apiService } from '../../services/api';
import { useAppStore } from '../../stores/appStore';
import { useAnonymousSession } from '../../hooks/useAnonymousSession';
import { ConversionLimitModal } from '../ConversionLimitModal/ConversionLimitModal';
import { UpgradeModal } from '../UpgradeModal/UpgradeModal';
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

export const AIAssistantFAB = ({ isOpen, onOpenChange }: AIAssistantFABProps) => {
    const { token, user } = useAppStore();
    const isAdminUnlimited = user?.is_superuser === true || user?.can_access_admin_panel === true || user?.is_premium === true;
    const { sessionId, syncFromCreditsRemaining } = useAnonymousSession();
    const [isMinimized, setIsMinimized] = useState(false);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: '👋 ¡Hola! Soy tu Asistente de IA. Puedo ayudarte con:\n\n• Cómo usar la aplicación\n• Consejos de conversión de archivos\n• Recomendaciones de formato\n• Cualquier pregunta sobre tus documentos\n\n¿En qué puedo ayudarte?',
            timestamp: new Date()
        }
    ]);
    const [credits, setCredits] = useState(10);
    const [showLimitModal, setShowLimitModal] = useState(false);
    const [showUpgradeModal, setShowUpgradeModal] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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
                // Registrado: mismo pool que conversiones (5 total) → 6.ª consulta muestra modal upgrade
                // Anónimo: 3 consultas → 4.ª consulta muestra modal registro
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

    const handleClose = () => {
        onOpenChange(false);
        setIsMinimized(false);
    };

    const toggleMinimize = () => {
        setIsMinimized(!isMinimized);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading) return;
        // Anónimo con 0 créditos: al intentar la 4.ª consulta → modal de registro
        if (!token && credits <= 0) {
            setShowLimitModal(true);
            return;
        }
        // Registrado con 0 créditos: al intentar la 6.ª consulta → modal de upgrade (Pasa a Premium)
        if (token && credits <= 0) {
            setShowUpgradeModal(true);
            return;
        }

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await apiService.sendChatMessage(
                userMessage.content,
                token ? undefined : sessionId
            );

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.message,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);
            setCredits(response.credits_remaining);
            if (!token && response.credits_remaining !== undefined) {
                syncFromCreditsRemaining(response.credits_remaining);
            }
        } catch (error: any) {
            const msg = error?.message || '';
            const friendly = msg === 'anonymous_limit_reached'
                ? 'No quedan créditos. Regístrate para obtener más.'
                : msg || 'Lo siento, encontré un error. Por favor intenta de nuevo.';
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: `❌ ${friendly}`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
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

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e as any);
        }
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
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
            {/* Panel dockeado a la derecha: misma altura que el menú izquierdo, fijo al scroll (trigger en header) */}
            <div
                className={`ai-chat-panel ai-chat-panel--docked ${isOpen ? 'ai-chat-panel--open' : ''} ${isMinimized ? 'minimized' : ''}`}
                aria-hidden={!isOpen}
                role="complementary"
                aria-label="Asistente de IA"
            >
                {/* Header */}
                <div className="ai-chat-header">
                    <div className="ai-chat-header-left">
                        <div className="ai-chat-avatar-wrapper">
                            <img
                                src="/ai-assistant-avatar.png"
                                alt=""
                                className="ai-chat-avatar"
                            />
                        </div>
                        <div>
                            <h3>Asistente de IA</h3>
                            <span className="ai-chat-status">En línea • {isAdminUnlimited ? '∞' : `${credits} créditos`}</span>
                        </div>
                    </div>
                    <div className="ai-chat-header-actions">
                        <button
                            onClick={toggleMinimize}
                            className="ai-chat-btn"
                            title={isMinimized ? 'Maximizar' : 'Minimizar'}
                        >
                            {isMinimized ? <Maximize2 size={18} /> : <Minimize2 size={18} />}
                        </button>
                        <button
                            onClick={handleClose}
                            className="ai-chat-btn"
                            title="Cerrar"
                        >
                            <X size={18} />
                        </button>
                    </div>
                </div>

                {!isMinimized && (
                    <>
                        {/* Messages */}
                        <div className="ai-chat-messages">
                            {messages.map((message) => (
                                <div
                                    key={message.id}
                                    className={`ai-chat-message ${message.role}`}
                                >
                                    <div className="ai-chat-message-content">
                                        {message.content}
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
                                        <span>IA está pensando...</span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input */}
                        <div className="ai-chat-input-container">
                            {credits <= 0 && !isAdminUnlimited && (
                                <div className="ai-chat-warning">
                                    ⚠️ {token ? 'No quedan créditos. Actualiza para continuar.' : 'No quedan créditos. Regístrate para obtener más.'}
                                </div>
                            )}
                            <form onSubmit={handleSubmit} className="ai-chat-input-form">
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
                                >
                                    {loading ? (
                                        <Loader className="ai-chat-loader" size={20} />
                                    ) : (
                                        <Send size={20} />
                                    )}
                                </button>
                            </form>
                        </div>
                    </>
                )}
            </div>
        </>
    );
};
