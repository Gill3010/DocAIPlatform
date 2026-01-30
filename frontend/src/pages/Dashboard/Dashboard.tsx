import { useState, useEffect, useMemo } from 'react';
import { BarChart3, Clock, CheckCircle, Zap, History, FileEdit } from 'lucide-react';
import { Link } from 'react-router-dom';
import { StatsCard } from '../../components/StatsCard/StatsCard';
import { QuickActionCard } from '../../components/QuickActionCard/QuickActionCard';
import { ConversionCard } from '../../components/ConversionCard/ConversionCard';
import { useAppStore } from '../../stores/appStore';
import { apiService } from '../../services/api';
import {
    getDashboardConversions,
    CONVERSION_CATEGORY_LABELS,
    type ConversionCategory
} from '../../constants/conversions';
import { filterConversionsByQuery } from '../../utils/searchConversions';
import { useDashboardSearch } from '../../contexts/DashboardSearchContext';
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

    const conversionTypes = useMemo(() => getDashboardConversions(), []);
    const { query: searchQuery } = useDashboardSearch();
    const filteredConversions = useMemo(
        () => filterConversionsByQuery(conversionTypes, searchQuery),
        [conversionTypes, searchQuery]
    );
    const conversionsByCategory = useMemo(() => {
        const map = new Map<ConversionCategory, typeof conversionTypes>();
        for (const c of filteredConversions) {
            const list = map.get(c.category) ?? [];
            list.push(c);
            map.set(c.category, list);
        }
        return map;
    }, [filteredConversions]);

    const otherActions = [
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

    const categoryOrder: ConversionCategory[] = ['document', 'image', 'web'];

    return (
        <div className="dashboard-page">
            <section className="stats-section">
                <div className="stats-grid">
                    {stats.map((stat, index) => (
                        <StatsCard key={index} {...stat} />
                    ))}
                </div>
            </section>

            <section className="conversions-section">
                <div className="section-header">
                    <h2 className="section-title">Conversiones disponibles</h2>
                    <Link to="/convert" className="section-link">
                        Ver todas
                    </Link>
                </div>
                {searchQuery.trim() && filteredConversions.length === 0 ? (
                    <p className="conversions-section__no-results">
                        No hay coincidencias. Prueba con «PDF», «Word» o «imagen».
                    </p>
                ) : (
                    <>
                        {searchQuery.trim() && (
                            <p className="conversions-section__count" aria-live="polite">
                                {filteredConversions.length} {filteredConversions.length === 1 ? 'resultado' : 'resultados'}
                            </p>
                        )}
                        {categoryOrder.map((category) => {
                            const list = conversionsByCategory.get(category);
                            if (!list?.length) return null;
                            return (
                                <div key={category} className="conversion-category">
                                    <h3 className="conversion-category__title">
                                        {CONVERSION_CATEGORY_LABELS[category]}
                                    </h3>
                                    <div className="conversion-cards-grid">
                                        {list.map((conv) => (
                                            <ConversionCard
                                                key={conv.id}
                                                sourceLabel={conv.sourceLabel}
                                                targetLabel={conv.targetLabel}
                                                icon={conv.icon}
                                                category={conv.category}
                                                href={`/convert?from=${encodeURIComponent(conv.primarySourceFormat)}&to=${encodeURIComponent(conv.targetId)}`}
                                            />
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </>
                )}
            </section>

            <section className="quick-actions-section">
                <h2 className="section-title">Otras acciones</h2>
                <div className="quick-actions-grid">
                    {otherActions.map((action, index) => (
                        <QuickActionCard key={index} {...action} />
                    ))}
                </div>
            </section>
        </div>
    );
};
