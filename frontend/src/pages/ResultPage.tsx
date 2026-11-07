import React, { useState, useEffect, useMemo } from 'react';
import {
  Monitor,
  Download,
  FolderOpen,
  ShieldAlert,
  BarChart2,
  MessageSquare,
  RefreshCw,
  AlertCircle,
  X,
  Layers,
  Users,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  Eye,
  Search,
  CheckCircle,
  FileText,
  User,
  Bot,
  Copy,
  Check,
  Sparkles,
  Zap,
  Printer,
  Lock,
  Radio,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import {
  RunResult,
  RunHistoryItem,
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
  isBriefingMode?: boolean;
  onToggleBriefingMode?: () => void;
}

type TabType = 'buzzers' | 'topics' | 'narrative' | 'comments';

const DEFAULT_THREAT_LEXICON = [
  'papua merdeka',
  'merdeka',
  'opm',
  'kkb',
  'boikot',
  'pencitraan',
  'rezim',
  'oligarki',
  'korup',
  'mark-up',
  'fiktif',
  'diretas',
  'lumpuh',
  'bocor',
  'backdoor',
  'ddos',
  'sara',
  'penindasan',
  'pelanggaran ham',
  'tarik semua pasukan',
  'militerisme',
];

const renderForensicHighlightedText = (text: string, extraKeywords: string[] = []) => {
  if (!text) return '-';
  const allKw = Array.from(
    new Set([...DEFAULT_THREAT_LEXICON, ...extraKeywords].map((k) => k.trim()).filter((k) => k.length >= 3))
  );
  if (allKw.length === 0) return text;

  const escaped = allKw
    .sort((a, b) => b.length - a.length)
    .map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const pattern = new RegExp(`(${escaped.join('|')})`, 'gi');
  const parts = text.split(pattern);

  return parts.map((part, idx) => {
    const isHit = allKw.some((k) => k.toLowerCase() === part.toLowerCase());
    if (isHit) {
      return (
        <mark
          key={idx}
          style={{
            background: 'rgba(239, 68, 68, 0.25)',
            color: '#fca5a5',
            padding: '1px 5px',
            borderRadius: '4px',
            border: '1px solid rgba(239, 68, 68, 0.5)',
            fontWeight: 700,
          }}
        >
          {part}
        </mark>
      );
    }
    return part;
  });
};

export const ResultPage: React.FC<ResultPageProps> = ({
  runId,
  onNavigateNew,
  isBriefingMode,
  onToggleBriefingMode,
}) => {
  const [result, setResult] = useState<RunResult | null>(null);
  const [runInfo, setRunInfo] = useState<RunHistoryItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<TabType>('buzzers');
  const [exporting, setExporting] = useState(false);
  const [exportNotice, setExportNotice] = useState('');
  const [copiedHash, setCopiedHash] = useState(false);

  // Modal Akun Terindikasi & Detail Komentarnya
  const [selectedAccount, setSelectedAccount] = useState<FlaggedAccountItem | null>(null);

  // Sub-view Tab 1: 'individual' (Dossier Akun) vs 'botnet' (Jaringan Bot Massal)
  const [buzzerViewMode, setBuzzerViewMode] = useState<'individual' | 'botnet'>('individual');
  const [botnetSearch, setBotnetSearch] = useState('');
  const [buzzerSearch, setBuzzerSearch] = useState('');
  const [buzzerRiskFilter, setBuzzerRiskFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'SUSPICIOUS'>('ALL');
  const [buzzerActorFilter, setBuzzerActorFilter] = useState<'ALL' | 'PROVOCATEUR' | 'BUZZER' | 'BOT' | 'HYBRID'>('ALL');

  // State Agentic Context Calibrator & Instant Re-Analysis
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [calibrationReasoning, setCalibrationReasoning] = useState<string>('');
  const [customWhitelist, setCustomWhitelist] = useState<string[]>([]);
  const [customThreats, setCustomThreats] = useState<string[]>([]);
  const [newWhitelistTag, setNewWhitelistTag] = useState('');
  const [newThreatTag, setNewThreatTag] = useState('');
  const [calibrationNotice, setCalibrationNotice] = useState<string>('');

  // Filter untuk Tab 4: Eksplorasi Bukti Komentar
  const [commentSearch, setCommentSearch] = useState('');
  const [commentSentimentFilter, setCommentSentimentFilter] = useState<'ALL' | 'Positif' | 'Netral' | 'Negatif'>('ALL');

  // Shortcut F11 untuk Mode Komando Puskodal (Briefing Mode)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F11' && onToggleBriefingMode) {
        e.preventDefault();
        onToggleBriefingMode();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onToggleBriefingMode]);

  useEffect(() => {
    if (runId) {
      loadData(runId);
    }
  }, [runId]);

  const loadData = async (id: string, preserveTab: boolean = false) => {
    if (!preserveTab) setLoading(true);
    setError('');
    try {
      const [info, res] = await Promise.all([
        api.get_run(id),
        api.get_run_results(id),
      ]);
      setRunInfo(info || null);
      setResult(res || null);

      if (!preserveTab) {
        setActiveTab('buzzers');
      }
    } catch (err: any) {
      setError(err?.message || 'Gagal memuat data hasil.');
    } finally {
      if (!preserveTab) setLoading(false);
    }
  };

  const handleRequestAICalibration = async () => {
    if (!runId) return;
    setIsCalibrating(true);
    setCalibrationNotice('');
    try {
      const res = await api.get_ai_threat_calibration({ run_id: runId });
      if (res && res.success) {
        setCalibrationReasoning(res.reasoning_summary || '');
        const newWl = res.whitelist_recommendations || [];
        const newTh = res.hostile_threat_keywords || [];
        setCustomWhitelist((prev) => Array.from(new Set([...prev, ...newWl])));
        setCustomThreats((prev) => Array.from(new Set([...prev, ...newTh])));
        setCalibrationNotice(`✓ Rekomendasi AI berhasil didapatkan: ${newWl.length} usulan whitelist dan ${newTh.length} target ancaman.`);
      } else {
        setCalibrationNotice(res?.error || 'Gagal memanggil kalibrasi AI.');
      }
    } catch (e: any) {
      setCalibrationNotice(e?.message || 'Terjadi kesalahan saat memanggil kalibrasi AI.');
    } finally {
      setIsCalibrating(false);
    }
  };

  const handleReanalyze = async () => {
    if (!runId) return;
    setIsReanalyzing(true);
    setCalibrationNotice('');
    try {
      const res = await api.reanalyze_intelligence({
        run_id: runId,
        whitelist: customWhitelist,
        threats: customThreats,
      });
      if (res && res.success) {
        await loadData(runId, true);
        setCalibrationNotice(`⚡ Berhasil! Intelijen diperbarui seketika: ${res.bot_networks_count ?? 0} klaster bot, ${res.flagged_accounts_count ?? 0} akun teridentifikasi.`);
      } else {
        setCalibrationNotice(res?.error || 'Gagal melakukan analisa ulang.');
      }
    } catch (e: any) {
      setCalibrationNotice(e?.message || 'Terjadi kesalahan saat analisa ulang.');
    } finally {
      setIsReanalyzing(false);
    }
  };

  const addWhitelistTag = () => {
    const val = newWhitelistTag.trim();
    if (val && !customWhitelist.includes(val)) {
      setCustomWhitelist([...customWhitelist, val]);
      setNewWhitelistTag('');
    }
  };

  const removeWhitelistTag = (tag: string) => {
    setCustomWhitelist(customWhitelist.filter((t) => t !== tag));
  };

  const addThreatTag = () => {
    const val = newThreatTag.trim();
    if (val && !customThreats.includes(val)) {
      setCustomThreats([...customThreats, val]);
      setNewThreatTag('');
    }
  };

  const removeThreatTag = (tag: string) => {
    setCustomThreats(customThreats.filter((t) => t !== tag));
  };

  const handleExportXlsx = async () => {
    if (!runId) return;
    setExporting(true);
    setExportNotice('');
    try {
      const res = await api.export_xlsx(runId);
      if (res.success && res.path) {
        setExportNotice(`Laporan Excel Forensik (lengkap dengan Segel SHA-256 & Grafik) berhasil dibuat: ${res.path}`);
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
  const safeSentimentData = Array.isArray(result?.interactive_data?.sentiment) ? result.interactive_data.sentiment : [];
  const safeTopicsData = Array.isArray(result?.interactive_data?.topics) ? result.interactive_data.topics : [];
  const safeCorpusComments: AuthorCommentItem[] = Array.isArray(result?.corpus_comments) ? result.corpus_comments : [];

  const sha256Hash = result?.sha256_hash || result?.meta?.sha256_hash || runInfo?.sha256_hash || '';

  const handleCopySha256 = () => {
    if (!sha256Hash) return;
    navigator.clipboard?.writeText(sha256Hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  // Konsolidasi Akun Terindikasi
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

  // Hitung Rasio Agitator Organik vs Operasi Bot
  const actorRatioStats = useMemo(() => {
    let agitatorCount = 0;
    let botBuzzerCount = 0;
    flaggedAccounts.forEach((a) => {
      if (a.actor_type?.startsWith('PROVOCATEUR') || ((a.provocation_score ?? 0) > (a.bot_score ?? 0))) {
        agitatorCount += 1;
      } else {
        botBuzzerCount += 1;
      }
    });
    return { agitatorCount, botBuzzerCount };
  }, [flaggedAccounts]);

  // Kumpulkan seluruh kode DISARM Framework yang terdeteksi
  const detectedDisarmMatrix = useMemo(() => {
    const counts: Record<string, number> = {};
    flaggedAccounts.forEach((a) => {
      const list = (a.disarm_framework && a.disarm_framework.length > 0)
        ? a.disarm_framework
        : (a.threat_tags || []).filter((t) => t.startsWith('DISARM'));
      list.forEach((code) => {
        counts[code] = (counts[code] || 0) + 1;
      });
    });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [flaggedAccounts]);

  // Filtered Flagged Accounts
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
          if (acc.actor_type !== 'SPAM_BOT' && acc.actor_type !== 'COORDINATED_BOT_NETWORK') return false;
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

  // Coordinated Bot Networks
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
        const matchDomain = (c.threat_domain || c.business_category || '').toLowerCase().includes(q);
        const matchVideo = (c.video_title || '').toLowerCase().includes(q);
        return matchText || matchTopic || matchDomain || matchVideo;
      }
      return true;
    });
  }, [safeCorpusComments, commentSentimentFilter, commentSearch]);

  const handleInspectAuthor = (authorIdOrName: string) => {
    const existing = flaggedAccounts.find(
      (a) => a.author_channel_id === authorIdOrName || a.username === authorIdOrName
    );
    if (existing) {
      setSelectedAccount(existing);
    } else {
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
        <h2 style={{ fontSize: '1.2rem', color: '#f8fafc', marginBottom: '8px' }}>Belum Ada Sesi Operasi yang Dipilih</h2>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '20px', lineHeight: 1.5 }}>
          Silakan inisialisasi operasi analisis baru atau pilih salah satu arsip operasi dari menu <strong>4. Arsip Operasi</strong>.
        </p>
        <button className="btn btn-primary" onClick={onNavigateNew}>
          1. Operasi Baru
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: '12px' }}>
        <RefreshCw size={24} color="#38bdf8" style={{ animation: 'spin 1.5s linear infinite' }} />
        <span style={{ color: '#94a3b8' }}>Memuat Peta Situasi (SITREP) Intelijen Kognitif...</span>
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
          {isCancelled ? 'Sesi Operasi Dibatalkan' : 'Sesi Operasi Mengalami Kendala'}
        </h2>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '16px' }}>
          {isCancelled
            ? 'Operasi dihentikan atas perintah analis sebelum kompilasi akhir selesai.'
            : 'Terjadi kendala saat mengeksekusi tahapan pipeline.'}
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
            <span>Operasi Baru</span>
          </button>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="panel panel-body" style={{ textAlign: 'center', padding: '40px 20px', maxWidth: '580px', margin: '40px auto' }}>
        <AlertCircle size={38} color="#f87171" style={{ margin: '0 auto 12px' }} />
        <h3 style={{ color: '#f8fafc', marginBottom: '8px', fontSize: '1.1rem' }}>Data SITREP Belum Tersedia</h3>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '18px' }}>
          {error || 'Berkas operasi belum selesai dikompilasi.'}
        </p>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
          <button className="btn btn-secondary" onClick={() => loadData(runId)}>
            Muat Ulang
          </button>
          <button className="btn btn-primary" onClick={onNavigateNew}>
            Operasi Baru
          </button>
        </div>
      </div>
    );
  }

  // Safe KPI calculations
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
  const polDesc = polIndex >= 0.5 ? 'Friksi opini tajam antar kubu' : 'Konsensus publik relatif stabil';

  const totalComments = Number(result?.meta?.total_comments) || 0;
  const totalCommenters = Number(result?.unique_authors_total || result?.meta?.unique_authors_total || totalComments) || 1;
  const critCount = flaggedAccounts.filter((a) => a.cib_risk_level === 'CRITICAL').length;

  // Hitung proporsi Silent Majority vs Loud Minority
  const loudMinorityCommentsCount = flaggedAccounts.reduce((acc, a) => acc + (a.total_comments || 0), 0);
  const loudMinorityPct = totalComments > 0 ? Math.min(100, Math.round((loudMinorityCommentsCount / totalComments) * 100)) : 0;
  const silentMajorityPct = Math.max(0, 100 - loudMinorityPct);
  const silentMajorityText =
    result?.polarization_metrics?.silent_majority_consensus ||
    `Mayoritas pasif (${silentMajorityPct}% volume interaksi) menunjukkan diskusi organik warga, sedangkan ${loudMinorityPct}% volume dipicu oleh ${flaggedAccounts.length} akun bising/terkoordinasi.`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {/* Header Info & Forensic Seals */}
      <div
        className="panel"
        style={{
          padding: '18px 22px',
          background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.92) 0%, rgba(11, 15, 25, 0.98) 100%)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            {/* Top Status & Integrity Badges */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.74rem', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                3. PETA SITUASI INTELIJEN KOGNITIF (SITREP PUSSIBERAD)
              </span>

              {cross?.is_multi_video ? (
                <span style={{ background: 'rgba(2, 132, 199, 0.2)', border: '1px solid #0284c7', color: '#38bdf8', padding: '2px 8px', borderRadius: '10px', fontSize: '0.66rem', fontWeight: 700 }}>
                  MULTI-VIDEO CORPUS ({cross.total_videos} VIDEO)
                </span>
              ) : (
                <span style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', padding: '2px 8px', borderRadius: '10px', fontSize: '0.66rem', fontWeight: 700 }}>
                  SINGLE-TARGET AUDIT
                </span>
              )}

              {/* Badge Verified by 4 Agentic Gates */}
              <span
                style={{
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.45)',
                  color: '#34d399',
                  padding: '2px 8px',
                  borderRadius: '10px',
                  fontSize: '0.66rem',
                  fontWeight: 800,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
                title="Telah diverifikasi oleh Quality Gate, Topic Gate, Verification Gate, dan Report Gate"
              >
                <ShieldCheck size={12} />
                <span>VERIFIED BY 4 AGENTIC GATES</span>
              </span>

              {/* Badge SHA-256 Chain of Custody */}
              {sha256Hash && (
                <button
                  type="button"
                  onClick={handleCopySha256}
                  title={`Klik untuk menyalin Segel Forensik Digital SHA-256:\n${sha256Hash}`}
                  style={{
                    background: 'rgba(245, 158, 11, 0.14)',
                    border: '1px solid rgba(245, 158, 11, 0.45)',
                    color: '#fbbf24',
                    padding: '2px 8px',
                    borderRadius: '10px',
                    fontSize: '0.66rem',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    cursor: 'pointer',
                  }}
                >
                  <Lock size={11} />
                  <span>SHA-256: {sha256Hash.slice(0, 10)}…{sha256Hash.slice(-4)}</span>
                  {copiedHash ? <Check size={11} /> : <Copy size={11} />}
                </button>
              )}
            </div>

            <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f8fafc', marginTop: '6px', lineHeight: 1.3 }}>
              {result?.meta?.video_title || 'Laporan Situasi Ruang Siber'}
            </h1>

            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
              Sumber Kanal: <strong style={{ color: '#cbd5e1' }}>{result?.meta?.channel_name || 'Multi-Platform Corpus'}</strong> • ID Operasi: <span className="mono-font" style={{ color: '#94a3b8' }}>{runId}</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={handleExportXlsx} disabled={exporting}>
              <Download size={15} />
              <span>{exporting ? 'Mengekspor...' : 'Ekspor Bukti XLSX'}</span>
            </button>

            <button className="btn btn-secondary" onClick={handleOpenFolder} title="Buka direktori barang bukti lokal">
              <FolderOpen size={15} />
              <span>Folder Bukti</span>
            </button>

            <button
              className="btn"
              onClick={onToggleBriefingMode}
              style={{
                background: isBriefingMode
                  ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(6, 182, 212, 0.25) 100%)'
                  : 'rgba(30, 41, 59, 0.6)',
                border: isBriefingMode ? '1px solid #10b981' : '1px solid #334155',
                color: isBriefingMode ? '#34d399' : '#f8fafc',
                boxShadow: isBriefingMode ? '0 0 15px rgba(16, 185, 129, 0.4)' : 'none',
                fontWeight: 700,
                fontSize: '0.8rem',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
              title="Pintasan Keyboard: F11 — Beralih ke Tampilan Layar Puskodal Penuh"
            >
              <Monitor size={15} color={isBriefingMode ? '#34d399' : '#38bdf8'} />
              <span>{isBriefingMode ? 'Mode Puskodal AKTIF (F11)' : 'Mode Puskodal (F11)'}</span>
            </button>

            <button className="btn btn-secondary" onClick={onNavigateNew} title="Mulai Operasi Pemantauan Baru">
              <RotateCcw size={15} />
              <span>Operasi Baru</span>
            </button>
          </div>
        </div>

        {exportNotice && (
          <div style={{ marginTop: '12px', padding: '10px 14px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '6px', fontSize: '0.8rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={15} />
            <span>{exportNotice}</span>
          </div>
        )}
      </div>

      {/* KPI Cards Row (With Dual-Engine Agitator vs Bot Ratio) */}
      <div style={{ display: 'grid', gridTemplateColumns: isBriefingMode ? 'repeat(auto-fit, minmax(230px, 1fr))' : 'repeat(auto-fit, minmax(195px, 1fr))', gap: '12px' }}>
        <KpiCard
          label="Total Bukti Komentar"
          value={totalComments.toLocaleString()}
          subValue={cross?.is_multi_video ? `${cross.total_videos} video (${totalCommenters.toLocaleString()} akun unik)` : `${totalCommenters.toLocaleString()} akun komentator unik`}
          icon={<MessageSquare size={18} />}
        />
        <KpiCard
          isBriefingMode={isBriefingMode}
          label="Skor Ancaman CIB"
          value={cibScoreNum.toFixed(2)}
          badge={{ text: String(rawCibLevel || 'LOW'), level: cibLevel }}
          subValue={`${botNetworks.length} klaster template bot kembar`}
          icon={<ShieldAlert size={18} />}
        />
        <KpiCard
          isBriefingMode={isBriefingMode}
          label="Indeks Polarisasi"
          value={polIndex.toFixed(2)}
          badge={{ text: polBadgeText, level: polBadgeLevel }}
          subValue={polDesc}
          icon={<BarChart2 size={18} />}
        />
        <KpiCard
          label="Agitator vs Operasi Bot"
          value={`${actorRatioStats.agitatorCount} : ${actorRatioStats.botBuzzerCount}`}
          badge={{
            text: critCount > 0 ? `${critCount} KRITIS` : `${flaggedAccounts.length} AKUN`,
            level: critCount > 0 ? 'critical' : flaggedAccounts.length > 5 ? 'high' : 'low',
          }}
          subValue={`🔥 ${actorRatioStats.agitatorCount} Provokator | 🤖 ${actorRatioStats.botBuzzerCount} Bot/Buzzer`}
          icon={<Users size={18} />}
        />
      </div>

      {/* Dekonstruksi Opini: Silent Majority vs Loud Minority Banner */}
      <div
        className="panel"
        style={{
          padding: '12px 18px',
          background: 'linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, rgba(15, 23, 42, 0.85) 60%, rgba(239, 68, 68, 0.12) 100%)',
          border: '1px solid rgba(51, 65, 85, 0.6)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc' }}>
            <Radio size={15} color="#10b981" />
            <span>DEKONSTRUKSI OPINI: KONSENSUS MAYORITAS PASIF (SILENT MAJORITY) VS MINORITAS BISING (LOUD MINORITY)</span>
          </div>
          <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', fontWeight: 700 }}>
            <span style={{ color: '#34d399' }}>🟢 Mayoritas Organik: {silentMajorityPct}%</span>
            <span style={{ color: '#f87171' }}>🔴 Distorsi Akun Terindikasi CIB/Agitator: {loudMinorityPct}%</span>
          </div>
        </div>

        {/* Visual Split Bar */}
        <div style={{ width: '100%', height: '8px', borderRadius: '4px', overflow: 'hidden', display: 'flex', background: '#1e293b' }}>
          <div style={{ width: `${silentMajorityPct}%`, background: '#10b981', transition: 'width 0.3s ease' }} />
          <div style={{ width: `${loudMinorityPct}%`, background: '#ef4444', transition: 'width 0.3s ease' }} />
        </div>

        <div style={{ fontSize: '0.76rem', color: '#cbd5e1', lineHeight: 1.4 }}>
          {silentMajorityText}
        </div>
      </div>

      {/* Interactive Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '14px' }}>
        <div className="panel" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' }}>
            Distribusi Sentimen Ruang Siber
          </div>
          <SentimentPie data={safeSentimentData} />
        </div>

        <div className="panel" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' }}>
            Peta Klaster Isu & Domain Ancaman Dominan
          </div>
          <TopTopicsBar data={safeTopicsData} />
        </div>
      </div>

      {/* =================================================================== */}
      {/* 4 ACTION-ORIENTED CORE TABS (STANDAR PUSKODAL)                      */}
      {/* =================================================================== */}
      <div className="panel" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="panel-header" style={{ padding: '10px 18px', background: 'rgba(15, 23, 42, 0.7)' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {/* TAB 1: INTELIJEN AKTOR & JARINGAN BOT (CIB) */}
            <button
              className={`btn ${activeTab === 'buzzers' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('buzzers')}
              style={{ fontSize: '0.8rem', padding: '8px 16px', fontWeight: 700 }}
            >
              <Users size={15} />
              <span>1. Intelijen Aktor & Jaringan Bot ({flaggedAccounts.length} Akun | {botNetworks.length} Botnet)</span>
            </button>

            {/* TAB 2: PETA NARASI & KLASTER ISU (+ KOMPARASI MULTI-VIDEO) */}
            <button
              className={`btn ${activeTab === 'topics' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('topics')}
              style={{ fontSize: '0.8rem', padding: '8px 16px', fontWeight: 700 }}
            >
              <Layers size={15} />
              <span>
                2. Peta Narasi & Klaster Isu ({safeTopics.length} Topik{cross?.is_multi_video ? ` • ${cross.total_videos} Video` : ''})
              </span>
            </button>

            {/* TAB 3: LAPORAN KIRKA SIBER SOSIAL (AI NARRATIVE & DISARM) */}
            <button
              className={`btn ${activeTab === 'narrative' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('narrative')}
              style={{ fontSize: '0.8rem', padding: '8px 16px', fontWeight: 700 }}
            >
              <BarChart2 size={15} />
              <span>3. Laporan KIRKA Siber Sosial (AI Narrative)</span>
            </button>

            {/* TAB 4: EKSPLORASI BUKTI KOMENTAR (FORENSIC CORPUS) */}
            <button
              className={`btn ${activeTab === 'comments' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('comments')}
              style={{ fontSize: '0.8rem', padding: '8px 16px', fontWeight: 700 }}
            >
              <FileText size={15} />
              <span>4. Eksplorasi Bukti Komentar ({totalComments.toLocaleString()})</span>
            </button>
          </div>
        </div>

        <div className="panel-body">
          {/* ======================================================== */}
          {/* TAB 1: INTELIJEN AKTOR & JARINGAN BOT (CIB)              */}
          {/* ======================================================== */}
          {activeTab === 'buzzers' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* PANEL ASISTEN AGENTIC AI: KALIBRASI KONTEKS & HUMAN-IN-THE-LOOP (SELALU TERLIHAT DI TAB 1) */}
              <div
                style={{
                  background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(16, 185, 129, 0.08) 50%, rgba(15, 23, 42, 0.95) 100%)',
                  border: '1px solid rgba(16, 185, 129, 0.35)',
                  borderRadius: '12px',
                  padding: '14px 18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div
                      style={{
                        background: 'rgba(16, 185, 129, 0.2)',
                        padding: '8px',
                        borderRadius: '8px',
                        border: '1px solid rgba(16, 185, 129, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Sparkles size={18} color="#10b981" />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <span>Kalibrasi Konteks Agentic AI & Eliminasi False Positive (Human-in-the-Loop)</span>
                      </div>
                      <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '2px 0 0' }}>
                        Pisahkan yel-yel patriotik/apresiasi organik warga ("TNI Bersama Rakyat") dari operasi bot musuh dan terapkan analisa ulang instan (&lt;2 dtk).
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <button
                      onClick={handleRequestAICalibration}
                      disabled={isCalibrating || isReanalyzing}
                      style={{
                        background: isCalibrating ? '#334155' : 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
                        color: '#ffffff',
                        border: 'none',
                        padding: '7px 14px',
                        borderRadius: '7px',
                        fontSize: '0.78rem',
                        fontWeight: 700,
                        cursor: isCalibrating ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      <Sparkles size={14} />
                      <span>{isCalibrating ? 'Memindai Konteks...' : 'Kalibrasi Konteks AI'}</span>
                    </button>

                    {(customWhitelist.length > 0 || customThreats.length > 0) && (
                      <button
                        onClick={handleReanalyze}
                        disabled={isReanalyzing || isCalibrating}
                        style={{
                          background: isReanalyzing ? '#334155' : 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
                          color: '#ffffff',
                          border: 'none',
                          padding: '7px 14px',
                          borderRadius: '7px',
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          cursor: isReanalyzing ? 'not-allowed' : 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <Zap size={14} />
                        <span>{isReanalyzing ? 'Menganalisis Ulang...' : 'Terapkan & Analisa Ulang'}</span>
                      </button>
                    )}
                  </div>
                </div>

                {calibrationNotice && (
                  <div style={{ fontSize: '0.76rem', color: '#6ee7b7', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle size={14} />
                    <span>{calibrationNotice}</span>
                  </div>
                )}

                {calibrationReasoning && (
                  <div style={{ background: 'rgba(2, 132, 199, 0.08)', borderLeft: '3px solid #38bdf8', padding: '7px 12px', borderRadius: '0 6px 6px 0', fontSize: '0.76rem', color: '#e2e8f0' }}>
                    <strong style={{ color: '#38bdf8' }}>Catatan Perwira Analis PUSSIBERAD: </strong>
                    {calibrationReasoning}
                  </div>
                )}

                {(customWhitelist.length > 0 || customThreats.length > 0 || calibrationReasoning) && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
                    <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '8px', padding: '10px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#6ee7b7', marginBottom: '6px' }}>
                        🟢 Whitelist Slogan / Apresiasi Warga ({customWhitelist.length})
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginBottom: '6px' }}>
                        {customWhitelist.map((item, idx) => (
                          <span key={idx} style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#6ee7b7', fontSize: '0.7rem', padding: '2px 7px', borderRadius: '5px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                            "{item}"
                            <button onClick={() => removeWhitelistTag(item)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: 0 }}>
                              <X size={11} />
                            </button>
                          </span>
                        ))}
                      </div>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <input
                          type="text"
                          placeholder="+ Tambah slogan whitelist..."
                          value={newWhitelistTag}
                          onChange={(e) => setNewWhitelistTag(e.target.value)}
                          onKeyDown={(e) => { if (e.key === 'Enter') addWhitelistTag(); }}
                          style={{ flex: 1, padding: '4px 8px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(51, 65, 85, 0.7)', borderRadius: '5px', color: '#f8fafc', fontSize: '0.74rem' }}
                        />
                        <button onClick={addWhitelistTag} style={{ background: '#059669', border: 'none', borderRadius: '5px', color: '#fff', padding: '0 10px', fontSize: '0.74rem', fontWeight: 600, cursor: 'pointer' }}>
                          Tambah
                        </button>
                      </div>
                    </div>

                    <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '8px', padding: '10px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#fca5a5', marginBottom: '6px' }}>
                        🔴 Kata Kunci Target Ancaman Hostile ({customThreats.length})
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginBottom: '6px' }}>
                        {customThreats.map((item, idx) => (
                          <span key={idx} style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#fca5a5', fontSize: '0.7rem', padding: '2px 7px', borderRadius: '5px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                            "{item}"
                            <button onClick={() => removeThreatTag(item)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: 0 }}>
                              <X size={11} />
                            </button>
                          </span>
                        ))}
                      </div>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <input
                          type="text"
                          placeholder="+ Tambah kata kunci ancaman..."
                          value={newThreatTag}
                          onChange={(e) => setNewThreatTag(e.target.value)}
                          onKeyDown={(e) => { if (e.key === 'Enter') addThreatTag(); }}
                          style={{ flex: 1, padding: '4px 8px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(51, 65, 85, 0.7)', borderRadius: '5px', color: '#f8fafc', fontSize: '0.74rem' }}
                        />
                        <button onClick={addThreatTag} style={{ background: '#dc2626', border: 'none', borderRadius: '5px', color: '#fff', padding: '0 10px', fontSize: '0.74rem', fontWeight: 600, cursor: 'pointer' }}>
                          Tambah
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* SUB-VIEW SWITCHER: DOSSIER AKUN INDIVIDU VS KLASTER JARINGAN BOT MASSAL */}
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
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    <User size={15} />
                    <span>Dossier Akun Terindikasi ({filteredFlaggedAccounts.length})</span>
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
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    <Bot size={15} />
                    <span>Jaringan Bot Massal / Template Kembar ({botNetworks.length} Klaster)</span>
                    {botNetworks.length > 0 && (
                      <span
                        style={{
                          background: buzzerViewMode === 'botnet' ? 'rgba(255,255,255,0.25)' : 'rgba(239, 68, 68, 0.25)',
                          color: buzzerViewMode === 'botnet' ? '#ffffff' : '#f87171',
                          fontSize: '0.68rem',
                          fontWeight: 800,
                          padding: '1px 6px',
                          borderRadius: '10px',
                        }}
                      >
                        CIB TERDETEKSI
                      </span>
                    )}
                  </button>
                </div>

                <div style={{ fontSize: '0.75rem', color: '#94a3b8', paddingRight: '8px' }}>
                  🔥 {actorRatioStats.agitatorCount} Provokator/Agitator • 🤖 {actorRatioStats.botBuzzerCount} Bot/Buzzer Terkoordinasi
                </div>
              </div>

              {buzzerViewMode === 'individual' ? (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
                    <div>
                      <h3 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#f8fafc' }}>
                        Daftar Dossier Akun Terindikasi (Dual-Engine: Skor Provokasi 🔥 vs Skor Bot 🤖)
                      </h3>
                      <p style={{ fontSize: '0.76rem', color: '#94a3b8', marginTop: '2px' }}>
                        Klik tombol <strong>"Lihat Dossier"</strong> pada baris akun untuk membuka seluruh riwayat komentar dan sorotan kata kunci provokasi.
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                      <div style={{ position: 'relative', width: '210px' }}>
                        <Search size={14} color="#64748b" style={{ position: 'absolute', left: '10px', top: '8px' }} />
                        <input
                          type="text"
                          placeholder="Cari akun atau kata kunci..."
                          value={buzzerSearch}
                          onChange={(e) => setBuzzerSearch(e.target.value)}
                          style={{
                            width: '100%',
                            padding: '5px 10px 5px 30px',
                            background: 'rgba(30, 41, 59, 0.6)',
                            border: '1px solid rgba(51, 65, 85, 0.6)',
                            borderRadius: '6px',
                            color: '#f8fafc',
                            fontSize: '0.76rem',
                          }}
                        />
                      </div>

                      <div style={{ display: 'flex', gap: '4px' }}>
                        {[
                          { id: 'ALL', label: 'SEMUA', col: '#94a3b8' },
                          { id: 'PROVOCATEUR', label: '🔥 AGITATOR', col: '#ef4444' },
                          { id: 'BUZZER', label: '📢 BUZZER', col: '#f59e0b' },
                          { id: 'BOT', label: '🤖 BOT', col: '#38bdf8' },
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
                                padding: '4px 8px',
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
                    <div style={{ textAlign: 'center', padding: '36px 20px', color: '#94a3b8', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '10px', border: '1px dashed #334155' }}>
                      <ShieldCheck size={36} color="#10b981" style={{ margin: '0 auto 8px' }} />
                      <div style={{ fontWeight: 600, color: '#f8fafc' }}>Tidak Ada Akun Mencurigakan yang Cocok dengan Filter</div>
                    </div>
                  ) : (
                    <div style={{ overflowX: 'auto', border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '10px' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                        <thead>
                          <tr style={{ background: 'rgba(30, 41, 59, 0.85)', borderBottom: '1px solid #334155', color: '#94a3b8', textAlign: 'left' }}>
                            <th style={{ padding: '10px 14px' }}>Akun & Tipologi Aktor</th>
                            <th style={{ padding: '10px 14px', textAlign: 'center' }}>Skor Provokasi (🔥)</th>
                            <th style={{ padding: '10px 14px', textAlign: 'center' }}>Skor Bot (🤖)</th>
                            <th style={{ padding: '10px 14px' }}>Indikator Forensik & DISARM</th>
                            <th style={{ padding: '10px 14px', textAlign: 'center' }}>Volume</th>
                            <th style={{ padding: '10px 14px', textAlign: 'center' }}>Risiko</th>
                            <th style={{ padding: '10px 14px', textAlign: 'center' }}>Aksi</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredFlaggedAccounts.map((b) => {
                            const risk = b.cib_risk_level;
                            const riskColor =
                              risk === 'CRITICAL' ? '#ef4444' : risk === 'HIGH' ? '#f59e0b' : risk === 'MEDIUM' ? '#38bdf8' : '#94a3b8';
                            const provScore = b.provocation_score ?? 0;
                            const botScore = b.bot_score ?? (b.inauthenticity_score ?? 0);

                            return (
                              <tr key={b.author_channel_id || b.username} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.4)', background: 'rgba(15, 23, 42, 0.4)' }}>
                                <td style={{ padding: '10px 14px' }}>
                                  <div style={{ fontWeight: 700, color: '#f8fafc' }}>{b.username}</div>
                                  {b.actor_label && (
                                    <span style={{ fontSize: '0.66rem', fontWeight: 700, color: b.actor_type?.startsWith('PROVOCATEUR') ? '#fca5a5' : '#7dd3fc' }}>
                                      {b.actor_label}
                                    </span>
                                  )}
                                </td>
                                <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 800, color: provScore >= 50 ? '#ef4444' : '#cbd5e1' }}>
                                  {provScore}/100
                                </td>
                                <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 800, color: botScore >= 50 ? '#38bdf8' : '#cbd5e1' }}>
                                  {botScore}/100
                                </td>
                                <td style={{ padding: '10px 14px' }}>
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                                    {b.detected_keywords && b.detected_keywords.length > 0 && (
                                      <span style={{ fontSize: '0.66rem', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>
                                        Leksikon: {b.detected_keywords.slice(0, 3).join(', ')}
                                      </span>
                                    )}
                                    {(b.threat_tags || []).slice(0, 4).map((t, idx) => (
                                      <span key={idx} style={{ fontSize: '0.66rem', background: 'rgba(2, 132, 199, 0.15)', color: '#7dd3fc', padding: '2px 6px', borderRadius: '4px' }}>
                                        {t}
                                      </span>
                                    ))}
                                  </div>
                                </td>
                                <td style={{ padding: '10px 14px', textAlign: 'center', color: '#cbd5e1', fontSize: '0.75rem' }}>
                                  <strong>{b.total_comments}</strong> komen ({b.videos_count} video)
                                </td>
                                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                                  <span style={{ color: riskColor, border: `1px solid ${riskColor}`, padding: '2px 8px', borderRadius: '10px', fontSize: '0.68rem', fontWeight: 700 }}>
                                    {risk}
                                  </span>
                                </td>
                                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                                  <button
                                    className="btn btn-secondary"
                                    onClick={() => setSelectedAccount(b)}
                                    style={{ padding: '4px 10px', fontSize: '0.72rem', color: '#38bdf8', borderColor: 'rgba(56, 189, 248, 0.4)' }}
                                  >
                                    <Eye size={12} />
                                    <span>Lihat Dossier ({b.total_comments})</span>
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
              ) : (
                /* SUB-VIEW: JARINGAN BOT MASSAL (KLASTER TEMPLATE KEMBAR) */
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                    <div>
                      <h3 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#f8fafc' }}>
                        Klaster Template Komentar Kembar Lintas Akun ({filteredBotNetworks.length} Klaster)
                      </h3>
                      <p style={{ fontSize: '0.76rem', color: '#94a3b8' }}>
                        Mendeteksi akun-akun berbeda yang memposting kalimat identik/sama persis secara terkoordinasi.
                      </p>
                    </div>
                    <input
                      type="text"
                      placeholder="Cari template atau akun..."
                      value={botnetSearch}
                      onChange={(e) => setBotnetSearch(e.target.value)}
                      style={{ width: '240px', padding: '5px 10px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid rgba(51, 65, 85, 0.6)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.76rem' }}
                    />
                  </div>

                  {filteredBotNetworks.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '36px', color: '#94a3b8', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '10px' }}>
                      Tidak ditemukan klaster komentar kembar lintas akun pada korpus ini.
                    </div>
                  ) : (
                    filteredBotNetworks.map((bn, bIdx) => (
                      <div key={bIdx} style={{ background: 'rgba(15, 23, 42, 0.65)', border: '1px solid rgba(239, 68, 68, 0.35)', borderRadius: '10px', padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '0.72rem', fontWeight: 700, padding: '2px 8px', borderRadius: '6px', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5' }}>
                              {bn.coordination_badge}
                            </span>
                            <span style={{ fontSize: '0.72rem', color: '#38bdf8', fontWeight: 700 }}>
                              👥 {bn.unique_accounts_count} Akun Berbeda • 🔁 {bn.total_occurrences}x Diposting • 🎬 {bn.unique_videos_count} Video
                            </span>
                          </div>
                          <button
                            onClick={() => {
                              const val = bn.template_text.trim();
                              if (val && !customWhitelist.includes(val)) {
                                const nextWl = [...customWhitelist, val];
                                setCustomWhitelist(nextWl);
                                if (runId) {
                                  api.reanalyze_intelligence({ run_id: runId, whitelist: nextWl, threats: customThreats })
                                    .then(() => loadData(runId, true));
                                }
                              }
                            }}
                            style={{ fontSize: '0.7rem', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#6ee7b7', padding: '3px 8px', borderRadius: '5px', cursor: 'pointer', fontWeight: 600 }}
                          >
                            + Whitelist Slogan Wajar
                          </button>
                        </div>

                        <div style={{ background: '#090d16', borderLeft: '4px solid #ef4444', padding: '10px 12px', borderRadius: '0 6px 6px 0', color: '#f8fafc', fontSize: '0.84rem', fontStyle: 'italic' }}>
                          "{renderForensicHighlightedText(bn.template_text, customThreats)}"
                        </div>

                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center', fontSize: '0.74rem' }}>
                          <span style={{ color: '#64748b', fontWeight: 600 }}>Akun Terlibat:</span>
                          {bn.accounts.map((acc, aIdx) => (
                            <span
                              key={aIdx}
                              onClick={() => handleInspectAuthor(acc)}
                              style={{ background: 'rgba(2, 132, 199, 0.15)', color: '#38bdf8', border: '1px solid rgba(2, 132, 199, 0.35)', padding: '2px 7px', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}
                            >
                              {acc}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 2: PETA NARASI & KLASTER ISU (+ MATRIKS MULTI-VIDEO) */}
          {/* ======================================================== */}
          {activeTab === 'topics' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {safeComparisonMatrix.length > 1 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <h3 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#f8fafc' }}>
                      Matriks Komparasi Opini & Ancaman CIB Lintas Video ({safeComparisonMatrix.length} Video Target)
                    </h3>
                    <p style={{ fontSize: '0.76rem', color: '#94a3b8' }}>
                      Perbandingan distribusi sentimen, topik dominan, dan skor CIB pada masing-masing video dalam korpus operasi.
                    </p>
                  </div>
                  <div style={{ overflowX: 'auto', border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '10px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                      <thead>
                        <tr style={{ background: 'rgba(30, 41, 59, 0.85)', borderBottom: '1px solid #334155', color: '#94a3b8', textAlign: 'left' }}>
                          <th style={{ padding: '10px 14px' }}>Video & Kanal</th>
                          <th style={{ padding: '10px 14px', textAlign: 'right' }}>Komentar</th>
                          <th style={{ padding: '10px 14px', textAlign: 'right' }}>Akun Unik</th>
                          <th style={{ padding: '10px 14px', textAlign: 'center' }}>Pos / Net / Neg</th>
                          <th style={{ padding: '10px 14px' }}>Isu Dominan</th>
                          <th style={{ padding: '10px 14px', textAlign: 'center' }}>Skor CIB</th>
                        </tr>
                      </thead>
                      <tbody>
                        {safeComparisonMatrix.map((row) => {
                          const rowCib = Number(row?.cib_score) || 0;
                          return (
                            <tr key={row.video_id} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.4)' }}>
                              <td style={{ padding: '10px 14px' }}>
                                <div style={{ fontWeight: 600, color: '#f8fafc' }}>{row.video_title}</div>
                                <div style={{ fontSize: '0.72rem', color: '#38bdf8' }}>{row.channel_name} ({row.video_id})</div>
                              </td>
                              <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 600, color: '#f8fafc' }}>
                                {(Number(row.total_comments) || 0).toLocaleString()}
                              </td>
                              <td style={{ padding: '10px 14px', textAlign: 'right', color: '#cbd5e1' }}>
                                {(Number(row.unique_commenters) || 0).toLocaleString()}
                              </td>
                              <td style={{ padding: '10px 14px', textAlign: 'center', fontSize: '0.75rem' }}>
                                <span style={{ color: '#10b981', fontWeight: 600 }}>{row.positive_pct}%</span> /{' '}
                                <span style={{ color: '#94a3b8' }}>{row.neutral_pct}%</span> /{' '}
                                <span style={{ color: '#ef4444', fontWeight: 600 }}>{row.negative_pct}%</span>
                              </td>
                              <td style={{ padding: '10px 14px', color: '#cbd5e1', fontSize: '0.76rem' }}>{row.top_topic || '-'}</td>
                              <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 700, color: rowCib >= 0.5 ? '#f87171' : '#34d399' }}>
                                {rowCib.toFixed(2)}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <TopicTable topics={safeTopics} />
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 3: LAPORAN KIRKA SIBER SOSIAL (AI NARRATIVE)         */}
          {/* ======================================================== */}
          {activeTab === 'narrative' && (
            <div className="markdown-container" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', paddingBottom: '14px', borderBottom: '1px solid #1e293b' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <BarChart2 size={20} color="#38bdf8" />
                  </div>
                  <div>
                    <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                      Laporan Perkiraan Intelijen Siber (KIRKA Siber Sosial — PUSSIBERAD)
                    </h2>
                    <span style={{ fontSize: '0.76rem', color: '#94a3b8' }}>
                      Terverifikasi Gate 4 (Anti-Halusinasi Fakta EDA) & Pemetaan Taktik DISARM Framework
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => window.print()}
                    style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem' }}
                  >
                    <Printer size={14} />
                    <span>Cetak / PDF Briefing</span>
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleExportXlsx}
                    disabled={exporting}
                    style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem' }}
                  >
                    <Download size={14} />
                    <span>Ekspor XLSX Lengkap</span>
                  </button>
                </div>
              </div>

              {/* Matriks Ringkasan Taktik DISARM Framework */}
              {detectedDisarmMatrix.length > 0 && (
                <div style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(244, 63, 94, 0.35)', borderRadius: '10px', padding: '12px 16px' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#fda4af', marginBottom: '8px', textTransform: 'uppercase' }}>
                    Matriks Indikator Taktik Operasi Informasi (DISARM / AMITT Standard) Terdeteksi:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {detectedDisarmMatrix.map(([code, cnt]) => (
                      <span
                        key={code}
                        style={{
                          background: 'rgba(225, 29, 72, 0.18)',
                          border: '1px solid rgba(244, 63, 94, 0.45)',
                          color: '#fecdd3',
                          padding: '4px 10px',
                          borderRadius: '6px',
                          fontSize: '0.74rem',
                          fontWeight: 700,
                        }}
                      >
                        {code} ({cnt} Akun)
                      </span>
                    ))}
                  </div>
                </div>
              )}

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
                {result?.narrative_md || 'Belum ada laporan KIRKA yang terkompilasi.'}
              </ReactMarkdown>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 4: EKSPLORASI BUKTI KOMENTAR (FORENSIC CORPUS)       */}
          {/* ======================================================== */}
          {activeTab === 'comments' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                  <h3 style={{ fontSize: '0.96rem', fontWeight: 700, color: '#f8fafc' }}>
                    Eksplorasi Barang Bukti Komentar ({filteredCorpusComments.length} dari {safeCorpusComments.length} Ditampilkan)
                  </h3>
                  <p style={{ fontSize: '0.76rem', color: '#94a3b8', marginTop: '2px' }}>
                    Kata kunci hasutan, separatisme, dan ancaman siber ditandai otomatis dengan sorotan merah. Klik nama akun untuk membuka dossier lengkap.
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <div style={{ position: 'relative', width: '240px' }}>
                    <Search size={14} color="#64748b" style={{ position: 'absolute', left: '10px', top: '8px' }} />
                    <input
                      type="text"
                      placeholder="Cari teks atau domain ancaman..."
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
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          {sent === 'Negatif' ? 'Hasutan / SARA / Delegitimasi' : sent === 'ALL' ? 'Semua' : sent}
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
                        <th style={{ padding: '10px 14px' }}>Teks Bukti Komentar (Auto-Highlight Forensik)</th>
                        <th style={{ padding: '10px 14px', textAlign: 'center' }}>Sentimen</th>
                        <th style={{ padding: '10px 14px' }}>Domain Ancaman & Sub-Isu</th>
                        <th style={{ padding: '10px 14px', textAlign: 'center' }}>Likes</th>
                        <th style={{ padding: '10px 14px', textAlign: 'center' }}>Dossier</th>
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
                        const extraHi = commentSearch.trim().length >= 3 ? [...customThreats, commentSearch.trim()] : customThreats;

                        return (
                          <tr key={c.comment_id || idx} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.3)' }}>
                            <td style={{ padding: '10px 14px', verticalAlign: 'top', width: '175px' }}>
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
                              {renderForensicHighlightedText(c.comment_text, extraHi)}
                            </td>

                            <td style={{ padding: '10px 14px', verticalAlign: 'top', textAlign: 'center', width: '90px' }}>
                              <span style={{ background: sBg, color: sColor, border: `1px solid ${sColor}44`, padding: '2px 8px', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 700 }}>
                                {c.ai_sentiment}
                              </span>
                            </td>

                            <td style={{ padding: '10px 14px', verticalAlign: 'top', width: '190px' }}>
                              <div style={{ color: '#cbd5e1', fontSize: '0.75rem', fontWeight: 600 }}>
                                {c.threat_domain || c.business_category || 'Opini & Respons Publik'}
                              </div>
                              <div style={{ color: '#94a3b8', fontSize: '0.7rem', fontStyle: 'italic' }}>
                                {c.sub_issue || c.topic_name || ''}
                              </div>
                            </td>

                            <td style={{ padding: '10px 14px', verticalAlign: 'top', textAlign: 'center', width: '65px', color: (c.like_count || 0) > 0 ? '#fbbf24' : '#64748b' }}>
                              {(c.like_count || 0).toLocaleString()}
                            </td>

                            <td style={{ padding: '10px 14px', verticalAlign: 'top', textAlign: 'center', width: '95px' }}>
                              <button
                                className="btn btn-secondary"
                                onClick={() => handleInspectAuthor(authorKey)}
                                style={{ padding: '3px 8px', fontSize: '0.7rem' }}
                              >
                                Dossier
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
    </div>
  );
};
