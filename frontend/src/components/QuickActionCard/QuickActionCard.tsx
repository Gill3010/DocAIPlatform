import type { LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import './QuickActionCard.css';

interface QuickActionCardProps {
    icon: LucideIcon;
    title: string;
    description: string;
    buttonText: string;
    href: string;
    gradient?: string;
}

export const QuickActionCard = ({
    icon: Icon,
    title,
    description,
    buttonText,
    href,
    gradient
}: QuickActionCardProps) => {
    return (
        <div className="quick-action-card">
            <div className={`action-icon-wrapper ${gradient || 'gradient-primary'}`}>
                <Icon className="action-icon" size={32} strokeWidth={2} />
            </div>
            <h3 className="action-title">{title}</h3>
            <p className="action-description">{description}</p>
            <Link to={href} className="action-button">
                {buttonText}
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            </Link>
        </div>
    );
};
