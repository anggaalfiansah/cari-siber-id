import React, { useState, useEffect } from 'react';
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
  const [isBusy, setIsBusy] = useState(false);

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

  const handleRunStarted = (runId: string) => {
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
    setSelectedRunId(runId);
    setCurrentTab('result');
  };

  const handleNavigateNew = () => {
    setCurrentTab('new');
  };

  return (
    <ErrorBoundary fallbackMessage="Terjadi kendala visual pada kerangka utama aplikasi.">
      <div style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden' }}>
        <Sidebar
          currentTab={currentTab}
          onSelectTab={(tab) => setCurrentTab(tab as any)}
          isBusy={isBusy}
        />

        <main style={{ flex: 1, padding: '24px 28px', overflowY: 'auto', background: '#0b0f19', display: 'flex', flexDirection: 'column' }}>
          <ErrorBoundary onReset={handleNavigateNew}>
            {currentTab === 'new' && (
              <NewAnalysisPage onRunStarted={handleRunStarted} isBusy={isBusy} />
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
