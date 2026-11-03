import React from 'react';
import { Activity, XCircle, BarChart3, AlertTriangle, CheckCircle2 } from 'lucide-react';
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
    if (confirm('Apakah Anda yakin ingin membatalkan analisis yang sedang berjalan?')) {
      await api.cancel_run();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '16px' }}>
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
                {progress.stepName || 'Menunggu Operasi'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                {progress.message || 'Tidak ada operasi yang sedang aktif.'}
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
                <span>Buka Hasil Intelijen</span>
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

      {/* Main Content: Stepper + Log */}
      <div style={{ display: 'grid', gridTemplateColumns: '290px 1fr', gap: '16px', flex: 1, minHeight: '480px' }}>
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
