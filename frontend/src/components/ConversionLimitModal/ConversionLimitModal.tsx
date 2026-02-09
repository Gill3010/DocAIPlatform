import { useNavigate } from 'react-router-dom';
import { LogIn, UserPlus } from 'lucide-react';
import './ConversionLimitModal.css';

interface ConversionLimitModalProps {
    isOpen: boolean;
    onClose: () => void;
    /** Session ID anónima para vincular tras registro (asegura las 2 conversiones adicionales) */
    anonymousSessionId?: string | null;
    /** Título del modal (p. ej. "Has usado tus 3 consultas de prueba" para el asistente IA) */
    title?: string;
    /** Texto descriptivo (p. ej. "2 consultas más" para el asistente IA) */
    description?: string;
}

const DEFAULT_TITLE = 'Has usado tus 3 conversiones de prueba';
const DEFAULT_DESCRIPTION = 'Regístrate o inicia sesión para obtener 2 conversiones más gratis.';

export const ConversionLimitModal = ({ isOpen, onClose, anonymousSessionId, title = DEFAULT_TITLE, description = DEFAULT_DESCRIPTION }: ConversionLimitModalProps) => {
    const navigate = useNavigate();

    if (!isOpen) return null;

    const handleRegister = () => {
        onClose();
        navigate('/login', { state: { mode: 'register', anonymousSessionId: anonymousSessionId ?? undefined } });
    };

    const handleLogin = () => {
        onClose();
        navigate('/login', { state: { anonymousSessionId: anonymousSessionId ?? undefined } });
    };

    return (
        <div className="conversion-limit-modal-overlay" onClick={onClose} role="presentation">
            <div
                className="conversion-limit-modal"
                onClick={(e) => e.stopPropagation()}
                role="dialog"
                aria-labelledby="limit-modal-title"
                aria-modal="true"
            >
                <h3 id="limit-modal-title" className="conversion-limit-modal__title">
                    {title}
                </h3>
                <p className="conversion-limit-modal__text">
                    {description}
                </p>
                <div className="conversion-limit-modal__actions">
                    <button
                        type="button"
                        className="conversion-limit-modal__btn conversion-limit-modal__btn--primary"
                        onClick={handleRegister}
                    >
                        <UserPlus size={18} />
                        Crear cuenta gratis
                    </button>
                    <button
                        type="button"
                        className="conversion-limit-modal__btn conversion-limit-modal__btn--secondary"
                        onClick={handleLogin}
                    >
                        <LogIn size={18} />
                        Ya tengo cuenta
                    </button>
                </div>
                <button
                    type="button"
                    className="conversion-limit-modal__close"
                    onClick={onClose}
                    aria-label="Cerrar"
                >
                    Cerrar
                </button>
            </div>
        </div>
    );
};
