import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import { useDashboardMetrics } from '../../hooks/useDashboardMetrics';
import { MetricsSummary } from '../MetricsSummary/MetricsSummary';
import './MetricsModal.css';

export function MetricsModal() {
    const { isMetricsModalOpen, closeMetricsModal } = useAppStore();
    const { stats, chartData, isLoading, loadStats } = useDashboardMetrics();
    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isMetricsModalOpen) {
            loadStats();
        }
    }, [isMetricsModalOpen]);

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') closeMetricsModal();
        };
        if (isMetricsModalOpen) {
            document.addEventListener('keydown', handleEscape);
            document.body.style.overflow = 'hidden';
        }
        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = '';
        };
    }, [isMetricsModalOpen, closeMetricsModal]);

    if (!isMetricsModalOpen) return null;

    const content = (
        <div
            className="metrics-modal-overlay"
            onClick={(e) => e.target === e.currentTarget && closeMetricsModal()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="metrics-modal-title"
        >
            <div className="metrics-modal" ref={modalRef} onClick={(e) => e.stopPropagation()}>
                <div className="metrics-modal__header">
                    <h2 id="metrics-modal-title" className="metrics-modal__title">
                        Tu resumen
                    </h2>
                    <button
                        type="button"
                        className="metrics-modal__close"
                        onClick={closeMetricsModal}
                        aria-label="Cerrar"
                    >
                        <X size={20} />
                    </button>
                </div>
                <div className="metrics-modal__body">
                    {isLoading ? (
                        <div className="metrics-modal__loading">Cargando métricas...</div>
                    ) : (
                        <MetricsSummary stats={stats} chartData={chartData} />
                    )}
                </div>
            </div>
        </div>
    );

    return createPortal(content, document.body);
}
