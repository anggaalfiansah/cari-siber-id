import React, { useEffect, useRef, useState } from 'react';
import { Terminal, Trash2, Copy, Check } from 'lucide-react';

interface LogViewerProps {
  logs: string[];
  onClear: () => void;
}

export const LogViewer: React.FC<LogViewerProps> = ({ logs, onClear }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const handleCopy = () => {
    if (logs.length === 0) return;
    navigator.clipboard.writeText(logs.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '380px' }}>
      <div className="panel-header" style={{ padding: '8px 14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600 }}>
          <Terminal size={14} color="#38bdf8" />
          <span>REALTIME RUNTIME LOG</span>
          <span style={{ fontSize: '0.7rem', color: '#475569' }}>({logs.length} lines)</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            className="btn btn-secondary"
            onClick={handleCopy}
            style={{ padding: '4px 10px', fontSize: '0.725rem', gap: '4px' }}
            title="Salin seluruh log"
          >
            {copied ? <Check size={12} color="#4ade80" /> : <Copy size={12} />}
            <span>{copied ? 'Tersalin' : 'Salin'}</span>
          </button>

          <button
            className="btn btn-secondary"
            onClick={onClear}
            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
            title="Bersihkan log"
          >
            <Trash2 size={12} />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        style={{
          flex: 1,
          padding: '12px 14px',
          background: '#070a10',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '0.75rem',
          lineHeight: '1.45',
          color: '#cbd5e1',
          overflowY: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}
      >
        {logs.length === 0 ? (
          <div style={{ color: '#475569', fontStyle: 'italic' }}>Menunggu log eksekusi...</div>
        ) : (
          logs.map((line, i) => {
            const isError = line.includes('[ERROR]') || line.includes('FAILED') || line.includes('Error:');
            const isSuccess = line.includes('[SUCCESS]') || line.includes('selesai') || line.includes('[OK]');
            const isWarning = line.includes('[WARNING]');
            const isInfo = line.includes('[INFO]') || line.includes('[PROCESS]');

            let color = '#cbd5e1';
            if (isError) color = '#f87171';
            else if (isSuccess) color = '#4ade80';
            else if (isWarning) color = '#fbbf24';
            else if (isInfo) color = '#38bdf8';

            return (
              <div key={i} style={{ color }}>
                {line}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
