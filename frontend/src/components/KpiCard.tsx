import React from 'react';

interface KpiCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  badge?: {
    text: string;
    level: 'low' | 'medium' | 'high' | 'critical';
  };
  icon?: React.ReactNode;
}

export const KpiCard: React.FC<KpiCardProps> = ({ label, value, subValue, badge, icon }) => {
  const getBadgeClass = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low': return 'badge-low';
      case 'medium': return 'badge-medium';
      case 'high': return 'badge-high';
      case 'critical': return 'badge-critical';
      default: return 'badge-low';
    }
  };

  return (
    <div className="panel" style={{ padding: '16px 20px', flex: 1, minWidth: '200px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8' }}>
          {label}
        </span>
        {icon && <div style={{ color: '#64748b' }}>{icon}</div>}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
        <span style={{ fontSize: '1.65rem', fontWeight: '700', color: '#f8fafc' }}>
          {value}
        </span>
        {badge && (
          <span className={`badge ${getBadgeClass(badge.level)}`}>
            {badge.text}
          </span>
        )}
      </div>

      {subValue && (
        <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
          {subValue}
        </div>
      )}
    </div>
  );
};
