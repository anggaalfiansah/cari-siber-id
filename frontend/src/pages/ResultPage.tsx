import React, { useState, useEffect, useMemo } from 'react';
import {
  Download,
  FolderOpen,
  ShieldAlert,
  BarChart2,
  MessageSquare,
  Image as ImageIcon,
  RefreshCw,
  AlertCircle,
  Maximize2,
  X,
  Layers,
  Users,
  ExternalLink,
  Flame,
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  Eye,
  Search,
  Filter,
  CheckCircle,
  ThumbsUp,
  Video,
  FileText,
  User,
  Bot,
  Copy,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import {
  RunResult,
  RunHistoryItem,
  ChartItem,
  FlaggedAccountItem,
  AuthorCommentItem,
  CoordinatedBotNetwork,
} from '../api/types';
import { api } from '../api/bridge';
import { KpiCard } from '../components/KpiCard';
import { SentimentPie } from '../components/SentimentPie';
import { TopTopicsBar } from '../components/TopTopicsBar';
import { TopicTable } from '../components/TopicTable';
import { AccountCommentsModal } from '../components/AccountCommentsModal';

interface ResultPageProps {
  runId: string | null;
  onNavigateNew: () => void;
  onNavigateNewWithReuse?: (runId: string) => void;
}

type TabType = 'buzzers' | 'cross_videos' | 'topics' | 'comments' | 'charts' | 'narrative';

export const ResultPage: React.FC<ResultPageProps> = ({ runId, onNavigateNew, onNavigateNewWithReuse }) => {
  const [result, setResult] = useState<RunResult | null>(null);
  const [runInfo, setRunInfo] = useState<RunHistoryItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<TabType>('buzzers');
  const [exporting, setExporting] = useState(false);
  const [exportNotice, setExportNotice] = useState('');
  const [selectedImage, setSelectedImage] = useState<ChartItem | null>(null);

  // Modal Akun Terindikasi & Detail Komentarnya
  const [selectedAccount, setSelectedAccount] = useState<FlaggedAccountItem | null>(null);

  // Filter untuk Tab Akun Terindikasi & Jaringan Bot Massal
  const [buzzerViewMode, setBuzzerViewMode] = useState<'individual' | 'botnet'>('individual');
  const [botnetSearch, setBotnetSearch] = useState('');
  const [buzzerSearch, setBuzzerSearch] = useState('');
  const [buzzerRiskFilter, setBuzzerRiskFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'SUSPICIOUS'>('ALL');
  const [buzzerActorFilter, setBuzzerActorFilter] = useState<'ALL' | 'PROVOCATEUR' | 'BUZZER' | 'BOT' | 'HYBRID'>('ALL');

  // Filter untuk Tab Eksplorasi Seluruh Komentar
  const [commentSearch, setCommentSearch] = useState('');
  const [commentSentimentFilter, setCommentSentimentFilter] = useState<'ALL' | 'Positif' | 'Netral' | 'Negatif'>('ALL');

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
      setRunInfo(info || null);
      setResult(res || null);

      if (res?.cross_video?.is_multi_video) {
        setActiveTab('cross_videos');
      } else if (res?.flagged_accounts && res.flagged_accounts.length > 0) {
        setActiveTab('buzzers');
      } else {
        setActiveTab('topics');
      }
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

  // Safe data extraction
  const cross = result?.cross_video;
  const safeComparisonMatrix = Array.isArray(cross?.video_comparison_matrix) ? cross.video_comparison_matrix : [];
  const safeTopics = Array.isArray(result?.topics) ? result.topics : [];
  const safeCharts = Array.isArray(result?.charts) ? result.charts : [];
  const safeSentimentData = Array.isArray(result?.interactive_data?.sentiment) ? result.interactive_data.sentiment : [];
  const safeTopicsData = Array.isArray(result?.interactive_data?.topics) ? result.interactive_data.topics : [];
  const safeCorpusComments: AuthorCommentItem[] = Array.isArray(result?.corpus_comments) ? result.corpus_comments : [];

  // Konsolidasi Akun Terindikasi (baik single video maupun multi-video)
  const flaggedAccounts: FlaggedAccountItem[] = useMemo(() => {
    if (Array.isArray(result?.flagged_accounts) && result.flagged_accounts.length > 0) {
      return result.flagged_accounts;
    }
    if (Array.isArray(cross?.cross_video_buzzers) && cross.cross_video_buzzers.length > 0) {
      return cross.cross_video_buzzers.map((b: any) => ({
        ...b,
        all_comments: b.all_comments || [],
        threat_tags: b.threat_tags || [`Lintas Video (${b.videos_count} Video)`],
      }));
    }
    return [];
  }, [result?.flagged_accounts, cross?.cross_video_buzzers]);

  // Filtered Flagged Accounts (Dual-Engine: Bot vs Provokator)
  const filteredFlaggedAccounts = useMemo(() => {
    return flaggedAccounts.filter((acc) => {
      if (buzzerRiskFilter !== 'ALL' && acc.cib_risk_level !== buzzerRiskFilter) {
        return false;
      }
      if (buzzerActorFilter !== 'ALL') {
        if (buzzerActorFilter === 'PROVOCATEUR') {
          const isProv = acc.actor_type?.startsWith('PROVOCATEUR') || (acc.provocation_score ?? 0) >= 40;
          if (!isProv) return false;
        } else if (buzzerActorFilter === 'BUZZER') {
          if (acc.actor_type !== 'BUZZER_COORDINATED') return false;
        } else if (buzzerActorFilter === 'BOT') {
          if (acc.actor_type !== 'SPAM_BOT') return false;
        } else if (buzzerActorFilter === 'HYBRID') {
          if (acc.actor_type !== 'HYBRID_THREAT') return false;
        }
      }
      if (buzzerSearch.trim()) {
        const q = buzzerSearch.toLowerCase();
        const matchUser = (acc.username || '').toLowerCase().includes(q);
        const matchId = (acc.author_channel_id || '').toLowerCase().includes(q);
        const matchTags = (acc.threat_tags || []).some((t) => t.toLowerCase().includes(q));
        const matchKeywords = (acc.detected_keywords || []).some((k) => k.toLowerCase().includes(q));
        const matchActor = (acc.actor_label || '').toLowerCase().includes(q);
        const matchSample = (acc.sample_comments || []).some((s) => s.toLowerCase().includes(q));
        return matchUser || matchId || matchTags || matchKeywords || matchActor || matchSample;
      }
      return true;
    });
  }, [flaggedAccounts, buzzerRiskFilter, buzzerActorFilter, buzzerSearch]);

  // Coordinated Bot Networks (Komentar Kembar Lintas Akun)
  const botNetworks: CoordinatedBotNetwork[] = useMemo(() => {
    return result?.coordinated_bot_networks || [];
  }, [result]);

  const filteredBotNetworks = useMemo(() => {
    return botNetworks.filter((bn) => {
      if (!botnetSearch.trim()) return true;
      const q = botnetSearch.toLowerCase();
      const matchText = (bn.template_text || '').toLowerCase().includes(q);
      const matchAccounts = (bn.accounts || []).some((acc) => acc.toLowerCase().includes(q));
      const matchVideos = (bn.target_video_titles || []).some((v) => v.toLowerCase().includes(q));
      return matchText || matchAccounts || matchVideos;
    });
  }, [botNetworks, botnetSearch]);

  // Filtered Corpus Comments
  const filteredCorpusComments = useMemo(() => {
    return safeCorpusComments.filter((c) => {
      if (commentSentimentFilter !== 'ALL' && c.ai_sentiment !== commentSentimentFilter) {
        return false;
      }
      if (commentSearch.trim()) {
        const q = commentSearch.toLowerCase();
        const matchText = (c.comment_text || '').toLowerCase().includes(q);
        const matchTopic = (c.topic_name || '').toLowerCase().includes(q);
        const matchVideo = (c.video_title || '').toLowerCase().includes(q);
        return matchText || matchTopic || matchVideo;
      }
      return true;
    });
  }, [safeCorpusComments, commentSentimentFilter, commentSearch]);

  // Buka detail akun dari username mana pun
  const handleInspectAuthor = (authorIdOrName: string) => {
    const existing = flaggedAccounts.find(
      (a) => a.author_channel_id === authorIdOrName || a.username === authorIdOrName
    );
    if (existing) {
      setSelectedAccount(existing);
    } else {
      // Buat entri sementara untuk akun yang belum masuk daftar flagged
      const matched = safeCorpusComments.filter(
        (c) => (c as any).author_channel_id === authorIdOrName || (c as any).username === authorIdOrName
      );
      setSelectedAccount({
        username: authorIdOrName,
        author_channel_id: authorIdOrName,
        author_channel_url: authorIdOrName.startsWith('UC') ? `https://www.youtube.com/channel/${authorIdOrName}` : '',
        videos_count: new Set(matched.map((m) => m.video_id)).size || 1,
        total_comments: matched.length || 1,
        total_likes_received: matched.reduce((acc, m) => acc + (m.like_count || 0), 0),
        target_video_ids: Array.from(new Set(matched.map((m) => m.video_id || ''))).filter(Boolean),
        target_video_titles: Array.from(new Set(matched.map((m) => m.video_title || ''))).filter(Boolean),
        sample_comments: matched.slice(0, 3).map((m) => m.comment_text),
        all_comments: matched,
        cib_risk_level: 'SUSPICIOUS',
        threat_tags: ['Pemeriksaan Pengguna Mandiri'],
      });
    }
  };

  if (!runId) {
    return (
      <div className="panel panel-body" style={{ textAlign: 'center', padding: '60px 20px', maxWidth: '580px', margin: '40px auto' }}>
        <BarChart2 size={42} color="#64748b" style={{ margin: '0 auto 12px' }} />
        <h2 style={{ fontSize: '1.2rem', color: '#f8fafc', marginBottom: '8px' }}>Belum Ada Hasil yang Dipilih</h2>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '20px', lineHeight: 1.5 }}>
          Silakan jalankan analisis baru atau pilih salah satu sesi selesai dari menu Riwayat Audit.
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

  if (runInfo && (runInfo.status === 'FAILED' || runInfo.status === 'CANCELLED')) {
    const isCancelled = runInfo.status === 'CANCELLED';
    return (
      <div className="panel panel-body" style={{ textAlign: 'center', padding: '48px 24px', maxWidth: '640px', margin: '40px auto' }}>
        {isCancelled ? (
          <AlertCircle size={44} color="#94a3b8" style={{ margin: '0 auto 14px' }} />
        ) : (
          <AlertTriangle size={44} color="#f87171" style={{ margin: '0 auto 14px' }} />
        )}
        <h2 style={{ fontSize: '1.25rem', color: '#f8fafc', marginBottom: '8px', fontWeight: 700 }}>
          {isCancelled ? 'Sesi Analisis Telah Dibatalkan' : 'Sesi Analisis Mengalami Kegagalan'}
        </h2>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '16px' }}>
          {isCancelled
            ? 'Operasi dihentikan atas permintaan pengguna sebelum hasil akhir selesai dikompilasi.'
            : 'Terjadi kendala teknis saat mengeksekusi tahapan pipeline analisis.'}
        </p>

        {runInfo.error_message && (
          <div style={{
            background: '#090d16',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '12px 16px',
            color: '#fca5a5',
            fontSize: '0.8rem',
            textAlign: 'left',
            margin: '0 auto 20px',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            maxHeight: '140px',
            overflowY: 'auto',
          }}>
            {runInfo.error_message}
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button className="btn btn-secondary" onClick={() => loadData(runId)}>
            <RefreshCw size={15} />
            <span>Coba Muat Ulang</span>
          </button>
          <button className="btn btn-primary" onClick={onNavigateNew}>
            <RotateCcw size={15} />
            <span>Mulai Analisis Baru</span>
          </button>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="panel panel-body" style={{ textAlign: 'center', padding: '40px 20px', maxWidth: '580px', margin: '40px auto' }}>
        <AlertCircle size={38} color="#f87171" style={{ margin: '0 auto 12px' }} />
        <h3 style={{ color: '#f8fafc', marginBottom: '8px', fontSize: '1.1rem' }}>Data Hasil Belum Tersedia</h3>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '18px' }}>
          {error || 'Berkas run belum selesai atau belum dieksekusi.'}
        </p>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
          <button className="btn btn-secondary" onClick={() => loadData(runId)}>
            Muat Ulang
          </button>
          <button className="btn btn-primary" onClick={onNavigateNew}>
            Analisis Baru
          </button>
        </div>
      </div>
    );
  }

  // Safe KPI calculations (mendukung pembacaan dari result direct maupun runInfo sqlite)
  const rawCibScore = (result?.cib_score !== undefined && result?.cib_score !== null)
    ? result.cib_score
    : (result?.meta?.cib_score !== undefined && result?.meta?.cib_score !== null)
      ? result.meta.cib_score
      : runInfo?.cib_score;
  const cibScoreNum = (rawCibScore !== undefined && rawCibScore !== null && !isNaN(Number(rawCibScore)))
    ? Number(rawCibScore)
    : 0.0;

  const rawCibLevel = result?.cib_level
    || result?.meta?.cib_level
    || runInfo?.cib_level
    || (cibScoreNum >= 0.7 ? 'CRITICAL' : cibScoreNum >= 0.35 ? 'HIGH' : cibScoreNum >= 0.2 ? 'MEDIUM' : 'LOW');
  const cibLevel = String(rawCibLevel).toLowerCase() as any;

  const rawPol = (result?.polarization_index !== undefined && result?.polarization_index !== null)
    ? result.polarization_index
    : (result?.meta?.polarization_index !== undefined && result?.meta?.polarization_index !== null)
      ? result.meta.polarization_index
      : runInfo?.polarization_index;
  const polIndex = (rawPol !== undefined && rawPol !== null && !isNaN(Number(rawPol)))
    ? Number(rawPol)
    : 0.0;
  const polBadgeLevel = polIndex >= 0.75 ? 'critical' : polIndex >= 0.5 ? 'high' : polIndex >= 0.25 ? 'medium' : 'low';
  const polBadgeText = polIndex >= 0.75 ? 'EKSTREM' : polIndex >= 0.5 ? 'TINGGI' : polIndex >= 0.25 ? 'MODERAT' : 'RENDAH';
  const polDesc = polIndex >= 0.5 ? 'Masyarakat terbelah secara tajam' : 'Sentimen relatif terarah atau satu kubu';

  const totalComments = Number(result?.meta?.total_comments) || 0;
  const totalCommenters = Number(result?.unique_authors_total || result?.meta?.unique_authors_total || totalComments) || 1;

  // Hitung jumlah risiko akun
  const critCount = flaggedAccounts.filter((a) => a.cib_risk_level === 'CRITICAL').length;
  const highCount = flaggedAccounts.filter((a) => a.cib_risk_level === 'HIGH').length;
  const medCount = flaggedAccounts.filter((a) => a.cib_risk_level === 'MEDIUM').length;
  const suspCount = flaggedAccounts.filter((a) => a.cib_risk_level === 'SUSPICIOUS').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Info & Actions */}
      <div
        className="panel"
        style={{
          padding: '20px 24px',
          background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.9) 0%, rgba(11, 15, 25, 0.95) 100%)',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>DASHBOARD INTELIJEN RUANG SIBER</span>
              {cross?.is_multi_video ? (
                <span style={{ background: 'rgba(2, 132, 199, 0.2)', border: '1px solid #0284c7', color: '#38bdf8', padding: '2px 8px', borderRadius: '10px', fontSize: '0.68rem', fontWeight: 700 }}>
                  MULTI-VIDEO CORPUS ({cross.total_videos} VIDEO)
                </span>
              ) : (
                <span style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', padding: '2px 8px', borderRadius: '10px', fontSize: '0.68rem', fontWeight: 700 }}>
                  SINGLE-VIDEO AUDIT
                </span>
              )}
            </div>

            <h1 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#f8fafc', marginTop: '6px', lineHeight: 1.3 }}>
              {result?.meta?.video_title || 'Laporan Ringkasan Opini'}
            </h1>

            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
              Kanal: <strong style={{ color: '#cbd5e1' }}>{result?.meta?.channel_name || 'Kanal YouTube'}</strong> • Run ID: <span className="mono-font" style={{ color: '#94a3b8' }}>{runId}</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={handleExportXlsx} disabled={exporting}>
              <Download size={15} />
              <span>{exporting ? 'Mengekspor...' : 'Ekspor XLSX Multi-Sheet'}</span>
            </button>

            <button className="btn btn-secondary" onClick={handleOpenFolder} title="Buka folder hasil run di file manager">
              <FolderOpen size={15} />
              <span>Buka Folder</span>
            </button>

            <button className="btn btn-secondary" onClick={onNavigateNew} title="Buat sesi analisis baru">
              <RotateCcw size={15} />
              <span>Analisis Baru</span>
            </button>
          </div>
        </div>

        {exportNotice && (
          <div style={{ marginTop: '14px', padding: '10px 14px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '6px', fontSize: '0.8rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={15} />
            <span>{exportNotice}</span>
          </div>
        )}
      </div>

      {/* KPI Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
        <KpiCard
          label="Total Komentar Diolah"
          value={totalComments.toLocaleString()}
          subValue={cross?.is_multi_video ? `Kolektif dari ${cross.total_videos} video` : 'Dianalisis IndoBERT & AI Gates'}
          icon={<MessageSquare size={18} />}
        />
        <KpiCard
          label="Skor Ancaman CIB"
          value={cibScoreNum.toFixed(2)}
          badge={{ text: String(rawCibLevel || 'LOW'), level: cibLevel }}
          subValue="Ancaman Operasi Bot / Buzzer"
          icon={<ShieldAlert size={18} />}
        />
        <KpiCard
          label="Indeks Polarisasi"
          value={polIndex.toFixed(2)}
          badge={{ text: polBadgeText, level: polBadgeLevel }}
          subValue={polDesc}
          icon={<BarChart2 size={18} />}
        />
        <KpiCard
          label="Akun Terindikasi Berisiko"
          value={flaggedAccounts.length.toLocaleString()}
          badge={{
            text: critCount > 0 ? `${critCount} KRITIS` : flaggedAccounts.length > 5 ? 'PERLU DITELITI' : 'TERKENDALI',
            level: critCount > 0 ? 'critical' : flaggedAccounts.length > 5 ? 'high' : 'low',
          }}
          subValue="Buzzer, spam bot, & provokator"
          icon={<Users size={18} />}
        />
        {cross?.is_multi_video && (
          <KpiCard
            label="Divergensi Framing"
            value={`${cross.sentiment_divergence_score || 0}%`}
            subValue="Selisih net sentimen antar kanal"
            icon={<Layers size={18} />}
          />
        )}
      </div>

      {/* Interactive Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '14px' }}>
        <div className="panel" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' }}>
            Distribusi Sentimen Agregat
          </div>
          <SentimentPie data={safeSentimentData} />
        </div>

        <div className="panel" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' }}>
            Klaster Topik Paling Banyak Dibahas
          </div>
          <TopTopicsBar data={safeTopicsData} />
        </div>
      </div>

      {/* Sub-Views Tabs */}
      <div className="panel" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="panel-header" style={{ padding: '10px 18px', background: 'rgba(15, 23, 42, 0.6)' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {/* TAB 1: AKUN TERINDIKASI & BUZZER (ALWAYS AVAILABLE) */}
            <button
              className={`btn ${activeTab === 'buzzers' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('buzzers')}
              style={{ fontSize: '0.8rem', padding: '7px 16px' }}
            >
              <Users size={14} />
              <span>Akun Terindikasi & Buzzer ({flaggedAccounts.length})</span>
            </button>

            {/* TAB 2: MULTI VIDEO COMPARISON (IF MULTI VIDEO) */}
            {cross?.is_multi_video && (
              <button
                className={`btn ${activeTab === 'cross_videos' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setActiveTab('cross_videos')}
                style={{ fontSize: '0.8rem', padding: '7px 16px' }}
              >
                <Layers size={14} />
                <span>Komparasi Video ({cross.total_videos})</span>
              </button>
            )}

            {/* TAB 3: TOPIK */}
            <button
              className={`btn ${activeTab === 'topics' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('topics')}
              style={{ fontSize: '0.8rem', padding: '7px 16px' }}
            >
              <MessageSquare size={14} />
              <span>Daftar Topik & Sub-Issue ({safeTopics.length})</span>
            </button>

            {/* TAB 4: CORPUS EXPLORER (SEMUA KOMENTAR) */}
            <button
              className={`btn ${activeTab === 'comments' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('comments')}
              style={{ fontSize: '0.8rem', padding: '7px 16px' }}
            >
              <FileText size={14} />
              <span>Eksplorasi Komentar ({totalComments})</span>
            </button>

            {/* TAB 5: CHARTS */}
            <button
              className={`btn ${activeTab === 'charts' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('charts')}
              style={{ fontSize: '0.8rem', padding: '7px 16px' }}
            >
              <ImageIcon size={14} />
              <span>Grafik Analitik ({safeCharts.length})</span>
            </button>

            {/* TAB 6: NARRATIVE */}
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
          {/* ======================================================== */}
          {/* TAB 1: AKUN TERINDIKASI & BUZZER (DRILL-DOWN KOMENTAR)    */}
          {/* ======================================================== */}
          {activeTab === 'buzzers' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* SUB-VIEW SWITCHER: INDIVIDUAL ACCOUNTS vs COORDINATED BOT NETWORKS */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '12px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  padding: '6px',
                  borderRadius: '10px',
                  border: '1px solid rgba(51, 65, 85, 0.5)',
                }}
              >
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => setBuzzerViewMode('individual')}
                    style={{
                      background: buzzerViewMode === 'individual' ? '#0284c7' : 'transparent',
                      color: buzzerViewMode === 'individual' ? '#ffffff' : '#94a3b8',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '7px',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <User size={15} />
                    <span>Profil Akun Terindikasi ({filteredFlaggedAccounts.length})</span>
                  </button>

                  <button
                    onClick={() => setBuzzerViewMode('botnet')}
                    style={{
                      background: buzzerViewMode === 'botnet' ? '#0284c7' : 'transparent',
                      color: buzzerViewMode === 'botnet' ? '#ffffff' : '#94a3b8',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '7px',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      transition: 'all 0.15s ease',
                      position: 'relative',
                    }}
                  >
                    <Bot size={15} />
                    <span>Jaringan Bot Massal ({botNetworks.length} Klaster Template)</span>
                    {botNetworks.length > 0 && (
                      <span
                        style={{
                          background: buzzerViewMode === 'botnet' ? 'rgba(255,255,255,0.25)' : 'rgba(239, 68, 68, 0.25)',
                          color: buzzerViewMode === 'botnet' ? '#ffffff' : '#f87171',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          padding: '1px 6px',
                          borderRadius: '10px',
                        }}
                      >
                        DETEKSI MASSAL
                      </span>
                    )}
                  </button>
                </div>

                <div style={{ fontSize: '0.75rem', color: '#64748b', paddingRight: '8px' }}>
                  {buzzerViewMode === 'individual'
                    ? 'Mode Pelacakan Individu (Dual-Engine)'
                    : 'Mode Deteksi Komentar Kembar Lintas Akun'}
                </div>
              </div>

              {buzzerViewMode === 'individual' && (<>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span>Pelacakan Akun Terindikasi Buzzer, Bot & Provokator</span>
                    <span style={{ fontSize: '0.75rem', background: 'rgba(2, 132, 199, 0.2)', color: '#38bdf8', border: '1px solid rgba(2, 132, 199, 0.35)', padding: '2px 9px', borderRadius: '10px', fontWeight: 600 }}>
                      {filteredFlaggedAccounts.length} Terindikasi dari {totalCommenters.toLocaleString()} Total Komentator ({((filteredFlaggedAccounts.length / totalCommenters) * 100).toFixed(1)}%)
                    </span>
                  </h3>
                  <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '3px', maxWidth: '680px', lineHeight: 1.4 }}>
                    Dual-Engine Forensik Siber membedakan <strong>Provokator Berdampak / Agitator Utas</strong> dengan <strong>Automated Bot & Buzzer Terarah</strong>. Klik tombol <strong>"Lihat Komentar & Dossier"</strong> untuk investigasi mendalam.
                  </p>
                </div>

                {/* Filter and Search Bar for Buzzers */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <div style={{ position: 'relative', width: '220px' }}>
                      <Search size={14} color="#64748b" style={{ position: 'absolute', left: '10px', top: '8px' }} />
                      <input
                        type="text"
                        placeholder="Cari akun atau teks..."
                        value={buzzerSearch}
                        onChange={(e) => setBuzzerSearch(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '5px 10px 5px 30px',
                          background: 'rgba(30, 41, 59, 0.6)',
                          border: '1px solid rgba(51, 65, 85, 0.6)',
                          borderRadius: '6px',
                          color: '#f8fafc',
                          fontSize: '0.78rem',
                          outline: 'none',
                        }}
                      />
                    </div>

                    <div style={{ display: 'flex', gap: '4px' }}>
                      {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'SUSPICIOUS'] as const).map((r) => {
                        const active = buzzerRiskFilter === r;
                        const col =
                          r === 'CRITICAL' ? '#ef4444' : r === 'HIGH' ? '#f59e0b' : r === 'MEDIUM' ? '#38bdf8' : '#94a3b8';
                        return (
                          <button
                            key={r}
                            onClick={() => setBuzzerRiskFilter(r)}
                            style={{
                              background: active ? `${col}25` : 'transparent',
                              border: `1px solid ${active ? col : 'rgba(51, 65, 85, 0.5)'}`,
                              color: active ? col : '#94a3b8',
                              padding: '4px 8px',
                              borderRadius: '6px',
                              fontSize: '0.7rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            {r}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Actor Typology Filter Chips */}
                  <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                    {[
                      { id: 'ALL', label: 'SEMUA TIPE', col: '#94a3b8' },
                      { id: 'PROVOCATEUR', label: '🔥 PROVOKATOR', col: '#ef4444' },
                      { id: 'BUZZER', label: '📢 BUZZER', col: '#f59e0b' },
                      { id: 'BOT', label: '🤖 SPAM BOT', col: '#38bdf8' },
                      { id: 'HYBRID', label: '⚔️ HYBRID', col: '#a855f7' },
                    ].map((t) => {
                      const active = buzzerActorFilter === t.id;
                      return (
                        <button
                          key={t.id}
                          onClick={() => setBuzzerActorFilter(t.id as any)}
                          style={{
                            background: active ? `${t.col}25` : 'rgba(15, 23, 42, 0.4)',
                            border: `1px solid ${active ? t.col : 'rgba(51, 65, 85, 0.4)'}`,
                            color: active ? t.col : '#94a3b8',
                            padding: '3px 8px',
                            borderRadius: '5px',
                            fontSize: '0.68rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          {t.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {filteredFlaggedAccounts.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: '#94a3b8', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '10px', border: '1px dashed #334155' }}>
                  <ShieldCheck size={40} color="#10b981" style={{ margin: '0 auto 10px' }} />
                  <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>
                    Tidak Terdeteksi Akun Mencurigakan yang Memenuhi Filter
                  </div>
                  <div style={{ fontSize: '0.78rem', marginTop: '4px', color: '#64748b' }}>
                    Komentator pada sesi ini berinteraksi secara organik atau tidak ada akun dengan anomali repetisi / copypasta.
                  </div>
                </div>
              ) : (
                <div style={{ overflowX: 'auto', border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '10px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                    <thead>
                      <tr style={{ background: 'rgba(30, 41, 59, 0.85)', borderBottom: '1px solid #334155', color: '#94a3b8', textAlign: 'left' }}>
                        <th style={{ padding: '12px 14px' }}>Akun & Tipologi Aktor</th>
                        <th style={{ padding: '12px 14px', textAlign: 'center' }}>Skor Provokasi (🔥)</th>
                        <th style={{ padding: '12px 14px', textAlign: 'center' }}>Skor Bot (🤖)</th>
                        <th style={{ padding: '12px 14px' }}>Bukti Forensik & Leksikon</th>
                        <th style={{ padding: '12px 14px', textAlign: 'center' }}>Aktivitas & Suka</th>
                        <th style={{ padding: '12px 14px', textAlign: 'center' }}>Polarisasi Sentimen</th>
                        <th style={{ padding: '12px 14px', textAlign: 'center' }}>Tingkat Risiko</th>
                        <th style={{ padding: '12px 14px', textAlign: 'center' }}>Tindakan</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredFlaggedAccounts.map((b) => {
                        const risk = b.cib_risk_level;
                        const riskColor =
                          risk === 'CRITICAL' ? '#ef4444' : risk === 'HIGH' ? '#f59e0b' : risk === 'MEDIUM' ? '#38bdf8' : '#94a3b8';
                        const riskBg =
                          risk === 'CRITICAL'
                            ? 'rgba(239, 68, 68, 0.15)'
                            : risk === 'HIGH'
                            ? 'rgba(245, 158, 11, 0.15)'
                            : risk === 'MEDIUM'
                            ? 'rgba(56, 189, 248, 0.15)'
                            : 'rgba(148, 163, 184, 0.15)';

                        const provScore = b.provocation_score ?? 0;
                        const botScore = b.bot_score ?? (b.inauthenticity_score ?? 0);

                        const pos = b.sentiment_breakdown?.Positif ?? (b.all_comments ? b.all_comments.filter((c) => c.ai_sentiment === 'Positif').length : 0);
                        const net = b.sentiment_breakdown?.Netral ?? (b.all_comments ? b.all_comments.filter((c) => c.ai_sentiment === 'Netral').length : 0);
                        const neg = b.sentiment_breakdown?.Negatif ?? (b.all_comments ? b.all_comments.filter((c) => c.ai_sentiment === 'Negatif').length : 0);

                        return (
                          <tr
                            key={b.author_channel_id || b.username}
                            style={{
                              borderBottom: '1px solid rgba(51, 65, 85, 0.4)',
                              transition: 'background 0.15s ease',
                              background: 'rgba(15, 23, 42, 0.4)',
                            }}
                          >
                            {/* Akun & Tipologi Aktor */}
                            <td style={{ padding: '12px 14px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <div
                                  style={{
                                    width: '36px',
                                    height: '36px',
                                    borderRadius: '50%',
                                    background: b.actor_type?.startsWith('PROVOCATEUR')
                                      ? 'linear-gradient(135deg, #ef4444 0%, #450a0a 100%)'
                                      : b.actor_type === 'HYBRID_THREAT'
                                      ? 'linear-gradient(135deg, #a855f7 0%, #3b0764 100%)'
                                      : 'linear-gradient(135deg, #0284c7 0%, #1e1b4b 100%)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontWeight: 700,
                                    fontSize: '0.85rem',
                                    color: '#f8fafc',
                                    flexShrink: 0,
                                  }}
                                >
                                  {b.username.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                  <div style={{ fontWeight: 600, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                                    <span>{b.username}</span>
                                  </div>
                                  {b.actor_label && (
                                    <div style={{ marginTop: '2px' }}>
                                      <span
                                        style={{
                                          fontSize: '0.66rem',
                                          fontWeight: 700,
                                          padding: '1px 6px',
                                          borderRadius: '4px',
                                          background: b.actor_type?.startsWith('PROVOCATEUR')
                                            ? 'rgba(239, 68, 68, 0.18)'
                                            : b.actor_type === 'HYBRID_THREAT'
                                            ? 'rgba(168, 85, 247, 0.18)'
                                            : 'rgba(2, 132, 199, 0.18)',
                                          color: b.actor_type?.startsWith('PROVOCATEUR')
                                            ? '#fca5a5'
                                            : b.actor_type === 'HYBRID_THREAT'
                                            ? '#c084fc'
                                            : '#7dd3fc',
                                          border: `1px solid ${
                                            b.actor_type?.startsWith('PROVOCATEUR')
                                              ? 'rgba(239, 68, 68, 0.4)'
                                              : b.actor_type === 'HYBRID_THREAT'
                                              ? 'rgba(168, 85, 247, 0.4)'
                                              : 'rgba(2, 132, 199, 0.4)'
                                          }`,
                                        }}
                                      >
                                        {b.actor_label}
                                      </span>
                                    </div>
                                  )}
                                  {b.author_channel_url ? (
                                    <a
                                      href={b.author_channel_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      style={{
                                        fontSize: '0.68rem',
                                        color: '#38bdf8',
                                        textDecoration: 'none',
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '3px',
                                        marginTop: '2px',
                                      }}
                                    >
                                      <span>Kanal YouTube</span>
                                      <ExternalLink size={10} />
                                    </a>
                                  ) : (
                                    <span style={{ fontSize: '0.66rem', color: '#64748b' }} className="mono-font">
                                      {b.author_channel_id}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </td>

                            {/* Skor Provokasi (🔥) */}
                            <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                              <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
                                <span style={{ fontWeight: 800, fontSize: '0.85rem', color: provScore >= 50 ? '#ef4444' : provScore >= 35 ? '#f87171' : '#94a3b8' }}>
                                  {provScore}/100
                                </span>
                                <div style={{ width: '48px', height: '4px', background: 'rgba(51, 65, 85, 0.5)', borderRadius: '2px', overflow: 'hidden' }}>
                                  <div
                                    style={{
                                      width: `${provScore}%`,
                                      height: '100%',
                                      background: '#ef4444',
                                    }}
                                  />
                                </div>
                              </div>
                            </td>

                            {/* Skor Bot (🤖) */}
                            <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                              <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
                                <span style={{ fontWeight: 800, fontSize: '0.85rem', color: botScore >= 50 ? '#0284c7' : botScore >= 35 ? '#38bdf8' : '#94a3b8' }}>
                                  {botScore}/100
                                </span>
                                <div style={{ width: '48px', height: '4px', background: 'rgba(51, 65, 85, 0.5)', borderRadius: '2px', overflow: 'hidden' }}>
                                  <div
                                    style={{
                                      width: `${botScore}%`,
                                      height: '100%',
                                      background: '#0284c7',
                                    }}
                                  />
                                </div>
                              </div>
                            </td>

                            {/* Bukti Forensik & Leksikon */}
                            <td style={{ padding: '12px 14px' }}>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                                {b.detected_keywords && b.detected_keywords.length > 0 && (
                                  <span
                                    style={{
                                      fontSize: '0.68rem',
                                      background: 'rgba(239, 68, 68, 0.18)',
                                      color: '#fca5a5',
                                      padding: '2px 7px',
                                      borderRadius: '4px',
                                      border: '1px solid rgba(239, 68, 68, 0.4)',
                                      fontWeight: 600,
                                    }}
                                  >
                                    Kata Hasutan: {b.detected_keywords.slice(0, 3).join(', ')}
                                  </span>
                                )}
                                {(b.threat_tags && b.threat_tags.length > 0 ? b.threat_tags : ['Aktivitas Berulang']).map((rawT, idx) => {
                                  const t = rawT.includes('<0 dtk') ? rawT.replace('<0 dtk', 'Posting Cepat') : rawT;
                                  const isBotnet = t.toLowerCase().includes('bot massal');
                                  const isBurst = t.toLowerCase().includes('burst');
                                  const isCopypasta = t.toLowerCase().includes('copypasta');
                                  return (
                                    <span
                                      key={idx}
                                      style={{
                                        fontSize: '0.68rem',
                                        background: isBotnet
                                          ? 'rgba(239, 68, 68, 0.2)'
                                          : isBurst
                                          ? 'rgba(245, 158, 11, 0.2)'
                                          : isCopypasta
                                          ? 'rgba(168, 85, 247, 0.2)'
                                          : 'rgba(2, 132, 199, 0.15)',
                                        color: isBotnet
                                          ? '#fca5a5'
                                          : isBurst
                                          ? '#fcd34d'
                                          : isCopypasta
                                          ? '#d8b4fe'
                                          : '#7dd3fc',
                                        padding: '2px 7px',
                                        borderRadius: '4px',
                                        border: `1px solid ${
                                          isBotnet
                                            ? 'rgba(239, 68, 68, 0.4)'
                                            : isBurst
                                            ? 'rgba(245, 158, 11, 0.4)'
                                            : isCopypasta
                                            ? 'rgba(168, 85, 247, 0.4)'
                                            : 'rgba(2, 132, 199, 0.3)'
                                        }`,
                                        fontWeight: isBotnet || isBurst ? 600 : 500,
                                      }}
                                    >
                                      {t}
                                    </span>
                                  );
                                })}
                              </div>
                            </td>

                            {/* Aktivitas & Suka */}
                            <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                              <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.85rem' }}>
                                {b.total_comments} Komentar
                              </div>
                              <div style={{ fontSize: '0.7rem', color: '#38bdf8', marginTop: '2px' }}>
                                {b.videos_count} Video
                              </div>
                              <div style={{ fontSize: '0.7rem', color: (b.total_likes_received || 0) > 0 ? '#fbbf24' : '#94a3b8', marginTop: '2px', fontWeight: 600 }}>
                                ❤️ {(b.total_likes_received || 0).toLocaleString()} Suka
                              </div>
                            </td>

                            {/* Sentimen */}
                            <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                              <div style={{ display: 'inline-flex', gap: '5px', fontSize: '0.72rem', fontWeight: 700 }}>
                                <span style={{ color: '#10b981' }}>{pos} Pos</span> /
                                <span style={{ color: '#94a3b8' }}>{net} Net</span> /
                                <span style={{ color: '#ef4444' }}>{neg} Neg</span>
                              </div>
                            </td>

                            {/* Risiko CIB */}
                            <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                              <span
                                style={{
                                  background: riskBg,
                                  color: riskColor,
                                  border: `1px solid ${riskColor}`,
                                  padding: '3px 9px',
                                  borderRadius: '12px',
                                  fontSize: '0.7rem',
                                  fontWeight: 700,
                                }}
                              >
                                {risk}
                              </span>
                            </td>

                            {/* Action: Lihat Semua Komentar */}
                            <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                              <button
                                className="btn btn-secondary"
                                onClick={() => setSelectedAccount(b)}
                                style={{
                                  padding: '5px 12px',
                                  fontSize: '0.75rem',
                                  background: 'rgba(2, 132, 199, 0.15)',
                                  borderColor: 'rgba(2, 132, 199, 0.4)',
                                  color: '#38bdf8',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '5px',
                                }}
                                title="Lihat semua komentar yang ditulis oleh akun ini"
                              >
                                <Eye size={13} />
                                <span>Lihat {b.total_comments} Komentar & Dossier</span>
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

          {/* TAMPILAN JARINGAN BOT MASSAL (KOMENTAR KEMBAR LINTAS AKUN) */}
          {buzzerViewMode === 'botnet' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <Bot size={18} color="#ef4444" />
                    <span>Deteksi Jaringan Bot Massal (Komentar Kembar Lintas Akun)</span>
                    <span style={{ fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.4)', padding: '2px 9px', borderRadius: '10px', fontWeight: 700 }}>
                      {filteredBotNetworks.length} Klaster Template Kembar
                    </span>
                  </h3>
                  <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '3px', maxWidth: '720px', lineHeight: 1.4 }}>
                    Sistem melacak pola <strong>Coordinated Inauthentic Behavior (CIB)</strong> di mana banyak akun pengguna yang berbeda memposting template teks yang <strong>sama persis / identik</strong>. Ini merupakan indikator kuat operasi bot farm terorganisir.
                  </p>
                </div>

                <div style={{ position: 'relative', width: '260px' }}>
                  <Search size={14} color="#64748b" style={{ position: 'absolute', left: '10px', top: '8px' }} />
                  <input
                    type="text"
                    placeholder="Cari teks template atau akun..."
                    value={botnetSearch}
                    onChange={(e) => setBotnetSearch(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '6px 10px 6px 30px',
                      background: 'rgba(30, 41, 59, 0.6)',
                      border: '1px solid rgba(51, 65, 85, 0.6)',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '0.78rem',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              {filteredBotNetworks.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: '#94a3b8', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '10px', border: '1px dashed #334155' }}>
                  <ShieldCheck size={40} color="#10b981" style={{ margin: '0 auto 10px' }} />
                  <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>
                    Tidak Ditemukan Pola Komentar Kembar Lintas Akun
                  </div>
                  <div style={{ fontSize: '0.78rem', marginTop: '4px', color: '#64748b' }}>
                    Seluruh komentar pada sesi ini ditulis dengan variasi bahasa organik tanpa adanya template duplikasi massal.
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {filteredBotNetworks.map((bn, bIdx) => {
                    const isCritical = bn.coordination_level === 'CRITICAL_MASS';
                    const isHigh = bn.coordination_level === 'HIGH_COORDINATION';
                    const borderColor = isCritical ? 'rgba(239, 68, 68, 0.45)' : isHigh ? 'rgba(245, 158, 11, 0.45)' : 'rgba(56, 189, 248, 0.35)';
                    const bgCard = isCritical ? 'rgba(239, 68, 68, 0.06)' : isHigh ? 'rgba(245, 158, 11, 0.05)' : 'rgba(15, 23, 42, 0.5)';
                    return (
                      <div
                        key={bIdx}
                        style={{
                          background: bgCard,
                          border: `1px solid ${borderColor}`,
                          borderRadius: '10px',
                          padding: '16px 18px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '12px',
                        }}
                      >
                        {/* Card Top: Badges & Stats */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                            <span
                              style={{
                                fontSize: '0.72rem',
                                fontWeight: 700,
                                padding: '3px 8px',
                                borderRadius: '6px',
                                background: isCritical ? 'rgba(239, 68, 68, 0.25)' : isHigh ? 'rgba(245, 158, 11, 0.25)' : 'rgba(56, 189, 248, 0.2)',
                                color: isCritical ? '#fca5a5' : isHigh ? '#fde047' : '#7dd3fc',
                                border: `1px solid ${isCritical ? '#ef4444' : isHigh ? '#f59e0b' : '#38bdf8'}`,
                              }}
                            >
                              {bn.coordination_badge}
                            </span>

                            <span
                              style={{
                                fontSize: '0.72rem',
                                fontWeight: 800,
                                padding: '3px 9px',
                                borderRadius: '6px',
                                background: 'rgba(239, 68, 68, 0.15)',
                                color: '#f87171',
                                border: '1px solid rgba(239, 68, 68, 0.3)',
                              }}
                            >
                              👥 {bn.unique_accounts_count} Akun Berbeda
                            </span>

                            <span
                              style={{
                                fontSize: '0.72rem',
                                fontWeight: 600,
                                padding: '3px 8px',
                                borderRadius: '6px',
                                background: 'rgba(56, 189, 248, 0.12)',
                                color: '#38bdf8',
                                border: '1px solid rgba(56, 189, 248, 0.25)',
                              }}
                            >
                              🎬 {bn.unique_videos_count} Video Sasaran
                            </span>

                            <span
                              style={{
                                fontSize: '0.72rem',
                                color: '#94a3b8',
                                background: 'rgba(51, 65, 85, 0.3)',
                                padding: '3px 8px',
                                borderRadius: '6px',
                              }}
                            >
                              🔁 {bn.total_occurrences}x Total Diposting
                            </span>
                          </div>

                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(bn.template_text);
                            }}
                            style={{
                              fontSize: '0.72rem',
                              background: 'rgba(51, 65, 85, 0.4)',
                              border: '1px solid rgba(100, 116, 139, 0.4)',
                              color: '#cbd5e1',
                              padding: '4px 10px',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px',
                            }}
                          >
                            <Copy size={12} />
                            <span>Salin Template</span>
                          </button>
                        </div>

                        {/* Template Text Quote */}
                        <div
                          style={{
                            background: '#090d16',
                            borderLeft: `4px solid ${isCritical ? '#ef4444' : isHigh ? '#f59e0b' : '#0284c7'}`,
                            borderRadius: '0 8px 8px 0',
                            padding: '12px 14px',
                            color: '#f8fafc',
                            fontSize: '0.85rem',
                            lineHeight: 1.5,
                            fontStyle: 'italic',
                            wordBreak: 'break-word',
                          }}
                        >
                          "{bn.template_text}"
                        </div>

                        {/* Video Targets & Target Accounts */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.76rem', color: '#94a3b8' }}>
                          {bn.target_video_titles && bn.target_video_titles.length > 0 && (
                            <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-start' }}>
                              <span style={{ fontWeight: 600, color: '#64748b', flexShrink: 0 }}>Target Video:</span>
                              <span style={{ color: '#cbd5e1' }}>
                                {bn.target_video_titles.slice(0, 3).join(' • ')}
                                {bn.target_video_titles.length > 3 ? ` (+${bn.target_video_titles.length - 3} video lainnya)` : ''}
                              </span>
                            </div>
                          )}

                          <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-start', flexWrap: 'wrap' }}>
                            <span style={{ fontWeight: 600, color: '#64748b', flexShrink: 0 }}>Akun Pelaku:</span>
                            <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                              {bn.accounts.map((acc, aIdx) => (
                                <span
                                  key={aIdx}
                                  onClick={() => handleInspectAuthor(acc)}
                                  style={{
                                    background: 'rgba(2, 132, 199, 0.15)',
                                    color: '#38bdf8',
                                    border: '1px solid rgba(2, 132, 199, 0.35)',
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    fontSize: '0.72rem',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                  }}
                                  title="Klik untuk membuka riwayat komentar akun ini"
                                >
                                  {acc}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

        </div>
      )}

          {/* ======================================================== */}
          {/* TAB 2: KOMPARASI MULTI-VIDEO                             */}
          {/* ======================================================== */}
          {activeTab === 'cross_videos' && cross && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                  Matriks Komparasi Opini Antar Video & Kanal
                </h3>
                <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>
                  Membandingkan framing narasi, polarisasi respon netizen, dan tingkat ancaman CIB pada masing-masing video target.
                </p>
              </div>

              <div style={{ overflowX: 'auto', border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '10px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ background: 'rgba(30, 41, 59, 0.85)', borderBottom: '1px solid #334155', color: '#94a3b8', textAlign: 'left' }}>
                      <th style={{ padding: '10px 14px' }}>Video & Kanal</th>
                      <th style={{ padding: '10px 14px', textAlign: 'right' }}>Total Komentar</th>
                      <th style={{ padding: '10px 14px', textAlign: 'right' }}>Komentator Unik</th>
                      <th style={{ padding: '10px 14px', textAlign: 'center' }}>Distribusi Sentimen (Pos / Net / Neg)</th>
                      <th style={{ padding: '10px 14px', textAlign: 'right' }}>Net Score</th>
                      <th style={{ padding: '10px 14px' }}>Topik Dominan</th>
                      <th style={{ padding: '10px 14px', textAlign: 'center' }}>Skor CIB</th>
                    </tr>
                  </thead>
                  <tbody>
                    {safeComparisonMatrix.map((row) => {
                      const netScore = Number(row?.net_sentiment) || 0;
                      const netColor = netScore > 0 ? '#10b981' : netScore < 0 ? '#ef4444' : '#94a3b8';
                      const rowCib = typeof row?.cib_score === 'number' ? row.cib_score : Number(row?.cib_score) || 0;
                      return (
                        <tr key={row.video_id} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.4)' }}>
                          <td style={{ padding: '12px 14px' }}>
                            <div style={{ fontWeight: 600, color: '#f8fafc', lineHeight: 1.3 }}>{row.video_title}</div>
                            <div style={{ fontSize: '0.72rem', color: '#38bdf8', marginTop: '3px' }}>
                              {row.channel_name} • <span className="mono-font">{row.video_id}</span>
                            </div>
                          </td>
                          <td style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 600, color: '#f8fafc' }}>
                            {(Number(row.total_comments) || 0).toLocaleString()}
                          </td>
                          <td style={{ padding: '12px 14px', textAlign: 'right', color: '#cbd5e1' }}>
                            {(Number(row.unique_commenters) || 0).toLocaleString()}
                          </td>
                          <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
                              <span style={{ color: '#10b981', fontWeight: 600 }}>{row.positive_pct || 0}%</span> /
                              <span style={{ color: '#94a3b8' }}>{row.neutral_pct || 0}%</span> /
                              <span style={{ color: '#ef4444', fontWeight: 600 }}>{row.negative_pct || 0}%</span>
                            </div>
                          </td>
                          <td style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 700, color: netColor }}>
                            {netScore > 0 ? `+${netScore}%` : `${netScore}%`}
                          </td>
                          <td style={{ padding: '12px 14px', color: '#cbd5e1' }}>
                            <span style={{ background: 'rgba(30, 41, 59, 0.7)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem' }}>
                              {row.top_topic || '-'}
                            </span>
                          </td>
                          <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                            <span
                              style={{
                                background: rowCib >= 0.7 ? 'rgba(239, 68, 68, 0.2)' : rowCib >= 0.35 ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                                color: rowCib >= 0.7 ? '#f87171' : rowCib >= 0.35 ? '#fbbf24' : '#10b981',
                                border: `1px solid ${rowCib >= 0.7 ? '#ef4444' : rowCib >= 0.35 ? '#f59e0b' : '#10b981'}`,
                                padding: '2px 8px',
                                borderRadius: '10px',
                                fontSize: '0.72rem',
                                fontWeight: 700,
                              }}
                            >
                              {rowCib.toFixed(2)}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 3: DAFTAR TOPIK & SUB-ISSUE                          */}
          {/* ======================================================== */}
          {activeTab === 'topics' && <TopicTable topics={safeTopics} />}

          {/* ======================================================== */}
          {/* TAB 4: EKSPLORASI SELURUH KOMENTAR (CORPUS EXPLORER)     */}
          {/* ======================================================== */}
          {activeTab === 'comments' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                    Eksplorasi Komentar Netizen ({safeCorpusComments.length} Komentar Termuat)
                  </h3>
                  <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>
                    Telusuri komentar individual, periksa sentimen AI, atau klik username komentator untuk melihat seluruh komentar akun tersebut.
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <div style={{ position: 'relative', width: '240px' }}>
                    <Search size={14} color="#64748b" style={{ position: 'absolute', left: '10px', top: '8px' }} />
                    <input
                      type="text"
                      placeholder="Cari teks komentar..."
                      value={commentSearch}
                      onChange={(e) => setCommentSearch(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '5px 10px 5px 30px',
                        background: 'rgba(30, 41, 59, 0.6)',
                        border: '1px solid rgba(51, 65, 85, 0.6)',
                        borderRadius: '6px',
                        color: '#f8fafc',
                        fontSize: '0.78rem',
                        outline: 'none',
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '4px' }}>
                    {(['ALL', 'Positif', 'Netral', 'Negatif'] as const).map((sent) => {
                      const active = commentSentimentFilter === sent;
                      const col =
                        sent === 'Positif' ? '#10b981' : sent === 'Negatif' ? '#ef4444' : sent === 'Netral' ? '#94a3b8' : '#38bdf8';
                      return (
                        <button
                          key={sent}
                          onClick={() => setCommentSentimentFilter(sent)}
                          style={{
                            background: active ? `${col}25` : 'transparent',
                            border: `1px solid ${active ? col : 'rgba(51, 65, 85, 0.5)'}`,
                            color: active ? col : '#94a3b8',
                            padding: '4px 8px',
                            borderRadius: '6px',
                            fontSize: '0.7rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          {sent === 'ALL' ? 'Semua' : sent}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {filteredCorpusComments.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: '#64748b', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '10px' }}>
                  Tidak ada komentar yang cocok dengan filter pencarian.
                </div>
              ) : (
                <div style={{ overflowX: 'auto', border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '10px', maxHeight: '600px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead style={{ position: 'sticky', top: 0, zIndex: 2 }}>
                      <tr style={{ background: 'rgba(30, 41, 59, 0.95)', borderBottom: '1px solid #334155', color: '#94a3b8', textAlign: 'left' }}>
                        <th style={{ padding: '10px 14px' }}>Penulis Akun</th>
                        <th style={{ padding: '10px 14px' }}>Teks Komentar</th>
                        <th style={{ padding: '10px 14px', textAlign: 'center' }}>Sentimen</th>
                        <th style={{ padding: '10px 14px' }}>Topik / Sub-Issue</th>
                        <th style={{ padding: '10px 14px', textAlign: 'center' }}>Suka</th>
                        <th style={{ padding: '10px 14px', textAlign: 'center' }}>Aksi</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredCorpusComments.map((c, idx) => {
                        const sColor =
                          c.ai_sentiment === 'Positif' ? '#10b981' : c.ai_sentiment === 'Negatif' ? '#ef4444' : '#94a3b8';
                        const sBg =
                          c.ai_sentiment === 'Positif'
                            ? 'rgba(16, 185, 129, 0.15)'
                            : c.ai_sentiment === 'Negatif'
                            ? 'rgba(239, 68, 68, 0.15)'
                            : 'rgba(148, 163, 184, 0.15)';
                        const authorKey = (c as any).author_channel_id || (c as any).username || 'Anonim';

                        return (
                          <tr key={c.comment_id || idx} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.3)' }}>
                            <td style={{ padding: '10px 14px', verticalAlign: 'top', width: '180px' }}>
                              <button
                                onClick={() => handleInspectAuthor(authorKey)}
                                style={{
                                  background: 'transparent',
                                  border: 'none',
                                  color: '#38bdf8',
                                  fontWeight: 600,
                                  cursor: 'pointer',
                                  textAlign: 'left',
                                  padding: 0,
                                  fontSize: '0.8rem',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                }}
                                title="Klik untuk melihat semua komentar dari akun ini"
                              >
                                <span>{(c as any).username || 'Anonim'}</span>
                                <Eye size={11} />
                              </button>
                              {c.video_title && (
                                <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '3px' }}>
                                  {c.video_title}
                                </div>
                              )}
                            </td>

                            <td style={{ padding: '10px 14px', verticalAlign: 'top', color: '#f1f5f9', lineHeight: 1.45 }}>
                              {c.comment_text}
                            </td>

                            <td style={{ padding: '10px 14px', verticalAlign: 'top', textAlign: 'center', width: '90px' }}>
                              <span style={{ background: sBg, color: sColor, border: `1px solid ${sColor}44`, padding: '2px 8px', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 700 }}>
                                {c.ai_sentiment}
                              </span>
                            </td>

                            <td style={{ padding: '10px 14px', verticalAlign: 'top', width: '180px' }}>
                              <div style={{ color: '#cbd5e1', fontSize: '0.75rem', fontWeight: 600 }}>{c.business_category || '-'}</div>
                              <div style={{ color: '#94a3b8', fontSize: '0.7rem', fontStyle: 'italic' }}>{c.sub_issue || c.topic_name || ''}</div>
                            </td>

                            <td style={{ padding: '10px 14px', verticalAlign: 'top', textAlign: 'center', width: '70px', color: (c.like_count || 0) > 0 ? '#fbbf24' : '#64748b' }}>
                              {(c.like_count || 0).toLocaleString()}
                            </td>

                            <td style={{ padding: '10px 14px', verticalAlign: 'top', textAlign: 'center', width: '110px' }}>
                              <button
                                className="btn btn-secondary"
                                onClick={() => handleInspectAuthor(authorKey)}
                                style={{ padding: '3px 8px', fontSize: '0.7rem' }}
                                title="Lihat semua komentar akun ini"
                              >
                                Profil Akun
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 5: CHARTS                                            */}
          {/* ======================================================== */}
          {activeTab === 'charts' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(440px, 1fr))', gap: '18px' }}>
              {safeCharts.length === 0 ? (
                <div style={{ padding: '36px', textAlign: 'center', color: '#64748b', gridColumn: '1 / -1' }}>
                  Belum ada grafik visualisasi yang tersedia.
                </div>
              ) : (
                safeCharts.map((c) => (
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
                ))
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 6: NARRATIVE INSIGHT AI                              */}
          {/* ======================================================== */}
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
                {result?.narrative_md || 'Belum ada narasi yang terkompilasi.'}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>

      {/* Modal Komentar Akun Terindikasi (Drill-Down Dossier) */}
      {selectedAccount && (
        <AccountCommentsModal
          account={selectedAccount}
          runId={runId}
          onClose={() => setSelectedAccount(null)}
        />
      )}

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
