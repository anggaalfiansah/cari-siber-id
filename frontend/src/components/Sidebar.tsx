import React from 'react';
import { Shield, PlusCircle, Activity, BarChart3, History, Settings, HelpCircle, AlertTriangle } from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  isBusy: boolean;
  onOpenAbout?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, isBusy, onOpenAbout }) => {
  const menuItems = [
    { id: 'new', label: '1. Operasi Baru', icon: PlusCircle },
    { id: 'progress', label: '2. Monitor Pipeline', icon: Activity, badge: isBusy ? 'Running' : null },
    { id: 'result', label: '3. Peta Situasi (SITREP)', icon: BarChart3 },
    { id: 'history', label: '4. Arsip Operasi', icon: History },
    { id: 'settings', label: '5. Konfigurasi Sistem', icon: Settings },
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '1rem', fontWeight: '700', letterSpacing: '0.04em', color: '#f8fafc' }}>
                CaRI-Siber ID
              </span>
              <span style={{
                fontSize: '0.6rem',
                fontWeight: 700,
                color: '#facc15',
                backgroundColor: 'rgba(234, 179, 8, 0.15)',
                border: '1px solid rgba(234, 179, 8, 0.35)',
                padding: '1px 5px',
                borderRadius: '4px',
              }}>
                PROTOTYPE
              </span>
            </div>
            <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: '600', letterSpacing: '0.02em', marginTop: '1px' }}>
              COGNITIVE DOMAIN INTEL
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

        {/* Tombol Bantuan / Panduan Awam */}
        {onOpenAbout && (
          <div style={{ marginTop: 'auto', paddingTop: '10px' }}>
            <button
              onClick={onOpenAbout}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 12px',
                borderRadius: '8px',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                background: 'rgba(2, 132, 199, 0.08)',
                color: '#38bdf8',
                cursor: 'pointer',
                textAlign: 'left',
                fontWeight: '600',
                fontSize: '0.8rem',
                transition: 'all 0.15s ease',
              }}
              title="Pelajari maksud, fungsi untuk orang awam, dan status prototipe sistem ini"
            >
              <HelpCircle size={16} />
              <span>Panduan & Info PoC</span>
            </button>
          </div>
        )}
      </nav>

      {/* Footer Info */}
      <div style={{ padding: '14px 16px', borderTop: '1px solid rgba(51, 65, 85, 0.4)', fontSize: '0.73rem', color: '#64748b' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#facc15', fontWeight: 600 }}>
          <AlertTriangle size={12} />
          <span>Proof-of-Concept (PoC)</span>
        </div>
        <div style={{ marginTop: '3px', color: '#475569', fontSize: '0.7rem' }}>
          Batch Snapshot • Target 24/7 Engine
        </div>
      </div>
    </aside>
  );
};
