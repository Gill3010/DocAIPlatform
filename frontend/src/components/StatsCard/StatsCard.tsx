import type { LucideIcon } from 'lucide-react';
import './StatsCard.css';

interface StatsCardProps {
    icon: LucideIcon;
    value: string | number;
    label: string;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    gradient?: string;
    /** Reduce padding and font size for compact layout (e.g. dashboard summary) */
    compact?: boolean;
}

export const StatsCard = ({ icon: Icon, value, label, trend, gradient, compact }: StatsCardProps) => {
    return (
        <div className={`stats-card ${compact ? 'stats-card--compact' : ''}`}>
            <div className={`stats-icon-wrapper ${gradient || 'gradient-primary'}`}>
                <Icon className="stats-icon" size={compact ? 20 : 24} strokeWidth={2} />
            </div>
            <div className="stats-content">
                <div className="stats-header">
                    <h3 className="stats-value">{value}</h3>
                    {trend && (
                        <span className={`stats-trend ${trend.isPositive ? 'positive' : 'negative'}`}>
                            {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
                        </span>
                    )}
                </div>
                <p className="stats-label">{label}</p>
            </div>
        </div>
    );
};
