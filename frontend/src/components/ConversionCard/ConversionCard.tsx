import type { LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import type { ConversionCategory } from '../../constants/conversions';
import './ConversionCard.css';

interface ConversionCardProps {
    sourceLabel: string;
    targetLabel: string;
    icon: LucideIcon;
    category: ConversionCategory;
    href: string;
    /** Si true, no es enlace y muestra "Próximamente" (herramientas PDF no implementadas). */
    comingSoon?: boolean;
    /** Texto del CTA (por defecto "Convertir" o "Próximamente"). Para herramientas PDF operativas usar "Usar". */
    ctaLabel?: string;
    /** Tooltip informativo que aparece al pasar el cursor */
    tooltip?: string;
}

const CATEGORY_GRADIENT: Record<ConversionCategory, string> = {
    document: 'gradient-primary',
    image: 'gradient-primary',
    web: 'gradient-warm'
};

const PDF_TOOLS_GRADIENT = 'gradient-warm';

export const ConversionCard = ({
    sourceLabel,
    targetLabel,
    icon: Icon,
    category,
    href,
    comingSoon = false,
    ctaLabel,
    tooltip
}: ConversionCardProps) => {
    const gradient = comingSoon ? PDF_TOOLS_GRADIENT : CATEGORY_GRADIENT[category];
    const cta = ctaLabel ?? (comingSoon ? 'Próximamente' : 'Convertir');
    const content = (
        <>
            <div className="conversion-card__deco" aria-hidden="true" />
            <div className={`conversion-card__icon-wrapper ${gradient}`}>
                <Icon className="conversion-card__icon" size={28} strokeWidth={2} />
            </div>
            <div className="conversion-card__labels">
                <span className="conversion-card__source">{sourceLabel}</span>
                <ArrowRight size={16} className="conversion-card__arrow" aria-hidden />
                <span className="conversion-card__target">{targetLabel}</span>
            </div>
            <span className="conversion-card__cta">
                {(cta === 'Convertir' || cta === 'Usar') ? (
                    <span className="conversion-card__cta-btn" aria-hidden="true">{cta}</span>
                ) : (
                    cta
                )}
            </span>
            {tooltip && (
                <span className="conversion-card__tooltip" role="tooltip">
                    {tooltip}
                </span>
            )}
        </>
    );
    if (comingSoon) {
        return (
            <div 
                className="conversion-card conversion-card--disabled conversion-card--has-tooltip" 
                aria-disabled="true"
                aria-describedby={tooltip ? 'tooltip' : undefined}
            >
                {content}
            </div>
        );
    }
    return (
        <Link 
            to={href} 
            className="conversion-card conversion-card--has-tooltip"
            aria-describedby={tooltip ? 'tooltip' : undefined}
        >
            {content}
        </Link>
    );
};
