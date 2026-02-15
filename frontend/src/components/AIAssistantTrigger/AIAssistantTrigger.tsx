import { MessageCircle, Sparkles } from 'lucide-react';
import './AIAssistantTrigger.css';

interface AIAssistantTriggerProps {
    onClick: () => void;
    isOpen?: boolean;
    /** Optional badge (e.g. credits count); hidden when undefined */
    badge?: number | '∞';
}

export const AIAssistantTrigger = ({ onClick, isOpen = false, badge }: AIAssistantTriggerProps) => {
    return (
        <button
            type="button"
            className={`ai-assistant-trigger ${isOpen ? 'ai-assistant-trigger--open' : ''}`}
            onClick={onClick}
            aria-label="Abrir asistente de IA"
            aria-expanded={isOpen}
        >
            <span className="ai-assistant-trigger__icon" aria-hidden>
                <MessageCircle size={20} strokeWidth={2} />
                <Sparkles size={12} className="ai-assistant-trigger__sparkle" aria-hidden />
            </span>
            <span className="ai-assistant-trigger__label">DocAI</span>
            {badge !== undefined && (
                <span className="ai-assistant-trigger__badge" aria-hidden>
                    {badge === '∞' ? '∞' : badge}
                </span>
            )}
        </button>
    );
};
