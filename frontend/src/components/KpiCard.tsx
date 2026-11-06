import React from 'react';

interface KpiCardProps {
  isBriefingMode?: boolean;
  label: string;
  value: string | number;
  subValue?: string;
  badge?: {
    text: string;
    level: 'low' | 'medium' | 'high' | 'critical';
  };
  icon?: React.ReactNode;
}

export const KpiCard: React.FC<KpiCardProps> = ({ label, value, subValue, badge, icon, isBriefingMode }) => {
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
    <div className="panel" style={{ padding: isBriefingMode ? '22px 24px' : '16px 20px', flex: 1, minWidth: isBriefingMode ? '240px' : '200px', transition: 'all 0.2s ease', border: isBriefingMode ? '1px solid rgba(56, 189, 248, 0.4)' : undefined, boxShadow: isBriefingMode ? '0 4px 20px rgba(0, 0, 0, 0.5)' : undefined }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: isBriefingMode ? '0.9rem' : '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8' }}>
          {label}
        </span>
        {icon && <div style={{ color: '#64748b' }}>{icon}</div>}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
        <span style={{ fontSize: isBriefingMode ? '2.1rem' : '1.65rem', fontWeight: '800', color: '#f8fafc' }}>
          {value}
        </span>
        {badge && (
          <span className={`badge ${getBadgeClass(badge.level)}`}>
            {badge.text}
          </span>
        )}
      </div>

      {subValue && (
        <div style={{ fontSize: isBriefingMode ? '0.88rem' : '0.75rem', color: isBriefingMode ? '#94a3b8' : '#64748b', marginTop: '4px' }}>
          {subValue}
        </div>
      )}
    </div>
  );
};
