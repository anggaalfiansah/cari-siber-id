import React from 'react';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

interface StepperProps {
  currentStepName: string;
  stepIndex?: number;
  percent: number;
  status?: string;
}

const PHASES = [
  { id: 1, name: 'Scraping Komentar', desc: 'Metadata & Raw Comments' },
  { id: 2, name: 'Topic Modeling (IndoBERT)', desc: 'Normalisasi Alay & Klasterisasi' },
  { id: 3, name: 'AI Labeling & 4 Gates', desc: 'Pelabelan Sentimen & Self-Healing' },
  { id: 4, name: 'Agregasi & Engagement', desc: 'Pemetaan Matriks Isu & Like' },
  { id: 5, name: 'EDA & Visualisasi', desc: 'Analitik & Pembuatan 8 Grafik' },
  { id: 6, name: 'Narasi Insight AI', desc: 'Penyusunan Executive Briefing' },
  { id: 7, name: 'Audit CIB & Polarisasi', desc: 'Indikator Bot & Konsensus Opini' },
];

export const Stepper: React.FC<StepperProps> = ({ currentStepName, stepIndex = 0, percent, status = 'RUNNING' }) => {
  const isCompleted = status === 'COMPLETED' || percent === 100;

  // Derive stepIndex from stepName if not explicitly passed
  let activeIndex = stepIndex;
  if (!activeIndex && currentStepName) {
    const found = PHASES.find((p) => currentStepName.toLowerCase().includes(p.name.toLowerCase().split(' ')[0]));
    if (found) activeIndex = found.id;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {PHASES.map((p) => {
        let isDone = false;
        let isCurrent = false;

        if (isCompleted) {
          isDone = true;
        } else if (activeIndex > 0) {
          if (p.id < activeIndex) {
            isDone = true;
          } else if (p.id === activeIndex) {
            isCurrent = true;
          }
        }

        let icon = <Circle size={15} color="#475569" />;
        let textColor = '#64748b';
        let descColor = '#334155';

        if (isDone) {
          icon = <CheckCircle2 size={16} color="#10b981" />;
          textColor = '#cbd5e1';
          descColor = '#64748b';
        } else if (isCurrent) {
          icon = <Loader2 size={16} color="#38bdf8" style={{ animation: 'spin 1.5s linear infinite' }} />;
          textColor = '#38bdf8';
          descColor = '#0284c7';
        }

        return (
          <div
            key={p.id}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              padding: '8px 10px',
              borderRadius: '6px',
              background: isCurrent ? 'rgba(2, 132, 199, 0.12)' : 'transparent',
              border: isCurrent ? '1px solid rgba(56, 189, 248, 0.25)' : '1px solid transparent',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ marginTop: '2px', flexShrink: 0 }}>{icon}</div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: isCurrent ? 700 : 500, color: textColor }}>
                {p.id}. {p.name}
              </span>
              <span style={{ fontSize: '0.7rem', color: descColor, marginTop: '1px' }}>
                {p.desc}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
