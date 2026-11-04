import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackMessage?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[UI ERROR BOUNDARY]', error, errorInfo);
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    } else {
      window.location.reload();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          padding: '30px',
          textAlign: 'center',
        }}>
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '16px',
            padding: '32px 28px',
            maxWidth: '560px',
            width: '100%',
          }}>
            <div style={{
              display: 'inline-flex',
              padding: '12px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.2)',
              marginBottom: '16px',
            }}>
              <AlertTriangle size={32} color="#ef4444" />
            </div>

            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>
              Kendala Tampilan Terdeteksi
            </h2>

            <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '16px', lineHeight: 1.5 }}>
              {this.props.fallbackMessage || 'Komponen visual mengalami kesalahan saat merender data. Anda dapat memuat ulang tampilan atau kembali ke halaman analisis baru.'}
            </p>

            {this.state.error && (
              <div style={{
                background: '#090d16',
                border: '1px solid #1e293b',
                borderRadius: '8px',
                padding: '10px 14px',
                textAlign: 'left',
                fontSize: '0.75rem',
                color: '#f87171',
                fontFamily: 'monospace',
                marginBottom: '20px',
                maxHeight: '120px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
              }}>
                {this.state.error.message || String(this.state.error)}
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button
                className="btn btn-primary"
                onClick={this.handleReset}
                style={{ padding: '8px 18px', fontSize: '0.85rem' }}
              >
                <RefreshCw size={15} />
                <span>Pulihkan Tampilan</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
