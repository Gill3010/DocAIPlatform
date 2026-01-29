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
}

export const StatsCard = ({ icon: Icon, value, label, trend, gradient }: StatsCardProps) => {
    return (
        <div className="stats-card">
            <div className={`stats-icon-wrapper ${gradient || 'gradient-primary'}`}>
                <Icon className="stats-icon" size={24} strokeWidth={2} />
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
