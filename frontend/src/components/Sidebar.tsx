import React from 'react';
import { Shield, PlusCircle, Activity, BarChart3, History, Settings } from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  isBusy: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, isBusy }) => {
  const menuItems = [
    { id: 'new', label: 'Inisialisasi Operasi Pemantauan', icon: PlusCircle },
    { id: 'progress', label: 'Progres Operasi', icon: Activity, badge: isBusy ? 'Running' : null },
    { id: 'result', label: 'Pusat Intelijen Kognitif & Situasi Siber', icon: BarChart3 },
    { id: 'history', label: 'Riwayat Audit', icon: History },
    { id: 'settings', label: 'Pengaturan API', icon: Settings },
  ];

  return (
    <aside style={{
      width: '240px',
      background: '#090d16',
      borderRight: '1px solid rgba(51, 65, 85, 0.4)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      height: '100%',
    }}>
      {/* Brand */}
      <div style={{ padding: '20px 18px', borderBottom: '1px solid rgba(51, 65, 85, 0.4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7, #06b6d4)',
            borderRadius: '8px',
            padding: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Shield size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '1rem', fontWeight: '700', letterSpacing: '0.04em', color: '#f8fafc' }}>
              CaRI-Siber ID
            </div>
            <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: '600', letterSpacing: '0.02em' }}>
              COGNITIVE DOMAIN INTELLIGENCE
            </div>
          </div>
        </div>
      </div>

      {/* Nav Menu */}
      <nav style={{ padding: '14px 10px', flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                background: isActive ? 'rgba(2, 132, 199, 0.15)' : 'transparent',
                color: isActive ? '#38bdf8' : '#94a3b8',
                cursor: 'pointer',
                textAlign: 'left',
                fontWeight: isActive ? '600' : '500',
                fontSize: '0.875rem',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Icon size={18} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span style={{
                  background: '#0284c7',
                  color: '#ffffff',
                  fontSize: '0.65rem',
                  fontWeight: '700',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  animation: 'pulse 1.5s infinite',
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div style={{ padding: '14px 16px', borderTop: '1px solid rgba(51, 65, 85, 0.4)', fontSize: '0.75rem', color: '#475569' }}>
        <div>Domain Kognitif v1.0</div>
        <div style={{ marginTop: '2px', color: '#334155' }}>IndoBERT + 4 Hardened Gates</div>
      </div>
    </aside>
  );
};
