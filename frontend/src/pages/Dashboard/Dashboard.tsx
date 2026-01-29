import { useState, useEffect } from 'react';
import { BarChart3, Clock, CheckCircle, Zap, RefreshCw, History, FileEdit } from 'lucide-react';
import { StatsCard } from '../../components/StatsCard/StatsCard';
import { QuickActionCard } from '../../components/QuickActionCard/QuickActionCard';
import { useAppStore } from '../../stores/appStore';
import { apiService } from '../../services/api';
import './Dashboard.css';

export const Dashboard = () => {
    const { user } = useAppStore();
    const [stats, setStats] = useState([
        {
            icon: BarChart3,
            value: '...',
            label: 'Conversiones Totales',
            trend: { value: 0, isPositive: true },
            gradient: 'gradient-primary'
        },
        {
            icon: Clock,
            value: '...',
            label: 'Créditos Gratis',
            gradient: 'gradient-warning'
        },
        {
            icon: CheckCircle,
            value: '...',
            label: 'Tasa de Éxito',
            trend: { value: 0, isPositive: true },
            gradient: 'gradient-success'
        },
        {
            icon: Zap,
            value: '...',
            label: 'Tiempo Promedio',
            trend: { value: 0, isPositive: false },
            gradient: 'gradient-info'
        }
    ]);
    const [userName, setUserName] = useState('User');

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const data = await apiService.getUserStats();
            
            setUserName(data.user.name);
            
            setStats([
                {
                    icon: BarChart3,
                    value: data.conversions.total,
                    label: 'Conversiones Totales',
                    trend: { 
                        value: data.conversions.completed, 
                        isPositive: true 
                    },
                    gradient: 'gradient-primary'
                },
                {
                    icon: Clock,
                    value: data.credits.remaining,
                    label: 'Créditos Gratis',
                    gradient: 'gradient-warning'
                },
                {
                    icon: CheckCircle,
                    value: `${data.success_rate}%`,
                    label: 'Tasa de Éxito',
                    trend: { 
                        value: data.success_rate, 
                        isPositive: data.success_rate >= 80 
                    },
                    gradient: 'gradient-success'
                },
                {
                    icon: Zap,
                    value: data.avg_processing_time,
                    label: 'Tiempo Promedio',
                    trend: { 
                        value: 0, 
                        isPositive: true 
                    },
                    gradient: 'gradient-info'
                }
            ]);
        } catch (error) {
            console.error('Failed to load stats:', error);
            // Keep mock data on error
        }
    };

    const quickActions = [
        {
            icon: RefreshCw,
            title: 'Convertir Archivos',
            description: 'Transforma documentos entre formatos al instante con nuestro potente motor de conversión',
            buttonText: 'Comenzar a Convertir',
            href: '/convert',
            gradient: 'gradient-primary'
        },
        {
            icon: FileEdit,
            title: 'Formatear Manuscrito',
            description: 'Aplica formato profesional automático a tu manuscrito',
            buttonText: 'Formatear Ahora',
            href: '/format-manuscript',
            gradient: 'gradient-warm'
        },
        {
            icon: History,
            title: 'Historial de Conversiones',
            description: 'Accede y gestiona todas tus conversiones de documentos anteriores',
            buttonText: 'Ver Historial',
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
                <h2 className="section-title">Acciones Rápidas</h2>
                <div className="quick-actions-grid">
                    {quickActions.map((action, index) => (
                        <QuickActionCard key={index} {...action} />
                    ))}
                </div>
            </section>
        </div>
    );
};
