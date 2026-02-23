import { useMemo } from 'react';
import { History, FileEdit, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAppStore } from '../../stores/appStore';

import { QuickActionCard } from '../../components/QuickActionCard/QuickActionCard';
import { ConversionCard } from '../../components/ConversionCard/ConversionCard';
import { ValueBanner } from '../../components/ValueBanner/ValueBanner';
import { ConversionSearch } from '../../components/ConversionSearch/ConversionSearch';
import {
    getDashboardConversions,
    CONVERSION_CATEGORY_LABELS,
    PDF_TOOLS,
    PDF_TOOLS_LABEL,
    PDF_TOOLS_OPERATIONAL,
    type ConversionCategory
} from '../../constants/conversions';
import { filterConversionsByQuery, filterPdfToolsByQuery } from '../../utils/searchConversions';
import { useDashboardSearch } from '../../contexts/DashboardSearchContext';
import './Dashboard.css';

export const Dashboard = () => {
    const { token } = useAppStore();
    const isAnonymous = !token;

    const conversionTypes = useMemo(() => getDashboardConversions(), []);
    const { query: searchQuery, setQuery: setSearchQuery } = useDashboardSearch();
    const filteredConversions = useMemo(
        () => filterConversionsByQuery(conversionTypes, searchQuery),
        [conversionTypes, searchQuery]
    );
    const filteredPdfTools = useMemo(
        () => filterPdfToolsByQuery(PDF_TOOLS, searchQuery),
        [searchQuery]
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
            icon: FileText,
            title: 'Editor Colaborativo',
            description: 'Accede a tus documentos y edítalos con otros en tiempo real',
            buttonText: 'Ver Mis Documentos',
            href: '/documents',
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
            gradient: 'gradient-primary'
        }
    ];

    const categoryOrder: ConversionCategory[] = ['document', 'image', 'web'];

    return (
        <div className="dashboard-page">
            <section className="dashboard-value-banner" aria-label="Descubre DocAI Platform">
                <ValueBanner />
            </section>

            <section className="dashboard-search-section">
                <ConversionSearch
                    query={searchQuery}
                    onQueryChange={setSearchQuery}
                    filteredConversions={filteredConversions}
                />
            </section>

            <section className="conversions-section">
                <div className="section-header">
                    <h2 className="section-title">Conversiones disponibles</h2>
                    <Link to="/convert" className="section-link">
                        Ver todas
                    </Link>
                </div>
                {searchQuery.trim() && filteredConversions.length === 0 && filteredPdfTools.length === 0 ? (
                    <p className="conversions-section__no-results">
                        No hay coincidencias. Prueba con «PDF», «Word» o «imagen».
                    </p>
                ) : (
                    <>
                        {searchQuery.trim() && (
                            <p className="conversions-section__count" aria-live="polite">
                                {filteredConversions.length + filteredPdfTools.length} {(filteredConversions.length + filteredPdfTools.length) === 1 ? 'resultado' : 'resultados'}
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
                                                tooltip={conv.tooltip}
                                            />
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                        {filteredPdfTools.length > 0 && (
                            <div className="conversion-category">
                                <h3 className="conversion-category__title">
                                    {PDF_TOOLS_LABEL}
                                </h3>
                                <div className="conversion-cards-grid">
                                    {filteredPdfTools.map((tool) => (
                                        <ConversionCard
                                            key={tool.id}
                                            sourceLabel="PDF"
                                            targetLabel={tool.name}
                                            icon={tool.icon}
                                            category="document"
                                            href={PDF_TOOLS_OPERATIONAL.includes(tool.id) ? `/pdf-tools?tool=${encodeURIComponent(tool.id)}` : '#'}
                                            comingSoon={!PDF_TOOLS_OPERATIONAL.includes(tool.id)}
                                            ctaLabel={PDF_TOOLS_OPERATIONAL.includes(tool.id) ? 'Usar' : undefined}
                                            tooltip={tool.tooltip}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                )}
            </section>

            {!isAnonymous && (
                <section className="recent-history-section">
                    <div className="section-header">
                        <h2 className="section-title">Historial Reciente</h2>
                        <Link to="/history" className="section-link">Ver todo el historial</Link>
                    </div>
                    <div className="recent-conversions-list">
                        {/* 
                          Note: In a real app we'd fetch this. 
                          For now, the summary already exists in the stats or we could fetch it.
                          I'll just add a placeholder or hint that they can find it in 'Mis Documentos'
                        */}
                        <div className="recent-hint-card">
                            <p>Tus archivos convertidos ahora están disponibles para edición colaborativa.</p>
                            <Link to="/documents" className="btn-primary-outline">Ir a Mis Documentos</Link>
                        </div>
                    </div>
                </section>
            )}

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
