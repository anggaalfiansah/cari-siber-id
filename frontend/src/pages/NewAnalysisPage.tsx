import React, { useState } from 'react';
import { Play, Youtube, Instagram, AlertCircle } from 'lucide-react';
import { api } from '../api/bridge';

interface NewAnalysisPageProps {
  onRunStarted: (runId: string) => void;
  isBusy: boolean;
}

export const NewAnalysisPage: React.FC<NewAnalysisPageProps> = ({ onRunStarted, isBusy }) => {
  const [videoUrl, setVideoUrl] = useState('');
  const [limit, setLimit] = useState(1000);
  const [sortBy, setSortBy] = useState('top');
  const [includeReplies, setIncludeReplies] = useState(true);
  const [skipScrape, setSkipScrape] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoUrl.trim()) {
      setError('Silakan masukkan URL Video YouTube terlebih dahulu.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const res = await api.start_run({
        video_url: videoUrl.trim(),
        limit_comments: limit,
        sort_by: sortBy,
        include_replies: includeReplies,
        skip_scrape: skipScrape,
      });

      if (res.success && res.run_id) {
        onRunStarted(res.run_id);
      } else {
        setError(res.error || 'Gagal memulai analisis.');
      }
    } catch (err: any) {
      setError(err?.message || 'Terjadi kesalahan sistem.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '1.4rem', fontWeight: '700', color: '#f8fafc' }}>
          Mulai Analisis Ruang Siber Baru
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#94a3b8', marginTop: '4px' }}>
          Audit dinamika opini publik, deteksi narasi manipulasi bot/buzzer (CIB), dan petakan polarisasi kognitif.
        </p>
      </div>

      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          padding: '12px 16px',
          borderRadius: '8px',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Platform Selector */}
      <div className="panel" style={{ padding: '16px' }}>
        <label className="form-label">Platform Target</label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginTop: '8px' }}>
          {/* YouTube Card (Active) */}
          <div
            style={{
              border: '2px solid #0284c7',
              background: 'rgba(2, 132, 199, 0.12)',
              padding: '12px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
            }}
          >
            <Youtube size={22} color="#f43f5e" />
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#f8fafc' }}>
                YouTube
              </div>
              <div style={{ fontSize: '0.7rem', color: '#38bdf8' }}>
                Didukung & Aktif
              </div>
            </div>
          </div>

          {/* Instagram Card (Coming Soon) */}
          <div
            style={{
              border: '1px solid #334155',
              background: 'rgba(15, 23, 42, 0.5)',
              padding: '12px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              opacity: 0.55,
              cursor: 'not-allowed',
            }}
            title="Integrasi Instagram sedang dipersiapkan (Segera Hadir)"
          >
            <Instagram size={22} color="#94a3b8" />
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#94a3b8' }}>
                Instagram
              </div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
                Segera Hadir
              </div>
            </div>
          </div>

          {/* TikTok Card (Coming Soon) */}
          <div style={{
            border: '1px solid #334155',
            background: 'rgba(15, 23, 42, 0.5)',
            padding: '12px',
            borderRadius: '8px',
            opacity: 0.5,
            cursor: 'not-allowed',
          }}>
            <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#94a3b8' }}>TikTok</div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Segera Hadir</div>
          </div>

          {/* Play Store Card (Coming Soon) */}
          <div style={{
            border: '1px solid #334155',
            background: 'rgba(15, 23, 42, 0.5)',
            padding: '12px',
            borderRadius: '8px',
            opacity: 0.5,
            cursor: 'not-allowed',
          }}>
            <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#94a3b8' }}>Play Store</div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Segera Hadir</div>
          </div>
        </div>
      </div>

      {/* Form Settings */}
      <form onSubmit={handleStart} className="panel panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">URL Video YouTube Target *</label>
          <input
            type="text"
            className="form-input"
            placeholder="https://www.youtube.com/watch?v=... atau https://youtu.be/..."
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            disabled={isBusy || loading}
            autoFocus
          />
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
            Mendukung URL video reguler, Shorts, atau format singkat (youtu.be).
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Batas Komentar</label>
            <select
              className="form-select"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              disabled={isBusy || loading}
            >
              <option value={100}>100 Komentar (Uji Cepat)</option>
              <option value={500}>500 Komentar (Standar)</option>
              <option value={1000}>1.000 Komentar (Rekomendasi)</option>
              <option value={2500}>2.500 Komentar (Komprehensif)</option>
              <option value={5000}>5.000 Komentar (Penuh)</option>
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Urutan Pengambilan</label>
            <select
              className="form-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              disabled={isBusy || loading}
            >
              <option value="top">Top (Terpopuler & Interaksi Tertinggi)</option>
              <option value="new">New (Komentar Terbaru)</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '24px', paddingTop: '8px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <input
              type="checkbox"
              checked={includeReplies}
              onChange={(e) => setIncludeReplies(e.target.checked)}
              disabled={isBusy || loading}
            />
            Sertakan Balasan Komentar (Replies)
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <input
              type="checkbox"
              checked={skipScrape}
              onChange={(e) => setSkipScrape(e.target.checked)}
              disabled={isBusy || loading}
            />
            Gunakan Cache Scrape Lokal (Skip Scrape)
          </label>
        </div>

        <div style={{ borderTop: '1px solid rgba(51, 65, 85, 0.4)', paddingTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isBusy || loading || !videoUrl.trim()}
            style={{ padding: '10px 24px', fontSize: '0.95rem' }}
          >
            <Play size={18} />
            <span>{isBusy ? 'Operasi Lain Sedang Berjalan' : loading ? 'Mempersiapkan...' : 'Jalankan Analisis Kognitif'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
