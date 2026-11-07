import React, { useState, useEffect } from 'react';
import { History, Trash2, ExternalLink, RefreshCw, AlertCircle, ShieldCheck, Copy, Check } from 'lucide-react';
import { RunHistoryItem } from '../api/types';
import { api, waitForPyWebView } from '../api/bridge';

interface HistoryPageProps {
  onSelectRun: (runId: string) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onSelectRun }) => {
  const [runs, setRuns] = useState<RunHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const loadHistory = async () => {
    setLoading(true);
    setError('');
    try {
      await waitForPyWebView();
      const list = await api.list_history();
      setRuns(Array.isArray(list) ? list : []);
    } catch (err: any) {
      setError(err?.message || 'Gagal memuat arsip operasi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (e: React.MouseEvent, runId: string) => {
    e.stopPropagation();
    if (confirm(`Hapus arsip operasi (${runId}) beserta seluruh barang bukti digitalnya?`)) {
      try {
        await api.delete_history(runId);
        setRuns((prev) => prev.filter((r) => r.id !== runId));
      } catch (err: any) {
        alert('Gagal menghapus arsip: ' + err?.message);
      }
    }
  };

  const handleCopyHash = (e: React.MouseEvent, runId: string, hash: string) => {
    e.stopPropagation();
    if (!hash) return;
    navigator.clipboard?.writeText(hash);
    setCopiedId(runId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="badge badge-low">TERVERIFIKASI</span>;
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

  const getCibBadge = (level?: string) => {
    switch (String(level || 'LOW').toUpperCase()) {
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
          <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f8fafc' }}>
            4. Arsip Operasi & Barang Bukti Digital (Chain of Custody)
          </h1>
          <p style={{ fontSize: '0.84rem', color: '#94a3b8', marginTop: '2px' }}>
            Penyimpanan lokal terisolasi beserta segel integritas kriptografi SHA-256 untuk akuntabilitas barang bukti siber sosial.
          </p>
        </div>

        <button className="btn btn-secondary" onClick={loadHistory} disabled={loading}>
          <RefreshCw size={15} style={{ animation: loading ? 'spin 1.5s linear infinite' : 'none' }} />
          <span>Segarkan Arsip</span>
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', borderRadius: '8px', display: 'flex', gap: '8px', fontSize: '0.85rem' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="panel" style={{ flex: 1, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
          <thead>
            <tr style={{ background: '#090d16', color: '#94a3b8', textAlign: 'left', borderBottom: '1px solid #1e293b' }}>
              <th style={{ padding: '12px 14px' }}>Waktu Operasi</th>
              <th style={{ padding: '12px 14px' }}>Target Operasi / Kampanye</th>
              <th style={{ padding: '12px 14px' }}>Status</th>
              <th style={{ padding: '12px 14px' }}>Bukti Komentar</th>
              <th style={{ padding: '12px 14px' }}>Indeks CIB</th>
              <th style={{ padding: '12px 14px' }}>Polarisasi</th>
              <th style={{ padding: '12px 14px' }}>Segel Forensik (SHA-256)</th>
              <th style={{ padding: '12px 14px', textAlign: 'right' }}>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {runs.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                  <History size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                  <div>Belum ada arsip operasi intelijen yang tercatat.</div>
                </td>
              </tr>
            ) : (
              runs.map((r) => {
                const isCompleted = r.status === 'COMPLETED';
                const isFailed = r.status === 'FAILED';
                const cibScoreNum = typeof r.cib_score === 'number' ? r.cib_score : Number(r.cib_score);
                const polIndexNum = typeof r.polarization_index === 'number' ? r.polarization_index : Number(r.polarization_index);
                const sha256 = r.sha256_hash || '';

                return (
                  <tr
                    key={r.id}
                    onClick={() => isCompleted && onSelectRun(r.id)}
                    style={{
                      borderBottom: '1px solid rgba(51, 65, 85, 0.25)',
                      cursor: isCompleted ? 'pointer' : 'default',
                      transition: 'background 0.15s ease',
                      opacity: isFailed ? 0.85 : 1,
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(15, 23, 42, 0.6)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <td style={{ padding: '12px 14px', color: '#94a3b8', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>
                      {r.created_at}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ fontWeight: 600, color: '#f1f5f9', maxWidth: '280px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {r.video_title || r.target_url}
                      </div>
                      {r.channel_name && <div style={{ fontSize: '0.72rem', color: '#64748b' }}>{r.channel_name}</div>}
                      {isFailed && r.error_message && (
                        <div style={{ fontSize: '0.7rem', color: '#f87171', marginTop: '2px', maxWidth: '280px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          Error: {r.error_message}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      {getStatusBadge(r.status)}
                    </td>
                    <td style={{ padding: '12px 14px', fontFamily: 'monospace', color: '#cbd5e1' }}>
                      {(Number(r.total_comments) || 0) > 0 ? Number(r.total_comments).toLocaleString() : '-'}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      {isCompleted && !isNaN(cibScoreNum) ? (
                        <span className={`badge ${getCibBadge(r.cib_level)}`}>
                          {cibScoreNum.toFixed(2)} ({r.cib_level || 'LOW'})
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ padding: '12px 14px', fontFamily: 'monospace', color: '#cbd5e1' }}>
                      {isCompleted && !isNaN(polIndexNum) ? polIndexNum.toFixed(2) : '-'}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      {sha256 ? (
                        <button
                          type="button"
                          onClick={(e) => handleCopyHash(e, r.id, sha256)}
                          title={`Klik untuk menyalin SHA-256 penuh:\n${sha256}`}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            background: 'rgba(16, 185, 129, 0.12)',
                            border: '1px solid rgba(16, 185, 129, 0.35)',
                            color: '#34d399',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontFamily: 'JetBrains Mono, monospace',
                            fontSize: '0.72rem',
                            cursor: 'pointer',
                          }}
                        >
                          <ShieldCheck size={12} />
                          <span>{sha256.slice(0, 10)}…{sha256.slice(-4)}</span>
                          {copiedId === r.id ? <Check size={11} /> : <Copy size={11} />}
                        </button>
                      ) : (
                        <span style={{ color: '#475569', fontSize: '0.75rem' }}>-</span>
                      )}
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        {isCompleted && (
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '5px 8px' }}
                            title="Buka Peta Situasi (SITREP)"
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
                          title="Hapus Arsip"
                          onClick={(e) => handleDelete(e, r.id)}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
