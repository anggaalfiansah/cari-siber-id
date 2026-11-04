import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface TopTopicsBarProps {
  data?: Array<{
    topic: string;
    full_topic: string;
    category?: string;
    keywords?: string;
    count: number;
    sentiment: string;
  }>;
}

export const TopTopicsBar: React.FC<TopTopicsBarProps> = ({ data }) => {
  const safeData = Array.isArray(data) ? data : [];

  const getBarColor = (sentiment?: string) => {
    switch (String(sentiment || '').toLowerCase()) {
      case 'positif': return '#10b981';
      case 'negatif': return '#ef4444';
      default: return '#0284c7';
    }
  };

  const renderCustomTick = ({ x, y, payload }: any) => {
    const text = String(payload?.value || '');
    return (
      <g transform={`translate(${x},${y})`}>
        <title>{text}</title>
        <text
          x={-8}
          y={4}
          textAnchor="end"
          fill="#cbd5e1"
          fontSize={11}
          fontWeight={500}
        >
          {text}
        </text>
      </g>
    );
  };

  if (safeData.length === 0) {
    return (
      <div style={{
        width: '100%',
        height: '280px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#64748b',
        fontSize: '0.82rem',
      }}>
        <span>Belum ada data topik klaster yang teridentifikasi.</span>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '280px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={safeData}
          layout="vertical"
          margin={{ top: 8, right: 24, left: 10, bottom: 5 }}
          barCategoryGap={6}
        >
          <XAxis type="number" stroke="#475569" fontSize={11} tickLine={false} />
          <YAxis
            type="category"
            dataKey="topic"
            stroke="#94a3b8"
            width={210}
            tick={renderCustomTick}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: '#090d16',
              borderColor: '#334155',
              borderRadius: '8px',
              color: '#f8fafc',
              fontSize: '0.82rem',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
            formatter={(value: any, _, item: any) => [
              `${value} Komentar (${item?.payload?.sentiment || 'Netral'})`,
              item?.payload?.category ? `Kategori: ${item.payload.category}` : 'Jumlah',
            ]}
            labelFormatter={(_, items: any) => {
              if (items && items[0]) {
                const p = items[0].payload;
                return p?.full_topic || p?.topic || '';
              }
              return '';
            }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={18}>
            {safeData.map((entry, index) => (
              <Cell key={`bar-${index}`} fill={getBarColor(entry.sentiment)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
