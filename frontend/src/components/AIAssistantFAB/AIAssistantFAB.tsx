import { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, X, Minimize2, Maximize2, Loader } from 'lucide-react';
import { apiService } from '../../services/api';
import './AIAssistantFAB.css';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export const AIAssistantFAB = () => {
    const [isOpen, setIsOpen] = useState(false);
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
                const stats = await apiService.getUserStats();
                setCredits(stats.credits.remaining);
            } catch (error) {
                console.error('Failed to load credits:', error);
            }
        };
        loadCredits();
    }, []);

    const toggleOpen = () => {
        setIsOpen(!isOpen);
        if (!isOpen) {
            setIsMinimized(false);
        }
    };

    const toggleMinimize = () => {
        setIsMinimized(!isMinimized);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading || credits <= 0) return;

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
            const response = await apiService.sendChatMessage(userMessage.content);

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.message,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);
            setCredits(response.credits_remaining);
        } catch (error: any) {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: `❌ ${error.message || 'Lo siento, encontré un error. Por favor intenta de nuevo.'}`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
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
            {/* FAB Button */}
            <button
                className={`ai-fab ${isOpen ? 'open' : ''}`}
                onClick={toggleOpen}
                title="Asistente de IA"
            >
                {isOpen ? <X size={24} /> : <Sparkles size={24} />}
                {credits > 0 && !isOpen && (
                    <span className="ai-fab-badge">{credits}</span>
                )}
            </button>

            {/* Chat Panel */}
            {isOpen && (
                <div className={`ai-chat-panel ${isMinimized ? 'minimized' : ''}`}>
                    {/* Header */}
                    <div className="ai-chat-header">
                        <div className="ai-chat-header-left">
                            <Sparkles size={20} className="ai-chat-icon" />
                            <div>
                                <h3>Asistente de IA</h3>
                                <span className="ai-chat-status">En línea • {credits} créditos</span>
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
                                onClick={toggleOpen}
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
                                {credits <= 0 && (
                                    <div className="ai-chat-warning">
                                        ⚠️ No quedan créditos. Actualiza para continuar.
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
                                        disabled={loading || credits <= 0}
                                    />
                                    <button
                                        type="submit"
                                        disabled={!input.trim() || loading || credits <= 0}
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
            )}
        </>
    );
};
