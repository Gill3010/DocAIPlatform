import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import './MiniSuccessRateChart.css';

interface MiniSuccessRateChartProps {
    /** 0-100 */
    value: number | null;
    label: string;
}

const SUCCESS_COLOR = 'var(--color-success, #2ECC71)';
const REMAINING_COLOR = 'var(--color-bg-tertiary)';

export function MiniSuccessRateChart({ value, label }: MiniSuccessRateChartProps) {
    const rate = value == null || Number.isNaN(value) ? 0 : Math.min(100, Math.max(0, value));
    const data = [
        { name: 'Éxito', value: rate, color: SUCCESS_COLOR },
        { name: 'Resto', value: 100 - rate, color: REMAINING_COLOR }
    ].filter((d) => d.value > 0);

    return (
        <div className="mini-success-rate-chart" role="img" aria-label={`${label}: ${rate}%`}>
            <div className="mini-success-rate-chart__viz">
                <ResponsiveContainer width="100%" height={80}>
                    <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                        <Pie
                            data={data.length ? data : [{ name: 'Sin dato', value: 100, color: REMAINING_COLOR }]}
                            cx="50%"
                            cy="50%"
                            innerRadius={24}
                            outerRadius={36}
                            paddingAngle={0}
                            dataKey="value"
                            stroke="none"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Pie>
                    </PieChart>
                </ResponsiveContainer>
                <span className="mini-success-rate-chart__center">
                    {value != null && !Number.isNaN(value) ? `${Math.round(value)}%` : '—'}
                </span>
            </div>
            <p className="mini-success-rate-chart__label">{label}</p>
        </div>
    );
}
