import React, { useState, useEffect } from 'react';
import { History, Trash2, ExternalLink, RefreshCw, AlertCircle } from 'lucide-react';
import { RunHistoryItem } from '../api/types';
import { api } from '../api/bridge';

interface HistoryPageProps {
  onSelectRun: (runId: string) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onSelectRun }) => {
  const [runs, setRuns] = useState<RunHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const list = await api.list_history();
      setRuns(list);
    } catch (err: any) {
      setError(err?.message || 'Gagal memuat riwayat audit.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (e: React.MouseEvent, runId: string) => {
    e.stopPropagation();
    if (confirm(`Hapus catatan analisis (${runId}) beserta seluruh filenya?`)) {
      try {
        await api.delete_history(runId);
        setRuns((prev) => prev.filter((r) => r.id !== runId));
      } catch (err: any) {
        alert('Gagal menghapus riwayat: ' + err?.message);
      }
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="badge badge-low">SELESAI</span>;
      case 'RUNNING':
        return <span className="badge" style={{ background: 'rgba(2, 132, 199, 0.2)', color: '#38bdf8' }}>BERJALAN</span>;
      case 'FAILED':
        return <span className="badge badge-high">GAGAL</span>;
      case 'CANCELLED':
        return <span className="badge" style={{ background: '#334155', color: '#94a3b8' }}>DIBATALKAN</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  const getCibBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-high';
      case 'MEDIUM': return 'badge-medium';
      default: return 'badge-low';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f8fafc' }}>Riwayat Audit Ruang Siber</h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '2px' }}>
            Daftar seluruh sesi analisis intelijen kognitif yang tersimpan secara lokal.
          </p>
        </div>

        <button className="btn btn-secondary" onClick={loadHistory} disabled={loading}>
          <RefreshCw size={15} style={{ animation: loading ? 'spin 1.5s linear infinite' : 'none' }} />
          <span>Segarkan</span>
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', borderRadius: '8px', display: 'flex', gap: '8px', fontSize: '0.85rem' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="panel" style={{ flex: 1, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: '#090d16', color: '#94a3b8', textAlign: 'left', borderBottom: '1px solid #1e293b' }}>
              <th style={{ padding: '12px 16px' }}>Waktu Audit</th>
              <th style={{ padding: '12px 16px' }}>Target Video</th>
              <th style={{ padding: '12px 16px' }}>Status</th>
              <th style={{ padding: '12px 16px' }}>Komentar</th>
              <th style={{ padding: '12px 16px' }}>Skor CIB</th>
              <th style={{ padding: '12px 16px' }}>Polarisasi</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {runs.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                  <History size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                  <div>Belum ada riwayat analisis yang tercatat.</div>
                </td>
              </tr>
            ) : (
              runs.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => r.status === 'COMPLETED' && onSelectRun(r.id)}
                  style={{
                    borderBottom: '1px solid rgba(51, 65, 85, 0.25)',
                    cursor: r.status === 'COMPLETED' ? 'pointer' : 'default',
                    transition: 'background 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(15, 23, 42, 0.6)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                >
                  <td style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                    {r.created_at}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ fontWeight: 600, color: '#f1f5f9', maxWidth: '320px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {r.video_title || r.target_url}
                    </div>
                    {r.channel_name && <div style={{ fontSize: '0.72rem', color: '#64748b' }}>{r.channel_name}</div>}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {getStatusBadge(r.status)}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: '#cbd5e1' }}>
                    {r.total_comments > 0 ? r.total_comments.toLocaleString() : '-'}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {r.status === 'COMPLETED' ? (
                      <span className={`badge ${getCibBadge(r.cib_level)}`}>
                        {r.cib_score.toFixed(2)} ({r.cib_level})
                      </span>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: '#cbd5e1' }}>
                    {r.status === 'COMPLETED' ? r.polarization_index.toFixed(2) : '-'}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '6px' }}>
                      {r.status === 'COMPLETED' && (
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '5px 8px' }}
                          title="Buka Hasil"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectRun(r.id);
                          }}
                        >
                          <ExternalLink size={14} />
                        </button>
                      )}
                      <button
                        className="btn btn-danger"
                        style={{ padding: '5px 8px' }}
                        title="Hapus Run"
                        onClick={(e) => handleDelete(e, r.id)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
