import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Tag } from 'lucide-react';
import { PaymentModal } from '../../components/Payment/PaymentModal';
import { useAppStore } from '../../stores/appStore';
import { apiService } from '../../services/api';
import { getToken } from '../../services/storageService';
import { setCheckoutIntent, getCheckoutIntent, removeCheckoutIntent } from '../../services/storageService';
import './Pricing.css';

const PLANS = [
    {
        id: 'Gratuito',
        name: 'Gratuito',
        price: 0,
        period: 'siempre',
        description: 'Ideal para probar la plataforma',
        features: ['5 conversiones gratuitas', 'Formatos básicos', 'Soporte por documentación'],
        recommended: false,
    },
    {
        id: 'Básico',
        name: 'Básico',
        price: 4.90,
        period: 'mes',
        description: 'Para uso personal y proyectos pequeños',
        features: ['50 conversiones/mes', 'Todos los formatos', 'Historial 30 días', 'Soporte por email'],
        recommended: false,
    },
    {
        id: 'Pro',
        name: 'Pro',
        price: 9.90,
        period: 'mes',
        description: 'Para equipos y uso profesional',
        features: ['Conversiones ilimitadas', 'Formatear manuscritos', 'Asistente IA', 'Historial 1 año', 'Soporte prioritario'],
        recommended: true,
    },
    {
        id: 'Empresa',
        name: 'Empresa',
        price: 29.90,
        period: 'mes',
        description: 'Soluciones a medida para organizaciones',
        features: ['Todo en Pro', 'API dedicada', 'Gestión de usuarios', 'SLA garantizado', 'Soporte 24/7'],
        recommended: false,
    },
];

export const Pricing = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const highlightPlanId = (location.state as { highlightPlan?: string } | null)?.highlightPlan;
    const fromModal = (location.state as { fromModal?: boolean } | null)?.fromModal;
    const recommendedCardRef = useRef<HTMLElement>(null);

    const [selectedPlan, setSelectedPlan] = useState<{ id: string; name: string; price: number; currency?: string } | null>(null);

    // Al llegar desde el modal de upgrade: scroll al plan recomendado y foco visual
    useEffect(() => {
        if (fromModal && highlightPlanId && recommendedCardRef.current) {
            const el = recommendedCardRef.current;
            const t = setTimeout(() => {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 150);
            return () => clearTimeout(t);
        }
    }, [fromModal, highlightPlanId]);

    // Tras login/registro: abrir modal de pago si hay intención pendiente
    useEffect(() => {
        const intent = getCheckoutIntent();
        const token = getToken();
        if (intent && token) {
            removeCheckoutIntent();
            setSelectedPlan({
                id: intent.planId,
                name: intent.planName,
                price: intent.planPrice,
                currency: intent.currency,
            });
        }
    }, []);

    const handleSelectPlan = (plan: typeof PLANS[0]) => {
        if (plan.price > 0) {
            const token = getToken();
            if (!token) {
                setCheckoutIntent({
                    planId: plan.id,
                    planName: plan.name,
                    planPrice: plan.price,
                    currency: plan.currency,
                });
                navigate('/login', { state: { returnTo: '/pricing', checkoutPlan: plan.id }, replace: false });
                return;
            }
            setSelectedPlan(plan);
        }
    };

    return (
        <div className="pricing-page">
            <header className="pricing-header">
                <Tag size={32} className="pricing-header__icon" aria-hidden />
                <h1 className="pricing-page__title">Precios</h1>
                <p className="pricing-page__intro">
                    Planes orientados a distintos usos. Los precios mostrados son orientativos y pueden variar.
                </p>
            </header>

            <div className="pricing-grid">
                {PLANS.map((plan) => {
                    const isRecommended = plan.recommended;
                    const isHighlight = highlightPlanId === plan.id;
                    return (
                        <article
                            key={plan.name}
                            ref={isRecommended ? recommendedCardRef : undefined}
                            className={`pricing-card ${isRecommended ? 'pricing-card--recommended' : ''} ${isHighlight && fromModal ? 'pricing-card--highlight' : ''}`}
                            id={plan.id === highlightPlanId ? `plan-${plan.id}` : undefined}
                        >
                            {isRecommended && (
                                <span className="pricing-card__badge" aria-hidden>Recomendado</span>
                            )}
                            <h2 className="pricing-card__name">{plan.name}</h2>
                            <div className="pricing-card__price">
                                <span className="pricing-card__amount">
                                    {plan.price === 0 ? '0' : `$${plan.price}`}
                                </span>
                                <span className="pricing-card__period">/{plan.period}</span>
                            </div>
                            <p className="pricing-card__desc">{plan.description}</p>
                            <ul className="pricing-card__features">
                                {plan.features.map((f) => (
                                    <li key={f}>{f}</li>
                                ))}
                            </ul>
                            <button
                                type="button"
                                className={`pricing-card__cta ${isRecommended ? 'pricing-card__cta--primary' : ''}`}
                                disabled={false} // Enable button
                                onClick={() => handleSelectPlan(plan)}
                            >
                                {plan.price === 0 ? 'Plan Actual' : (isRecommended ? 'Elegir Pro' : 'Elegir ' + plan.name)}
                            </button>
                        </article>
                    );
                })}
            </div>

            <p className="pricing-disclaimer">
                Los precios y condiciones están sujetos a cambios. Contáctanos para ofertas personalizadas.
            </p>

            {selectedPlan && (
                <div style={{ position: 'fixed', zIndex: 1000 }}>
                    {/* Lazy load or direct import PaymentModal */}
                    {/* Assuming PaymentModal is imported at top */}
                    <PaymentModal
                        plan={selectedPlan}
                        onClose={() => setSelectedPlan(null)}
                        onSuccess={async () => {
                            try {
                                // Refresh user profile in global store
                                const updatedUser = await apiService.getCurrentUser();
                                useAppStore.getState().setUser(updatedUser);

                                setSelectedPlan(null);
                                // Forzar navegación al dashboard para ver los cambios
                                navigate('/dashboard');
                            } catch (e) {
                                console.error("Error refreshing user state", e);
                                setSelectedPlan(null);
                            }
                        }}
                    />
                </div>
            )}
        </div>
    );
};
