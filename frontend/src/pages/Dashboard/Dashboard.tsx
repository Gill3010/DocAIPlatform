import { BarChart3, Clock, CheckCircle, Zap, RefreshCw, Bot, History } from 'lucide-react';
import { StatsCard } from '../../components/StatsCard/StatsCard';
import { QuickActionCard } from '../../components/QuickActionCard/QuickActionCard';
import { useAppStore } from '../../stores/appStore';
import './Dashboard.css';

export const Dashboard = () => {
    const { user } = useAppStore();

    const stats = [
        {
            icon: BarChart3,
            value: 12,
            label: 'Total Conversions',
            trend: { value: 12, isPositive: true },
            gradient: 'gradient-primary'
        },
        {
            icon: Clock,
            value: user ? 3 - user.free_conversion_count : 3,
            label: 'Free Credits Left',
            gradient: 'gradient-warning'
        },
        {
            icon: CheckCircle,
            value: '95%',
            label: 'Success Rate',
            trend: { value: 5, isPositive: true },
            gradient: 'gradient-success'
        },
        {
            icon: Zap,
            value: '2.4s',
            label: 'Avg. Processing Time',
            trend: { value: 8, isPositive: false },
            gradient: 'gradient-info'
        }
    ];

    const quickActions = [
        {
            icon: RefreshCw,
            title: 'Convert Files',
            description: 'Transform documents between formats instantly with our powerful conversion engine',
            buttonText: 'Start Converting',
            href: '/convert',
            gradient: 'gradient-primary'
        },
        {
            icon: Bot,
            title: 'AI Assistant',
            description: 'Get intelligent help with document formatting, editing, and optimization',
            buttonText: 'Ask AI',
            href: '/ai-assistant',
            gradient: 'gradient-success'
        },
        {
            icon: History,
            title: 'Conversion History',
            description: 'Access and manage all your previous document conversions',
            buttonText: 'View History',
            href: '/history',
            gradient: 'gradient-info'
        }
    ];

    return (
        <div className="dashboard-page">
            <section className="stats-section">
                <div className="stats-grid">
                    {stats.map((stat, index) => (
                        <StatsCard key={index} {...stat} />
                    ))}
                </div>
            </section>

            <section className="quick-actions-section">
                <h2 className="section-title">Quick Actions</h2>
                <div className="quick-actions-grid">
                    {quickActions.map((action, index) => (
                        <QuickActionCard key={index} {...action} />
                    ))}
                </div>
            </section>
        </div>
    );
};
