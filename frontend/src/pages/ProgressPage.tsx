import React from 'react';
import { Activity, XCircle, BarChart3, AlertTriangle, CheckCircle2, ShieldCheck, Cpu } from 'lucide-react';
import { Stepper } from '../components/Stepper';
import { LogViewer } from '../components/LogViewer';
import { api } from '../api/bridge';

interface ProgressPageProps {
  progress: {
    status: string;
    percent: number;
    stepIndex?: number;
    stepName: string;
    message: string;
    runId?: string;
  };
  logs: string[];
  onClearLogs: () => void;
  onViewResult: (runId: string) => void;
}

export const ProgressPage: React.FC<ProgressPageProps> = ({
  progress,
  logs,
  onClearLogs,
  onViewResult,
}) => {
  const isRunning = progress.status === 'RUNNING';
  const isCancelling = progress.status === 'CANCELLING';
  const isCompleted = progress.status === 'COMPLETED';
  const isFailed = progress.status === 'FAILED';
  const isCancelled = progress.status === 'CANCELLED';

  const handleCancel = async () => {
    if (confirm('Apakah Anda yakin ingin membatalkan operasi analisis yang sedang berjalan?')) {
      await api.cancel_run();
    }
  };

  // Hitung status tiap Agentic Gate dari progres dan log
  const stepIdx = progress.stepIndex ?? 0;
  const pct = progress.percent ?? 0;

  const getGateState = (gateNum: 1 | 2 | 3 | 4): 'DONE' | 'ACTIVE' | 'WAITING' => {
    if (isCompleted) return 'DONE';
    if (gateNum === 1) {
      if (stepIdx > 2 || pct >= 50) return 'DONE';
      if (stepIdx === 2 || (pct >= 30 && pct < 50)) return 'ACTIVE';
      return 'WAITING';
    }
    if (gateNum === 2) {
      if (stepIdx > 3 || pct >= 62) return 'DONE';
      if (stepIdx === 3 && pct < 62) return 'ACTIVE';
      return 'WAITING';
    }
    if (gateNum === 3) {
      if (stepIdx > 3 || pct >= 72) return 'DONE';
      if (stepIdx === 3 && pct >= 55) return 'ACTIVE';
      return 'WAITING';
    }
    // Gate 4: Report Gate
    if (stepIdx > 6 || pct >= 96) return 'DONE';
    if (stepIdx === 6 || (pct >= 90 && pct < 96)) return 'ACTIVE';
    return 'WAITING';
  };

  const gates = [
    {
      num: 1 as const,
      title: 'Gate 1: Quality Gate',
      desc: 'Audit OOV & ekstraksi otomatis kamus slang siber',
    },
    {
      num: 2 as const,
      title: 'Gate 2: Topic Gate',
      desc: 'Evaluasi koherensi BERTopic & koreksi label domain ancaman',
    },
    {
      num: 3 as const,
      title: 'Gate 3: Verification Gate',
      desc: 'Re-routing otomatis komentar low-confidence (<0.65)',
    },
    {
      num: 4 as const,
      title: 'Gate 4: Report Gate',
      desc: 'Verifikasi silang angka KIRKA terhadap fakta EDA (Anti-Halusinasi)',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '14px' }}>
      {/* Top Header Card */}
      <div className="panel" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {isRunning && <Activity size={20} color="#38bdf8" style={{ animation: 'pulse 1.5s infinite' }} />}
            {isCompleted && <CheckCircle2 size={20} color="#10b981" />}
            {isFailed && <AlertTriangle size={20} color="#ef4444" />}
            {isCancelled && <XCircle size={20} color="#94a3b8" />}
            <div>
              <div style={{ fontSize: '1rem', fontWeight: '700', color: '#f8fafc' }}>
                {progress.stepName || '2. Monitor Pipeline & Audit Otonom'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                {progress.message || 'Menunggu inisialisasi operasi analisis.'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>
              {progress.percent}%
            </span>

            {isRunning && (
              <button className="btn btn-danger" onClick={handleCancel} disabled={isCancelling}>
                <XCircle size={16} />
                <span>{isCancelling ? 'Membatalkan...' : 'Batalkan'}</span>
              </button>
            )}

            {isCompleted && progress.runId && (
              <button className="btn btn-primary" onClick={() => onViewResult(progress.runId!)}>
                <BarChart3 size={16} />
                <span>Buka Peta Situasi (SITREP)</span>
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ width: '100%', height: '8px', background: '#1e293b', borderRadius: '4px', overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${progress.percent}%`,
              background: isCompleted ? '#10b981' : isFailed ? '#ef4444' : 'linear-gradient(90deg, #0284c7, #38bdf8)',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* 4 Agentic AI Hardened Verification Gates Status Strip */}
      <div className="panel" style={{ padding: '12px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', fontWeight: 700, color: '#e2e8f0', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            <ShieldCheck size={16} color="#10b981" />
            <span>Status Integritas 4 Agentic AI Hardened Verification Gates (Self-Healing Pipeline)</span>
          </div>
          <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
            Standar Verifikasi Otonom 4-Gate
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
          {gates.map((g) => {
            const st = getGateState(g.num);
            const isDone = st === 'DONE';
            const isActive = st === 'ACTIVE';

            return (
              <div
                key={g.num}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: isDone
                    ? 'rgba(16, 185, 129, 0.12)'
                    : isActive
                      ? 'rgba(56, 189, 248, 0.14)'
                      : 'rgba(15, 23, 42, 0.6)',
                  border: isDone
                    ? '1px solid rgba(16, 185, 129, 0.4)'
                    : isActive
                      ? '1px solid #38bdf8'
                      : '1px solid rgba(51, 65, 85, 0.5)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, color: isDone ? '#34d399' : isActive ? '#38bdf8' : '#cbd5e1' }}>
                    {g.title}
                  </span>
                  <span style={{
                    fontSize: '0.64rem',
                    fontWeight: 800,
                    padding: '2px 6px',
                    borderRadius: '6px',
                    background: isDone ? '#10b981' : isActive ? '#0284c7' : '#1e293b',
                    color: isDone ? '#052e16' : isActive ? '#ffffff' : '#64748b',
                  }}>
                    {isDone ? 'LOLOS VERIFIKASI' : isActive ? 'MENGAUDIT...' : 'MENUNGGU'}
                  </span>
                </div>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', lineHeight: 1.35 }}>
                  {g.desc}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Content: Stepper + Log */}
      <div style={{ display: 'grid', gridTemplateColumns: '290px 1fr', gap: '16px', flex: 1, minHeight: '420px' }}>
        {/* Stepper */}
        <div className="panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '14px', letterSpacing: '0.05em' }}>
            Tahapan Pipeline
          </div>
          <Stepper
            currentStepName={progress.stepName}
            stepIndex={progress.stepIndex}
            percent={progress.percent}
            status={progress.status}
          />
        </div>

        {/* Terminal Log */}
        <LogViewer logs={logs} onClear={onClearLogs} />
      </div>
    </div>
  );
};
