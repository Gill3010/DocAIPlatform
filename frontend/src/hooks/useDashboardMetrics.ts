import { useState, useEffect, useCallback } from 'react';
import { BarChart3, Clock, CheckCircle, Zap } from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { useAnonymousSession } from './useAnonymousSession';
import { apiService } from '../services/api';

const INITIAL_STATS = [
    { icon: BarChart3, value: '...', label: 'Conversiones Totales', trend: { value: 0, isPositive: true }, gradient: 'gradient-primary' as const },
    { icon: Clock, value: '...', label: 'Créditos', gradient: 'gradient-warning' as const },
    { icon: CheckCircle, value: '...', label: 'Tasa de Éxito', trend: { value: 0, isPositive: true }, gradient: 'gradient-success' as const },
    { icon: Zap, value: '...', label: 'Tiempo Promedio', trend: { value: 0, isPositive: false }, gradient: 'gradient-info' as const },
];

const INITIAL_CHART = { successRate: null, creditsRemaining: 0, creditsTotal: 0, creditsUnlimited: false };

export type StatsItem = typeof INITIAL_STATS[0];
export type ChartData = typeof INITIAL_CHART;

export function useDashboardMetrics() {
    const { token, user } = useAppStore();
    const { creditsRemaining: anonRemaining, anonymousLimit, anonymousConversionsUsed, sessionId: anonSessionId } = useAnonymousSession();
    const isAnonymous = !token;
    const isPremiumUser = user?.is_superuser === true || user?.is_premium === true;

    const [stats, setStats] = useState<StatsItem[]>(INITIAL_STATS);
    const [chartData, setChartData] = useState<ChartData>(INITIAL_CHART);
    const [isLoading, setIsLoading] = useState(true);

    const loadStats = useCallback(async () => {
        setIsLoading(true);
        if (isAnonymous) {
            try {
                const anonData = await apiService.getAnonymousStats(anonSessionId);
                setStats([
                    { icon: BarChart3, value: String(anonymousConversionsUsed), label: 'Conversiones Totales', trend: { value: 0, isPositive: true }, gradient: 'gradient-primary' },
                    { icon: Clock, value: `${anonRemaining} de ${anonymousLimit}`, label: 'Créditos', gradient: 'gradient-warning' },
                    { icon: CheckCircle, value: `${anonData.success_rate}%`, label: 'Tasa de Éxito', trend: { value: anonData.success_rate, isPositive: anonData.success_rate >= 80 }, gradient: 'gradient-success' },
                    { icon: Zap, value: anonData.avg_processing_time, label: 'Tiempo Promedio', gradient: 'gradient-info' },
                ]);
                setChartData({
                    successRate: anonData.success_rate,
                    creditsRemaining: anonRemaining,
                    creditsTotal: anonymousLimit,
                    creditsUnlimited: false,
                });
            } catch {
                /* ignore */
            } finally {
                setIsLoading(false);
            }
            return;
        }
        try {
            const updatedUser = await apiService.getCurrentUser();
            useAppStore.getState().setUser(updatedUser);
            const data = await apiService.getUserStats();
            const isPremium = data.credits.is_premium || updatedUser.is_premium || updatedUser.is_superuser;
            const planId = updatedUser.premium_plan_id || data.user.premium_plan_id;
            const isUnlimited = updatedUser.is_superuser || (isPremium && planId !== 'Básico');
            const creditsDisplay = isUnlimited ? '∞' : `${data.credits.remaining} de ${data.credits.limit}`;

            setStats([
                { icon: BarChart3, value: data.conversions.total, label: 'Conversiones Totales', trend: { value: data.conversions.completed, isPositive: true }, gradient: 'gradient-primary' },
                { icon: Clock, value: creditsDisplay, label: 'Créditos', gradient: 'gradient-warning' },
                { icon: CheckCircle, value: `${data.success_rate}%`, label: 'Tasa de Éxito', trend: { value: data.success_rate, isPositive: data.success_rate >= 80 }, gradient: 'gradient-success' },
                { icon: Zap, value: data.avg_processing_time, label: 'Tiempo Promedio', gradient: 'gradient-info' },
            ]);
            setChartData({
                successRate: data.success_rate,
                creditsRemaining: data.credits.remaining,
                creditsTotal: data.credits.limit,
                creditsUnlimited: isUnlimited,
            });
        } catch (error) {
            console.error('Failed to load stats:', error);
            setChartData((prev) => ({ ...prev, successRate: null }));
        } finally {
            setIsLoading(false);
        }
    }, [isAnonymous, anonRemaining, anonymousLimit, anonymousConversionsUsed, anonSessionId]);

    useEffect(() => {
        loadStats();
    }, [loadStats]);

    return { stats, chartData, isLoading, loadStats };
}
