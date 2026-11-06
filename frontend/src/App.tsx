import React, { useState, useEffect } from 'react';
import { Monitor } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { NewAnalysisPage } from './pages/NewAnalysisPage';
import { ProgressPage } from './pages/ProgressPage';
import { ResultPage } from './pages/ResultPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { ErrorBoundary } from './components/ErrorBoundary';
import { subscribePyWebViewEvents, waitForPyWebView, api } from './api/bridge';
import { PyWebViewEvent } from './api/types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'new' | 'progress' | 'result' | 'history' | 'settings'>('new');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [reuseRunId, setReuseRunId] = useState<string | undefined>(undefined);
  const [isBusy, setIsBusy] = useState(false);
  const [isBriefingMode, setIsBriefingMode] = useState(false);

  const [progress, setProgress] = useState({
    status: 'IDLE',
    percent: 0,
    stepIndex: 0,
    stepName: 'Siap',
    message: 'Silakan daftarkan analisis baru untuk memulai.',
    runId: undefined as string | undefined,
  });

  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    waitForPyWebView().then(() => {
      api.is_runner_busy()
        .then((busy: boolean) => setIsBusy(busy))
        .catch(() => setIsBusy(false));
    });

    const unsubscribe = subscribePyWebViewEvents((event: PyWebViewEvent) => {
      if (event.type === 'progress') {
        setProgress((prev) => ({
          status: event.status,
          percent: event.percent,
          stepIndex: event.step_index !== undefined ? event.step_index : prev.stepIndex,
          stepName: event.step_name,
          message: event.message,
          runId: event.run_id || prev.runId,
        }));
        setIsBusy(event.status === 'RUNNING' || event.status === 'CANCELLING');
      } else if (event.type === 'log') {
        setLogs((prev) => [...prev.slice(-400), event.line]);
      } else if (event.type === 'completed') {
        setProgress((prev) => ({
          status: 'COMPLETED',
          percent: 100,
          stepIndex: 7,
          stepName: 'Selesai',
          message: event.message,
          runId: event.run_id || prev.runId,
        }));
        setIsBusy(false);
        setSelectedRunId(event.run_id);
        setCurrentTab('result');
      } else if (event.type === 'error') {
        setProgress((prev) => ({
          ...prev,
          status: 'FAILED',
          message: event.message,
        }));
        setIsBusy(false);
      }
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    // Mode Komando / Briefing hanya aktif untuk presentasi dashboard hasil (Puskodal view).
    // Saat berpindah halaman/tab, otomatis kembalikan ke tampilan normal (sidebar muncul).
    if (currentTab !== 'result') {
      setIsBriefingMode(false);
    }
  }, [currentTab]);

  const handleRunStarted = (runId: string) => {
    setIsBriefingMode(false);
    setSelectedRunId(runId);
    setProgress({
      status: 'RUNNING',
      percent: 5,
      stepIndex: 0,
      stepName: 'Inisialisasi',
      message: 'Operasi dimulai...',
      runId,
    });
    setLogs([`[${new Date().toLocaleTimeString()}] Sesi analisis dimulai: ${runId}`]);
    setIsBusy(true);
    setCurrentTab('progress');
  };

  const handleSelectHistoryRun = (runId: string) => {
    setIsBriefingMode(false);
    setSelectedRunId(runId);
    setCurrentTab('result');
  };

  const handleNavigateNew = () => {
    setIsBriefingMode(false);
    setReuseRunId(undefined);
    setCurrentTab('new');
  };

  const handleNavigateNewWithReuse = (runId: string) => {
    setIsBriefingMode(false);
    setReuseRunId(runId);
    setCurrentTab('new');
  };

  return (
    <ErrorBoundary fallbackMessage="Terjadi kendala visual pada kerangka utama aplikasi.">
      <div style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden' }}>
        {!isBriefingMode && (
          <Sidebar
            currentTab={currentTab}
            onSelectTab={(tab) => setCurrentTab(tab as any)}
            isBusy={isBusy}
          />
        )}

        {isBriefingMode && (
          <button
            onClick={() => setIsBriefingMode(false)}
            style={{
              position: 'fixed',
              top: '12px',
              right: '24px',
              zIndex: 9999,
              background: 'rgba(15, 23, 42, 0.92)',
              border: '1px solid #10b981',
              color: '#34d399',
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 15px rgba(0, 0, 0, 0.5), 0 0 10px rgba(16, 185, 129, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backdropFilter: 'blur(8px)',
              transition: 'all 0.15s ease',
            }}
            title="Klik untuk keluar dari Mode Komando / Briefing dan menampilkan kembali Sidebar"
          >
            <Monitor size={14} color="#34d399" />
            <span>Mode Komando Aktif</span>
            <span style={{ color: '#64748b', fontSize: '0.72rem' }}>|</span>
            <span style={{ color: '#f8fafc', textDecoration: 'underline' }}>✕ Kembali ke Normal</span>
          </button>
        )}

        <main style={{ flex: 1, padding: isBriefingMode ? '20px 32px' : '24px 28px', overflowY: 'auto', background: '#0b0f19', display: 'flex', flexDirection: 'column', transition: 'padding 0.2s ease' }}>
          <ErrorBoundary onReset={handleNavigateNew}>
            {currentTab === 'new' && (
              <NewAnalysisPage
                onRunStarted={handleRunStarted}
                isBusy={isBusy}
                initialReuseRunId={reuseRunId}
                onClearReuseRunId={() => setReuseRunId(undefined)}
              />
            )}

            {currentTab === 'progress' && (
              <ProgressPage
                progress={progress}
                logs={logs}
                onClearLogs={() => setLogs([])}
                onViewResult={(id) => {
                  setSelectedRunId(id);
                  setCurrentTab('result');
                }}
              />
            )}

            {currentTab === 'result' && (
              <ResultPage
                runId={selectedRunId}
                onNavigateNew={handleNavigateNew}
                onNavigateNewWithReuse={handleNavigateNewWithReuse}
                isBriefingMode={isBriefingMode}
                onToggleBriefingMode={() => setIsBriefingMode((prev) => !prev)}
              />
            )}

            {currentTab === 'history' && (
              <HistoryPage onSelectRun={handleSelectHistoryRun} />
            )}

            {currentTab === 'settings' && (
              <SettingsPage />
            )}
          </ErrorBoundary>
        </main>
      </div>
    </ErrorBoundary>
  );
};

export default App;
