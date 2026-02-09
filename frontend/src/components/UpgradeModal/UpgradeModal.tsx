import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { CreditCard } from 'lucide-react';
import './UpgradeModal.css';

interface UpgradeModalProps {
    isOpen: boolean;
    onClose: () => void;
    /** Título del modal (por defecto: conversiones gratuitas) */
    title?: string;
    /** Texto descriptivo bajo el título */
    description?: string;
}

const DEFAULT_TITLE = 'Has completado tus 5 conversiones gratuitas';
const DEFAULT_DESCRIPTION =
    'Suscríbete para seguir convirtiendo documentos sin límites y acceder a más formatos.';

export const UpgradeModal = ({
    isOpen,
    onClose,
    title = DEFAULT_TITLE,
    description = DEFAULT_DESCRIPTION,
}: UpgradeModalProps) => {
    const navigate = useNavigate();
    const primaryBtnRef = useRef<HTMLAnchorElement>(null);

    // Dirigir foco al CTA principal al abrir (mejor conversión y accesibilidad)
    useEffect(() => {
        if (isOpen && primaryBtnRef.current) {
            const t = setTimeout(() => primaryBtnRef.current?.focus(), 100);
            return () => clearTimeout(t);
        }
    }, [isOpen]);

    const handleVerPlanes = () => {
        onClose();
        navigate('/pricing', { state: { fromModal: true, highlightPlan: 'Pro' } });
    };

    if (!isOpen) return null;

    return (
        <div className="upgrade-modal-overlay" onClick={onClose} role="presentation">
            <div
                className="upgrade-modal"
                onClick={(e) => e.stopPropagation()}
                role="dialog"
                aria-labelledby="upgrade-modal-title"
                aria-describedby="upgrade-modal-desc"
                aria-modal="true"
            >
                <h3 id="upgrade-modal-title" className="upgrade-modal__title">
                    {title}
                </h3>
                <p id="upgrade-modal-desc" className="upgrade-modal__text">
                    {description}
                </p>
                <ul className="upgrade-modal__benefits">
                    <li>Conversiones ilimitadas</li>
                    <li>Archivos hasta 50 MB</li>
                    <li>Formatos premium (CAD, JATS)</li>
                    <li>Historial de conversiones</li>
                </ul>
                <a
                    ref={primaryBtnRef}
                    href="/pricing"
                    className="upgrade-modal__btn"
                    onClick={(e) => {
                        e.preventDefault();
                        handleVerPlanes();
                    }}
                    aria-describedby="upgrade-modal-desc"
                >
                    <CreditCard size={18} />
                    Ver planes y precios
                </a>
                <button
                    type="button"
                    className="upgrade-modal__close"
                    onClick={onClose}
                    aria-label="Cerrar"
                >
                    Cerrar
                </button>
            </div>
        </div>
    );
};
