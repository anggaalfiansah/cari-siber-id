import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface SentimentPieProps {
  data: Array<{ name: string; value: number; color: string }>;
}

export const SentimentPie: React.FC<SentimentPieProps> = ({ data }) => {
  const total = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <div style={{ width: '100%', height: '280px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={65}
            outerRadius={95}
            paddingAngle={4}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
            formatter={(value: any) => [`${value} komentar (${total > 0 ? ((Number(value) / total) * 100).toFixed(1) : 0}%)`, 'Jumlah']}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(val) => <span style={{ color: '#cbd5e1', fontSize: '0.8rem', fontWeight: 500 }}>{val}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
