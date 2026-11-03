import React, { useState, useEffect } from 'react';
import { Download, FolderOpen, ShieldAlert, BarChart2, MessageSquare, Image, RefreshCw, AlertCircle, Maximize2, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { RunResult, RunHistoryItem, ChartItem } from '../api/types';
import { api } from '../api/bridge';
import { KpiCard } from '../components/KpiCard';
import { SentimentPie } from '../components/SentimentPie';
import { TopTopicsBar } from '../components/TopTopicsBar';
import { TopicTable } from '../components/TopicTable';

interface ResultPageProps {
  runId: string | null;
  onNavigateNew: () => void;
}

export const ResultPage: React.FC<ResultPageProps> = ({ runId, onNavigateNew }) => {
  const [result, setResult] = useState<RunResult | null>(null);
  const [runInfo, setRunInfo] = useState<RunHistoryItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'topics' | 'charts' | 'narrative'>('topics');
  const [exporting, setExporting] = useState(false);
  const [exportNotice, setExportNotice] = useState('');
  const [selectedImage, setSelectedImage] = useState<ChartItem | null>(null);

  useEffect(() => {
    if (runId) {
      loadData(runId);
    }
  }, [runId]);

  const loadData = async (id: string) => {
    setLoading(true);
    setError('');
    try {
      const [info, res] = await Promise.all([
        api.get_run(id),
        api.get_run_results(id),
      ]);
      setRunInfo(info);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || 'Gagal memuat data hasil.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportXlsx = async () => {
    if (!runId) return;
    setExporting(true);
    setExportNotice('');
    try {
      const res = await api.export_xlsx(runId);
      if (res.success && res.path) {
        setExportNotice(`Laporan Excel berhasil dibuat: ${res.path}`);
      } else {
        setError(res.error || 'Gagal mengekspor file Excel.');
      }
    } catch (err: any) {
      setError(err?.message || 'Terjadi kesalahan saat ekspor.');
    } finally {
      setExporting(false);
    }
  };

  const handleOpenFolder = async () => {
    if (!runId) return;
    await api.open_folder(runId);
  };

  if (!runId) {
    return (
      <div className="panel panel-body" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <BarChart2 size={40} color="#64748b" style={{ margin: '0 auto 12px' }} />
        <h2 style={{ fontSize: '1.2rem', color: '#f8fafc', marginBottom: '8px' }}>Belum Ada Hasil yang Dipilih</h2>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '20px' }}>
          Silakan jalankan analisis baru atau pilih dari riwayat audit siber.
        </p>
        <button className="btn btn-primary" onClick={onNavigateNew}>
          Mulai Analisis Baru
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: '12px' }}>
        <RefreshCw size={24} color="#38bdf8" style={{ animation: 'spin 1.5s linear infinite' }} />
        <span style={{ color: '#94a3b8' }}>Memuat laporan intelijen kognitif...</span>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="panel panel-body" style={{ textAlign: 'center', padding: '40px 20px' }}>
        <AlertCircle size={36} color="#ef4444" style={{ margin: '0 auto 12px' }} />
        <h3 style={{ color: '#f87171', marginBottom: '8px' }}>Gagal Memuat Hasil Analisis</h3>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '16px' }}>{error}</p>
        <button className="btn btn-secondary" onClick={() => runId && loadData(runId)}>
          Coba Lagi
        </button>
      </div>
    );
  }

  const cibLevel = (runInfo?.cib_level || 'LOW').toLowerCase() as any;
  const totalComments = result.meta.total_comments || runInfo?.total_comments || 0;
  const polIndex = runInfo?.polarization_index ?? 0;
  const polDesc = polIndex < 0.15 ? 'Konsensus Seragam (Non-Polarized)' : polIndex < 0.45 ? 'Polarisasi Moderat' : 'Polarisasi Tajam (Konflik Opini)';
  const polBadgeLevel = polIndex < 0.15 ? 'low' : polIndex < 0.45 ? 'medium' : 'high';
  const polBadgeText = polIndex < 0.15 ? 'SERAGAM' : polIndex < 0.45 ? 'MODERAT' : 'TERBELAH';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', paddingBottom: '30px' }}>
      {/* Header Info & Actions */}
      <div className="panel" style={{ padding: '18px 22px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              LAPORAN INTELIJEN KOGNITIF • {result.meta.channel_name || 'YOUTUBE'}
            </div>
            <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f8fafc', marginTop: '6px' }}>
              {result.meta.video_title}
            </h1>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
              Run ID: <span className="mono-font" style={{ color: '#94a3b8' }}>{runId}</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button className="btn btn-primary" onClick={handleExportXlsx} disabled={exporting}>
              <Download size={16} />
              <span>{exporting ? 'Mengekspor...' : 'Ekspor XLSX'}</span>
            </button>

            <button className="btn btn-secondary" onClick={handleOpenFolder} title="Buka folder output file">
              <FolderOpen size={16} />
              <span>Buka Folder</span>
            </button>
          </div>
        </div>

        {exportNotice && (
          <div style={{ marginTop: '14px', padding: '10px 14px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '6px', fontSize: '0.8rem', color: '#34d399' }}>
            {exportNotice}
          </div>
        )}
      </div>

      {/* KPI Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
        <KpiCard
          label="Total Komentar"
          value={totalComments.toLocaleString()}
          subValue="Dianalisis IndoBERT & AI Gates"
          icon={<MessageSquare size={18} />}
        />
        <KpiCard
          label="Skor Ancaman CIB"
          value={runInfo?.cib_score !== undefined ? runInfo.cib_score.toFixed(2) : '0.00'}
          badge={{ text: runInfo?.cib_level || 'LOW', level: cibLevel }}
          subValue="Indikator Operasi Bot / Buzzer"
          icon={<ShieldAlert size={18} />}
        />
        <KpiCard
          label="Indeks Polarisasi"
          value={polIndex.toFixed(2)}
          badge={{ text: polBadgeText, level: polBadgeLevel }}
          subValue={polDesc}
          icon={<BarChart2 size={18} />}
        />
      </div>

      {/* Interactive Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '14px' }}>
        <div className="panel" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' }}>
            Distribusi Sentimen Audiens
          </div>
          <SentimentPie data={result.interactive_data.sentiment} />
        </div>

        <div className="panel" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' }}>
            Klaster Topik Paling Banyak Dibahas
          </div>
          <TopTopicsBar data={result.interactive_data.topics} />
        </div>
      </div>

      {/* Sub-Views Tabs */}
      <div className="panel" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="panel-header" style={{ padding: '10px 18px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className={`btn ${activeTab === 'topics' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('topics')}
              style={{ fontSize: '0.8rem', padding: '7px 16px' }}
            >
              <MessageSquare size={14} />
              <span>Daftar Topik & Sub-Issue ({result.topics.length})</span>
            </button>

            <button
              className={`btn ${activeTab === 'charts' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('charts')}
              style={{ fontSize: '0.8rem', padding: '7px 16px' }}
            >
              <Image size={14} />
              <span>Grafik Analitik ({result.charts.length})</span>
            </button>

            <button
              className={`btn ${activeTab === 'narrative' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('narrative')}
              style={{ fontSize: '0.8rem', padding: '7px 16px' }}
            >
              <BarChart2 size={14} />
              <span>Narasi Insight AI</span>
            </button>
          </div>
        </div>

        <div className="panel-body">
          {activeTab === 'topics' && <TopicTable topics={result.topics} />}

          {activeTab === 'charts' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(440px, 1fr))', gap: '18px' }}>
              {result.charts.map((c) => (
                <div
                  key={c.id}
                  style={{
                    background: '#090d16',
                    border: '1px solid #1e293b',
                    borderRadius: '10px',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <div style={{
                    padding: '12px 16px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    borderBottom: '1px solid #1e293b',
                    color: '#e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}>
                    <span>{c.title}</span>
                    <button
                      className="btn btn-secondary"
                      onClick={() => setSelectedImage(c)}
                      style={{ padding: '3px 8px', fontSize: '0.75rem' }}
                      title="Perbesar gambar"
                    >
                      <Maximize2 size={13} />
                    </button>
                  </div>
                  <div
                    style={{ background: '#ffffff', padding: '10px', cursor: 'pointer' }}
                    onClick={() => setSelectedImage(c)}
                  >
                    <img
                      src={c.data_uri}
                      alt={c.title}
                      style={{ width: '100%', height: 'auto', display: 'block', borderRadius: '4px' }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'narrative' && (
            <div className="markdown-container">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid #1e293b' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <BarChart2 size={20} color="#38bdf8" />
                  </div>
                  <div>
                    <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', margin: 0, padding: 0, background: 'none', border: 'none' }}>
                      Dokumen Intelijen Kognitif & Narasi Publik
                    </h2>
                    <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                      Dihasilkan otomatis oleh Agentic NLP & IndoBERT Intelligence Pipeline
                    </span>
                  </div>
                </div>
              </div>

              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ node, ...props }) => (
                    <div className="markdown-table-wrapper">
                      <table {...props} />
                    </div>
                  ),
                }}
              >
                {result.narrative_md}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>

      {/* Image Modal Lightbox */}
      {selectedImage && (
        <div
          onClick={() => setSelectedImage(null)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(5px)',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '30px',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '12px',
              maxWidth: '92vw',
              maxHeight: '92vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <div style={{
              padding: '12px 18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #1e293b',
            }}>
              <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#f8fafc' }}>
                {selectedImage.title}
              </span>
              <button
                className="btn btn-secondary"
                onClick={() => setSelectedImage(null)}
                style={{ padding: '4px 8px' }}
              >
                <X size={16} />
              </button>
            </div>
            <div style={{ background: '#ffffff', padding: '14px', overflow: 'auto' }}>
              <img
                src={selectedImage.data_uri}
                alt={selectedImage.title}
                style={{ maxWidth: '100%', maxHeight: '78vh', display: 'block', margin: '0 auto' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
