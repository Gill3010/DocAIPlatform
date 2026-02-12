import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import './MiniCreditsChart.css';

interface MiniCreditsChartProps {
    remaining: number;
    total: number;
    /** When true, show as "full" (e.g. admin unlimited) */
    unlimited?: boolean;
    label: string;
}

const REMAINING_COLOR = 'var(--color-cta, #FF8C42)';
const USED_COLOR = 'var(--color-bg-tertiary)';

export function MiniCreditsChart({ remaining, total, unlimited, label }: MiniCreditsChartProps) {
    const totalSafe = total <= 0 ? 1 : total;
    const remainingClamped = unlimited ? totalSafe : Math.min(totalSafe, Math.max(0, remaining));
    const used = totalSafe - remainingClamped;
    const data = [
        { name: 'Disponibles', value: remainingClamped, color: REMAINING_COLOR },
        { name: 'Usados', value: used, color: USED_COLOR }
    ].filter((d) => d.value > 0);

    return (
        <div className="mini-credits-chart" role="img" aria-label={`${label}: ${remaining} de ${total}`}>
            <div className="mini-credits-chart__viz">
                <ResponsiveContainer width="100%" height={80}>
                    <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                        <Pie
                            data={
                                data.length
                                    ? data
                                    : [{ name: 'Sin dato', value: 1, color: USED_COLOR }]
                            }
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
                <span className="mini-credits-chart__center">
                    {unlimited ? '∞' : `${remaining}/${total}`}
                </span>
            </div>
            <p className="mini-credits-chart__label">{label}</p>
        </div>
    );
}
