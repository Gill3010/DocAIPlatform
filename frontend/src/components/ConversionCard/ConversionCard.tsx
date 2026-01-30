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
}

const CATEGORY_GRADIENT: Record<ConversionCategory, string> = {
    document: 'gradient-primary',
    image: 'gradient-info',
    web: 'gradient-warm'
};

export const ConversionCard = ({
    sourceLabel,
    targetLabel,
    icon: Icon,
    category,
    href
}: ConversionCardProps) => {
    return (
        <Link to={href} className="conversion-card">
            <div className={`conversion-card__icon-wrapper ${CATEGORY_GRADIENT[category]}`}>
                <Icon className="conversion-card__icon" size={28} strokeWidth={2} />
            </div>
            <div className="conversion-card__labels">
                <span className="conversion-card__source">{sourceLabel}</span>
                <ArrowRight size={16} className="conversion-card__arrow" aria-hidden />
                <span className="conversion-card__target">{targetLabel}</span>
            </div>
            <span className="conversion-card__cta">Convertir</span>
        </Link>
    );
};
