import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { BarChart3, Clock, CheckCircle, Zap } from 'lucide-react';
import './MetricsSummary.css';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale);

interface MetricsSummaryProps {
    stats: {
        label: string;
        value: string | number;
        icon: any;
        trend?: { value: number; isPositive: boolean };
        gradient?: string;
    }[];
    chartData: {
        successRate: number | null;
        creditsRemaining: number;
        creditsTotal: number;
        creditsUnlimited: boolean;
    };
}

export function MetricsSummary({ stats, chartData }: MetricsSummaryProps) {
    // Conversiones Totales (first stat)
    const totalConversions = stats[0];
    // Tiempo Promedio (last stat)
    const avgTime = stats[3];

    // Success Rate Chart Data
    const successRateValue = chartData.successRate ?? 0;
    const successRateData = {
        labels: ['Éxito', 'Otros'],
        datasets: [
            {
                data: [successRateValue, 100 - successRateValue],
                backgroundColor: ['#2ECC71', 'rgba(0, 0, 0, 0.05)'], // Success green, subtle grey
                borderWidth: 0,
                cutout: '75%',
            },
        ],
    };

    // Credits Chart Data
    const creditsUsed = chartData.creditsUnlimited ? 0 : Math.max(0, chartData.creditsTotal - chartData.creditsRemaining);
    const creditsRemaining = chartData.creditsUnlimited ? 1 : chartData.creditsRemaining;
    const creditsTotal = chartData.creditsUnlimited ? 1 : chartData.creditsTotal;

    // Visual fix: if unlimited, show full circle. If not, show usage.
    const creditsData = {
        labels: ['Disponibles', 'Usados'],
        datasets: [
            {
                data: [creditsRemaining, creditsUsed],
                backgroundColor: ['#FF8C42', 'rgba(0, 0, 0, 0.05)'], // Warning orange, subtle grey
                borderWidth: 0,
                cutout: '75%',
            },
        ],
    };

    const chartOptions = {
        plugins: {
            legend: { display: false },
            tooltip: { enabled: false }, // Disable tooltip for clean look or enable if needed
        },
        maintainAspectRatio: false,
        cutout: '75%',
    };

    return (
        <div className="metrics-summary">
            {/* Widget 1: Total Conversions (Highlight) */}
            <div className="metric-widget metric-widget--primary">
                <div className="metric-widget__header">
                    <h3 className="metric-widget__title">{totalConversions.label}</h3>
                    <BarChart3 className="metric-widget__icon" size={20} />
                </div>
                <div className="metric-widget__content">
                    <span className="metric-widget__value">{totalConversions.value}</span>
                    {totalConversions.trend && (
                        <span className="metric-widget__subtext">
                            {totalConversions.trend.isPositive ? '+' : ''}{totalConversions.trend.value} recientes
                        </span>
                    )}
                </div>
            </div>

            {/* Widget 2: Credits (Doughnut) */}
            <div className="metric-widget metric-widget--chart">
                <div className="metric-widget__header" style={{ width: '100%' }}>
                    <h3 className="metric-widget__title">Créditos</h3>
                    <Clock className="metric-widget__icon" size={20} />
                </div>
                <div className="metric-widget__chart-container">
                    <Doughnut data={creditsData} options={chartOptions} />
                    <div className="chart-center-label">
                        <span className="chart-center-value">
                            {chartData.creditsUnlimited ? '∞' : chartData.creditsRemaining}
                        </span>
                    </div>
                </div>
                <span className="metric-widget__subtext">
                    {chartData.creditsUnlimited ? 'Ilimitados' : `de ${chartData.creditsTotal} totales`}
                </span>
            </div>

            {/* Widget 3: Success Rate (Doughnut) */}
            <div className="metric-widget metric-widget--chart">
                <div className="metric-widget__header" style={{ width: '100%' }}>
                    <h3 className="metric-widget__title">Tasa de Éxito</h3>
                    <CheckCircle className="metric-widget__icon" size={20} />
                </div>
                <div className="metric-widget__chart-container">
                    <Doughnut data={successRateData} options={chartOptions} />
                    <div className="chart-center-label">
                        <span className="chart-center-value">
                            {chartData.successRate != null ? `${Math.round(chartData.successRate)}%` : '—'}
                        </span>
                    </div>
                </div>
                <span className="metric-widget__subtext">
                    Calidad de conversión
                </span>
            </div>

            {/* Widget 4: Avg Time (Standard) */}
            <div className="metric-widget">
                <div className="metric-widget__header">
                    <h3 className="metric-widget__title">{avgTime.label}</h3>
                    <Zap className="metric-widget__icon" size={20} />
                </div>
                <div className="metric-widget__content">
                    <span className="metric-widget__value">{avgTime.value}</span>
                    <span className="metric-widget__subtext">Promedio global</span>
                </div>
            </div>
        </div>
    );
}
