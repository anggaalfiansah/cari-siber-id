import React, { useState, useRef } from 'react';
import {
  Play,
  Youtube,
  AlertCircle,
  Search,
  Sparkles,
  CheckCircle2,
  RefreshCw,
  CheckSquare,
  Square,
  Shield,
  Database,
  Upload,
  FileSpreadsheet,
  Crosshair,
  Radar,
  ShieldAlert,
  Lock,
  Info,
} from 'lucide-react';
import { api } from '../api/bridge';
import { CuratedVideoItem, ReusableCorpus } from '../api/types';

interface NewAnalysisPageProps {
  onRunStarted: (runId: string) => void;
  isBusy: boolean;
  initialReuseRunId?: string;
  onClearReuseRunId?: () => void;
}

type MissionProfileId = 'tactical' | 'operational' | 'strategic';

export const NewAnalysisPage: React.FC<NewAnalysisPageProps> = ({
  onRunStarted,
  isBusy,
  initialReuseRunId,
  onClearReuseRunId,
}) => {
  // Mode sumber target: 'unified' (Omnibox Keyword/URL) vs 'offline' (Korpus Lokal / Simulasi Militer)
  const [sourceMode, setSourceMode] = useState<'unified' | 'offline'>(
    initialReuseRunId ? 'offline' : 'unified'
  );

  // Unified Omnibox input (bisa berisi kata kunci isu ATAU daftar URL YouTube per baris)
  const [unifiedInput, setUnifiedInput] = useState('');
  const [targetVideoCount, setTargetVideoCount] = useState<number>(20);
  const [videoSortMode, setVideoSortMode] = useState<'relevance' | 'comments' | 'views'>('relevance');
  const [isSearching, setIsSearching] = useState(false);
  const [curatedVideos, setCuratedVideos] = useState<CuratedVideoItem[]>([]);
  const [selectedVideos, setSelectedVideos] = useState<CuratedVideoItem[]>([]);
  const [discoveryStats, setDiscoveryStats] = useState<{ totalFound: number; totalComments: number; keyword: string } | null>(null);

  // Offline / Reusable Corpus state
  const [reusableCorpora, setReusableCorpora] = useState<ReusableCorpus[]>([]);
  const [selectedCorpus, setSelectedCorpus] = useState<ReusableCorpus | null>(null);
  const [isLoadingCorpora, setIsLoadingCorpora] = useState(false);
  const [isImportingFile, setIsImportingFile] = useState(false);
  const [importFeedback, setImportFeedback] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Mission Profile Selector ('tactical' = 300, 'operational' = 1000, 'strategic' = 0/Unlimited)
  const [missionProfile, setMissionProfile] = useState<MissionProfileId>('operational');
  const [limit, setLimit] = useState(1000);
  const [sortBy, setSortBy] = useState('top');
  const [includeReplies, setIncludeReplies] = useState(true);

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const sampleTopics = [
    'Disinformasi Operasi Pengamanan Perbatasan',
    'Isu Propaganda Separatisme Ruang Siber',
    'Operasi Penggiringan Opini Publik & Polarisasi',
    'Serangan Siber & Phishing Infrastruktur Publik',
  ];

  // Auto-detect apakah isi omnibox adalah daftar URL atau kata kunci topik
  const extractedUrls = React.useMemo(() => {
    return unifiedInput
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0 && (s.startsWith('http://') || s.startsWith('https://') || s.includes('youtube.com/') || s.includes('youtu.be/')));
  }, [unifiedInput]);

  const isUrlDetected = extractedUrls.length > 0;

  const loadReusableCorpora = async (preferRunId?: string) => {
    setIsLoadingCorpora(true);
    try {
      const list = await api.list_reusable_corpora();
      if (Array.isArray(list)) {
        setReusableCorpora(list);
        const targetId = preferRunId || initialReuseRunId;
        if (targetId) {
          const match = list.find((c: ReusableCorpus) => c.run_id === targetId);
          if (match) {
            setSelectedCorpus(match);
            return;
          }
        }
        if (list.length > 0 && !selectedCorpus) {
          setSelectedCorpus(list[0]);
        }
      }
    } catch (e) {
      console.error('Failed to load reusable corpora:', e);
    } finally {
      setIsLoadingCorpora(false);
    }
  };

  React.useEffect(() => {
    loadReusableCorpora();
  }, []);

  React.useEffect(() => {
    if (initialReuseRunId) {
      setSourceMode('offline');
      if (reusableCorpora.length > 0) {
        const match = reusableCorpora.find((c) => c.run_id === initialReuseRunId);
        if (match) setSelectedCorpus(match);
      }
    }
  }, [initialReuseRunId, reusableCorpora]);

  const handleSelectMissionProfile = (profile: MissionProfileId) => {
    setMissionProfile(profile);
    if (profile === 'tactical') {
      setLimit(300);
      setSortBy('top');
      setIncludeReplies(false);
    } else if (profile === 'operational') {
      setLimit(1000);
      setSortBy('top');
      setIncludeReplies(true);
    } else {
      setLimit(0);
      setSortBy('newest');
      setIncludeReplies(true);
    }
  };

  const handleSearchCurate = async (keywordOverride?: string, countOverride?: number) => {
    const kw = (keywordOverride ?? unifiedInput).trim();
    if (!kw) {
      setError('Masukkan kata kunci isu ancaman atau tempelkan URL video target.');
      return;
    }
    const maxTarget = Math.max(1, Math.min(100, countOverride ?? targetVideoCount ?? 20));
    setError('');
    setIsSearching(true);
    setCuratedVideos([]);
    setSelectedVideos([]);

    try {
      const res = await api.search_and_curate_videos({ keyword: kw, max_curated: maxTarget });
      if (res.success && res.curated_videos) {
        setCuratedVideos(res.curated_videos);
        const totalComm = res.total_estimated_comments ?? res.curated_videos.reduce((acc, v) => acc + (v.comment_count || 0), 0);
        setDiscoveryStats({
          totalFound: res.total_candidates_found || res.curated_videos.length,
          totalComments: totalComm,
          keyword: kw,
        });
        const topSlice = res.curated_videos.slice(0, Math.min(maxTarget, res.curated_videos.length));
        setSelectedVideos(topSlice);
      } else {
        setError(res.error || 'Tidak ditemukan video yang relevan untuk kata kunci ini.');
      }
    } catch (err: any) {
      setError(err?.message || 'Gagal melakukan pencarian dan kurasi video.');
    } finally {
      setIsSearching(false);
    }
  };

  const sortedCuratedVideos = React.useMemo(() => {
    const copy = [...curatedVideos];
    if (videoSortMode === 'comments') {
      copy.sort((a, b) => (b.comment_count || 0) - (a.comment_count || 0));
    } else if (videoSortMode === 'views') {
      copy.sort((a, b) => (b.views_count || 0) - (a.views_count || 0));
    } else {
      copy.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
    }
    return copy;
  }, [curatedVideos, videoSortMode]);

  const selectedTotalComments = React.useMemo(() => {
    return selectedVideos.reduce((acc, v) => acc + (v.comment_count || 0), 0);
  }, [selectedVideos]);

  const toggleSelectVideo = (video: CuratedVideoItem) => {
    const exists = selectedVideos.some((v) => v.video_id === video.video_id);
    if (exists) {
      setSelectedVideos(selectedVideos.filter((v) => v.video_id !== video.video_id));
    } else {
      setSelectedVideos([...selectedVideos, video]);
    }
  };

  const handleImportExternalFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    setImportFeedback('');
    setIsImportingFile(true);

    try {
      const arrayBuffer = await file.arrayBuffer();
      const bytes = new Uint8Array(arrayBuffer);
      let binary = '';
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      const b64 = window.btoa(binary);

      const res = await api.import_external_corpus({
        filename: file.name,
        content_base64: b64,
        title: `Impor Forensik: ${file.name}`,
      });

      if (res.success && res.run_id) {
        setImportFeedback(
          res.message || `Berhasil mengimpor ${res.comment_count} bukti komentar. SHA-256: ${(res.sha256_hash || '').slice(0, 16)}...`
        );
        await loadReusableCorpora(res.run_id);
      } else {
        setError(res.error || 'Gagal mengimpor berkas bukti digital.');
      }
    } catch (err: any) {
      setError(err?.message || 'Gagal membaca berkas lokal.');
    } finally {
      setIsImportingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();

    if (sourceMode === 'offline') {
      if (!selectedCorpus) {
        setError('Silakan pilih salah satu dataset simulasi militer atau korpus bukti lokal.');
        return;
      }
      setError('');
      setLoading(true);
      try {
        const res = await api.start_run({
          source_run_id: selectedCorpus.run_id,
          limit_comments: limit,
          sort_by: sortBy,
          include_replies: includeReplies,
          skip_scrape: true,
        });
        if (res.success && res.run_id) {
          onClearReuseRunId?.();
          onRunStarted(res.run_id);
        } else {
          setError(res.error || 'Gagal memulai operasi analisis korpus lokal.');
        }
      } catch (err: any) {
        setError(err?.message || 'Terjadi kesalahan saat memulai pipeline.');
      } finally {
        setLoading(false);
      }
      return;
    }

    // Mode Unified: Jika user menempelkan URL langsung, gunakan extractedUrls. Jika tidak, gunakan selectedVideos hasil kurasi.
    let targetUrls: string[] = [];
    if (isUrlDetected) {
      targetUrls = extractedUrls;
    } else {
      targetUrls = selectedVideos
        .map((v: any) => v.url || v.video_url || (v.video_id ? `https://www.youtube.com/watch?v=${v.video_id}` : ''))
        .filter((u: string) => Boolean(u && u.trim()));
    }

    if (targetUrls.length === 0) {
      setError(
        'Tempelkan URL video YouTube target, atau ketik isu dan tekan "Kurasi Target AI" lalu centang minimal 1 video.'
      );
      return;
    }

    setError('');
    setLoading(true);

    try {
      const activeSearchKeyword = isUrlDetected
        ? ''
        : (discoveryStats?.keyword || unifiedInput.trim());
      const res = await api.start_run({
        video_url: targetUrls[0],
        video_urls: targetUrls,
        search_keyword: activeSearchKeyword,
        limit_comments: limit,
        sort_by: sortBy,
        include_replies: includeReplies,
        skip_scrape: false,
      });

      if (res.success && res.run_id) {
        onRunStarted(res.run_id);
      } else {
        setError(res.error || 'Gagal memulai operasi analisis.');
      }
    } catch (err: any) {
      setError(err?.message || 'Terjadi kesalahan sistem saat memulai pipeline.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '940px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em', margin: 0 }}>
            1. Inisialisasi Operasi Intelijen Kognitif
          </h1>
          <span
            title="Akuisisi target ruang siber terpadu: deteksi otomatis Kata Kunci vs Multi-URL, atau ingesti bukti digital offline bersegel SHA-256."
            style={{ color: '#64748b', cursor: 'help', display: 'inline-flex', alignItems: 'center' }}
          >
            <Info size={16} />
          </span>
        </div>

        <div
          title="Pipeline Otomatis: IndoBERT Topic Modeling → 4 Agentic Verification Gates → Dual-Engine CIB → Segel SHA-256"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '5px 11px',
            borderRadius: '8px',
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            color: '#34d399',
            fontSize: '0.73rem',
            fontWeight: 700,
            cursor: 'help',
          }}
        >
          <Lock size={13} />
          <span>4 AGENTIC GATES & SHA-256 SEAL READY</span>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          color: '#f87171',
          padding: '12px 16px',
          borderRadius: '8px',
          fontSize: '0.84rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* ===================================================================== */}
      {/* LANGKAH 1: PILIH SUMBER TARGET (OMNIBOX ONLINE VS KORPUS OFFLINE)     */}
      {/* ===================================================================== */}
      <div className="panel panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Crosshair size={17} color="#38bdf8" />
            <span>LANGKAH 1: Sumber Akuisisi Target</span>
          </div>

          {/* 2-Way Clean Switcher */}
          <div style={{
            display: 'inline-flex',
            background: '#090d16',
            padding: '4px',
            borderRadius: '8px',
            border: '1px solid rgba(51, 65, 85, 0.6)',
            gap: '4px',
          }}>
            <button
              type="button"
              onClick={() => setSourceMode('unified')}
              title="Deteksi otomatis Kata Kunci Isu (Pencarian & Kurasi AI) atau Daftar URL YouTube"
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: sourceMode === 'unified' ? '#0284c7' : 'transparent',
                color: sourceMode === 'unified' ? '#ffffff' : '#94a3b8',
              }}
            >
              <Sparkles size={14} />
              <span>Kotak Komando (Isu AI / Multi-URL)</span>
            </button>

            <button
              type="button"
              onClick={() => setSourceMode('offline')}
              title="Gunakan Dataset Simulasi bawaan atau impor file log komentar (.CSV / .JSON / .XLSX) secara offline"
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: sourceMode === 'offline' ? '#10b981' : 'transparent',
                color: sourceMode === 'offline' ? '#052e16' : '#94a3b8',
              }}
            >
              <Database size={14} />
              <span>Bukti Offline & Simulasi ({reusableCorpora.length})</span>
            </button>
          </div>
        </div>

        {sourceMode === 'unified' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Unified Omnibox Textarea */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label className="form-label" style={{ margin: 0, display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <span>Kata Kunci Isu Ancaman atau Daftar URL YouTube</span>
                  <span
                    title="Ketik kata kunci topik untuk mencari & mengkurasi video otomatis dengan AI, atau tempelkan satu/beberapa URL YouTube (1 URL per baris)."
                    style={{ color: '#64748b', cursor: 'help', display: 'inline-flex', alignItems: 'center' }}
                  >
                    <Info size={13} />
                  </span>
                </label>
                <span
                  title="Sistem mendeteksi secara otomatis apakah input berupa Kata Kunci Pencarian atau Tautan URL YouTube"
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '10px',
                    background: isUrlDetected ? 'rgba(244, 63, 94, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                    color: isUrlDetected ? '#fb7185' : '#38bdf8',
                    border: `1px solid ${isUrlDetected ? 'rgba(244, 63, 94, 0.35)' : 'rgba(56, 189, 248, 0.35)'}`,
                    cursor: 'help',
                  }}
                >
                  {isUrlDetected
                    ? `${extractedUrls.length} URL Target Langsung`
                    : 'Mode Pencarian & Kurasi AI'}
                </span>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'stretch' }}>
                <textarea
                  className="form-input"
                  rows={isUrlDetected ? 3 : 2}
                  value={unifiedInput}
                  onChange={(e) => setUnifiedInput(e.target.value)}
                  placeholder="Ketik isu (misal: 'Disinformasi Operasi Pengamanan Perbatasan') atau tempel URL YouTube..."
                  style={{ flex: 1, resize: 'vertical', fontFamily: isUrlDetected ? 'JetBrains Mono, monospace' : 'inherit', fontSize: '0.85rem' }}
                />
                {!isUrlDetected && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', minWidth: '175px' }}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        background: 'rgba(15, 23, 42, 0.85)',
                        border: '1px solid rgba(56, 189, 248, 0.35)',
                        borderRadius: '7px',
                        padding: '4px 8px',
                        gap: '6px',
                      }}
                      title="Jumlah target video yang ingin dicari dan dikurasi (1 - 100 video)"
                    >
                      <span style={{ fontSize: '0.71rem', color: '#94a3b8', fontWeight: 700, whiteSpace: 'nowrap' }}>
                        Target Video:
                      </span>
                      <input
                        type="number"
                        min={1}
                        max={100}
                        value={targetVideoCount}
                        onChange={(e) => {
                          const v = parseInt(e.target.value, 10);
                          setTargetVideoCount(Number.isNaN(v) ? 1 : Math.max(1, Math.min(100, v)));
                        }}
                        style={{
                          width: '54px',
                          background: '#090d16',
                          border: '1px solid rgba(71, 85, 105, 0.6)',
                          borderRadius: '5px',
                          color: '#38bdf8',
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          textAlign: 'center',
                          padding: '2px 4px',
                        }}
                      />
                    </div>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => handleSearchCurate()}
                      disabled={isSearching || isBusy}
                      style={{ flex: 1, padding: '8px 16px', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', fontWeight: 700 }}
                    >
                      {isSearching ? (
                        <>
                          <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} />
                          <span>Mengkurasi ({targetVideoCount})...</span>
                        </>
                      ) : (
                        <>
                          <Search size={16} />
                          <span>Kurasi {targetVideoCount} Target AI</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Sample Topic Chips */}
            {!isUrlDetected && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>Contoh Isu:</span>
                {sampleTopics.map((topic) => (
                  <button
                    key={topic}
                    type="button"
                    onClick={() => {
                      setUnifiedInput(topic);
                      handleSearchCurate(topic, targetVideoCount);
                    }}
                    title={`Klik untuk langsung mengkurasi ${targetVideoCount} video terkait "${topic}"`}
                    style={{
                      background: 'rgba(30, 41, 59, 0.65)',
                      border: '1px solid rgba(71, 85, 105, 0.45)',
                      color: '#cbd5e1',
                      borderRadius: '6px',
                      padding: '3px 9px',
                      fontSize: '0.72rem',
                      cursor: 'pointer',
                    }}
                  >
                    {topic}
                  </button>
                ))}
              </div>
            )}

            {/* Curated Video Selection Grid */}
            {!isUrlDetected && curatedVideos.length > 0 && (
              <div style={{
                background: 'rgba(9, 13, 22, 0.65)',
                border: '1px solid rgba(51, 65, 85, 0.6)',
                borderRadius: '10px',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span>Hasil Kurasi AI ({selectedVideos.length} dari {curatedVideos.length} video dipilih)</span>
                      <span style={{
                        fontSize: '0.73rem',
                        padding: '2px 8px',
                        borderRadius: '6px',
                        background: 'rgba(245, 158, 11, 0.16)',
                        border: '1px solid rgba(245, 158, 11, 0.4)',
                        color: '#fbbf24',
                        fontWeight: 700,
                      }}>
                        💬 Total Komentar Target Terpilih: {selectedTotalComments.toLocaleString('id-ID')} komentar
                      </span>
                    </div>
                    {discoveryStats && (
                      <div style={{ fontSize: '0.71rem', color: '#94a3b8' }}>
                        Ditemukan {discoveryStats.totalFound} kandidat • Total populasi komentar dari {curatedVideos.length} video terkurasi: {(discoveryStats.totalComments || 0).toLocaleString('id-ID')} komentar
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                    <div style={{ display: 'inline-flex', background: '#090d16', padding: '2px', borderRadius: '6px', border: '1px solid rgba(51, 65, 85, 0.6)', marginRight: '4px' }}>
                      {([
                        { id: 'relevance', label: 'Relevansi' },
                        { id: 'comments', label: '💬 Komentar Terbanyak' },
                        { id: 'views', label: 'Views' },
                      ] as const).map((sm) => (
                        <button
                          key={sm.id}
                          type="button"
                          onClick={() => setVideoSortMode(sm.id)}
                          style={{
                            padding: '3px 7px',
                            fontSize: '0.69rem',
                            borderRadius: '4px',
                            border: 'none',
                            background: videoSortMode === sm.id ? '#0284c7' : 'transparent',
                            color: videoSortMode === sm.id ? '#fff' : '#94a3b8',
                            cursor: 'pointer',
                            fontWeight: 600,
                          }}
                        >
                          {sm.label}
                        </button>
                      ))}
                    </div>
                    {[5, 10, 20].map((n) => (
                      <button
                        key={n}
                        type="button"
                        onClick={() => setSelectedVideos(sortedCuratedVideos.slice(0, Math.min(n, sortedCuratedVideos.length)))}
                        style={{
                          padding: '3px 9px',
                          fontSize: '0.72rem',
                          borderRadius: '5px',
                          border: '1px solid rgba(56, 189, 248, 0.4)',
                          background: selectedVideos.length === n ? 'rgba(2, 132, 199, 0.25)' : 'transparent',
                          color: '#38bdf8',
                          cursor: 'pointer',
                          fontWeight: 600,
                        }}
                      >
                        Top {n}
                      </button>
                    ))}
                    <button
                      type="button"
                      onClick={() => setSelectedVideos([...sortedCuratedVideos])}
                      style={{
                        padding: '3px 9px',
                        fontSize: '0.72rem',
                        borderRadius: '5px',
                        border: '1px solid rgba(148, 163, 184, 0.3)',
                        background: 'transparent',
                        color: '#cbd5e1',
                        cursor: 'pointer',
                      }}
                    >
                      Pilih Semua ({curatedVideos.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedVideos([])}
                      style={{
                        padding: '3px 9px',
                        fontSize: '0.72rem',
                        borderRadius: '5px',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        background: 'transparent',
                        color: '#f87171',
                        cursor: 'pointer',
                      }}
                    >
                      Reset
                    </button>
                  </div>
                </div>

                <div style={{ maxHeight: '280px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {sortedCuratedVideos.map((v, idx) => {
                    const isSel = selectedVideos.some((s) => s.video_id === v.video_id);
                    const commLabel =
                      v.comments_str ||
                      (typeof v.comment_count === 'number'
                        ? `${v.comment_count.toLocaleString('id-ID')} komentar`
                        : 'Komentar aktif');
                    return (
                      <div
                        key={v.video_id}
                        onClick={() => toggleSelectVideo(v)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: '10px',
                          padding: '8px 12px',
                          borderRadius: '8px',
                          background: isSel ? 'rgba(2, 132, 199, 0.14)' : 'rgba(15, 23, 42, 0.6)',
                          border: isSel ? '1px solid #0284c7' : '1px solid rgba(51, 65, 85, 0.4)',
                          cursor: 'pointer',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                          {isSel ? <CheckSquare size={16} color="#38bdf8" /> : <Square size={16} color="#64748b" />}
                          <div style={{ minWidth: 0 }}>
                            <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f8fafc', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              <span style={{ color: '#64748b', marginRight: '6px', fontSize: '0.74rem' }}>#{idx + 1}</span>
                              {v.title}
                            </div>
                            <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                              {v.channel} • {v.views || '-'} • <span style={{ color: '#fbbf24', fontWeight: 600 }}>💬 {commLabel}</span> • {v.published || '-'}
                            </div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                          <span style={{
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: '10px',
                            background: 'rgba(245, 158, 11, 0.14)',
                            border: '1px solid rgba(245, 158, 11, 0.35)',
                            color: '#fbbf24',
                          }}>
                            💬 {commLabel}
                          </span>
                          {v.relevance_score && (
                            <span style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              padding: '2px 7px',
                              borderRadius: '10px',
                              background: 'rgba(16, 185, 129, 0.15)',
                              color: '#34d399',
                            }}>
                              Skor {v.relevance_score}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* MODE OFFLINE: DATASET SIMULASI MILITER & IMPOR BERKAS EKSTERNAL (.CSV / .JSON / .XLSX) */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Top Bar: Upload External File */}
            <div style={{
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '10px',
              padding: '10px 14px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}>
              <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <FileSpreadsheet size={16} />
                <span>Ingesti Bukti Digital Multi-Platform (Mode Offline / Air-Gapped)</span>
                <span
                  title="Impor log komentar dari YouTube, X/Twitter, TikTok, atau Telegram (.CSV, .JSON, .XLSX) atau pilih Dataset Simulasi di bawah."
                  style={{ color: '#64748b', cursor: 'help', display: 'inline-flex', alignItems: 'center' }}
                >
                  <Info size={14} />
                </span>
              </div>

              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.json,.xlsx,.xls"
                  onChange={handleImportExternalFile}
                  style={{ display: 'none' }}
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isImportingFile}
                  style={{
                    borderColor: '#10b981',
                    color: '#34d399',
                    fontSize: '0.76rem',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <Upload size={14} />
                  <span>{isImportingFile ? 'Mengimpor...' : 'Impor File .CSV / .JSON / .XLSX'}</span>
                </button>
              </div>
            </div>

            {importFeedback && (
              <div style={{
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(16, 185, 129, 0.35)',
                color: '#34d399',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                <CheckCircle2 size={16} />
                <span>{importFeedback}</span>
              </div>
            )}

            {/* List of Preloaded Military Simulations & Saved Corpora */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '290px', overflowY: 'auto' }}>
              {isLoadingCorpora ? (
                <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8', fontSize: '0.84rem' }}>
                  Memuat daftar korpus bukti digital...
                </div>
              ) : reusableCorpora.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '0.84rem' }}>
                  Belum ada korpus lokal. Klik tombol Impor File di atas.
                </div>
              ) : (
                reusableCorpora.map((corp) => {
                  const isSelected = selectedCorpus?.run_id === corp.run_id;
                  return (
                    <div
                      key={corp.run_id}
                      onClick={() => setSelectedCorpus(corp)}
                      style={{
                        padding: '10px 14px',
                        borderRadius: '8px',
                        background: isSelected ? 'rgba(16, 185, 129, 0.14)' : 'rgba(15, 23, 42, 0.65)',
                        border: isSelected ? '2px solid #10b981' : '1px solid rgba(51, 65, 85, 0.5)',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '12px',
                      }}
                    >
                      <div style={{ minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          {corp.is_demo && (
                            <span style={{
                              background: 'rgba(245, 158, 11, 0.2)',
                              border: '1px solid rgba(245, 158, 11, 0.5)',
                              color: '#fbbf24',
                              fontSize: '0.66rem',
                              fontWeight: 800,
                              padding: '2px 7px',
                              borderRadius: '6px',
                            }}>
                              DATASET SIMULASI BAWAAN
                            </span>
                          )}
                          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc' }}>
                            {corp.title}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.73rem', color: '#94a3b8', marginTop: '3px', display: 'flex', gap: '12px', flexWrap: 'wrap', fontFamily: 'monospace' }}>
                          <span>{corp.comment_count.toLocaleString()} Komentar</span>
                          <span>• {corp.video_count} Sumber/Video</span>
                          <span>• {corp.size_mb} MB</span>
                          {corp.sha256_hash && (
                            <span style={{ color: '#34d399' }} title={`SHA-256: ${corp.sha256_hash}`}>
                              • SHA-256: {corp.sha256_hash.slice(0, 12)}...
                            </span>
                          )}
                        </div>
                      </div>

                      <div style={{ flexShrink: 0 }}>
                        {isSelected ? (
                          <span style={{
                            background: '#10b981',
                            color: '#052e16',
                            fontSize: '0.72rem',
                            fontWeight: 800,
                            padding: '4px 10px',
                            borderRadius: '6px',
                          }}>
                            TERPILIH
                          </span>
                        ) : (
                          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Pilih</span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>

      {/* ===================================================================== */}
      {/* LANGKAH 2: PRESET KEDALAMAN OPERASI (MISSION PROFILE SELECTOR)        */}
      {/* ===================================================================== */}
      <form onSubmit={handleStartAnalysis} className="panel panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Radar size={17} color="#f59e0b" />
            <span>LANGKAH 2: Profil Kedalaman Operasi</span>
            <span
              title="Pilih kedalaman akuisisi komentar: Patroli Cepat (300 komentar terpopuler), Audit Standar (1.000 komentar + balasan), atau Investigasi Forensik Penuh (seluruh komentar)."
              style={{ color: '#64748b', cursor: 'help', display: 'inline-flex', alignItems: 'center' }}
            >
              <Info size={14} />
            </span>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || isBusy}
            title="Jalankan Pipeline: IndoBERT Topic Modeling → 4 Agentic Verification Gates → Dual-Engine CIB → Segel SHA-256"
            style={{
              padding: '9px 22px',
              fontSize: '0.86rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: sourceMode === 'offline' ? 'linear-gradient(135deg, #059669, #10b981)' : undefined,
            }}
          >
            <Play size={16} />
            <span>
              {loading
                ? 'Menginisialisasi Operasi...'
                : sourceMode === 'offline'
                  ? 'Eksekusi Analisis Bukti Digital (Offline)'
                  : 'Luncurkan Operasi Analisis Ruang Siber'}
            </span>
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          {/* Profile 1: Patroli Cepat */}
          <div
            onClick={() => handleSelectMissionProfile('tactical')}
            title="Deteksi dini cepat pada komentar terpopuler (Top Comments) tanpa sub-balasan untuk penilaian situasi kilat."
            style={{
              padding: '10px 14px',
              borderRadius: '9px',
              background: missionProfile === 'tactical' ? 'rgba(56, 189, 248, 0.14)' : 'rgba(15, 23, 42, 0.65)',
              border: missionProfile === 'tactical' ? '2px solid #38bdf8' : '1px solid rgba(51, 65, 85, 0.5)',
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <span>1. Patroli Cepat</span>
              <Info size={13} color="#64748b" />
            </span>
            <span style={{ fontSize: '0.7rem', fontFamily: 'monospace', color: '#94a3b8', background: 'rgba(15, 23, 42, 0.8)', padding: '2px 7px', borderRadius: '5px' }}>
              300 Komentar
            </span>
          </div>

          {/* Profile 2: Audit Standar */}
          <div
            onClick={() => handleSelectMissionProfile('operational')}
            title="Standar operasional: mencakup sub-thread balasan untuk memetakan rasio Agitator vs Bot (CIB) & laporan KIRKA."
            style={{
              padding: '10px 14px',
              borderRadius: '9px',
              background: missionProfile === 'operational' ? 'rgba(16, 185, 129, 0.14)' : 'rgba(15, 23, 42, 0.65)',
              border: missionProfile === 'operational' ? '2px solid #10b981' : '1px solid rgba(51, 65, 85, 0.5)',
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#34d399', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <span>2. Audit Standar</span>
              <Info size={13} color="#64748b" />
            </span>
            <span style={{ fontSize: '0.7rem', fontFamily: 'monospace', color: '#34d399', fontWeight: 700, background: 'rgba(16, 185, 129, 0.12)', padding: '2px 7px', borderRadius: '5px' }}>
              1.000 + Balasan
            </span>
          </div>

          {/* Profile 3: Investigasi Forensik Penuh */}
          <div
            onClick={() => handleSelectMissionProfile('strategic')}
            title="Akuisisi komprehensif seluruh komentar & urutan kronologis terbaru untuk pembuktian forensik mendalam."
            style={{
              padding: '10px 14px',
              borderRadius: '9px',
              background: missionProfile === 'strategic' ? 'rgba(245, 158, 11, 0.14)' : 'rgba(15, 23, 42, 0.65)',
              border: missionProfile === 'strategic' ? '2px solid #f59e0b' : '1px solid rgba(51, 65, 85, 0.5)',
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fbbf24', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <span>3. Investigasi Forensik</span>
              <Info size={13} color="#64748b" />
            </span>
            <span style={{ fontSize: '0.7rem', fontFamily: 'monospace', color: '#fbbf24', fontWeight: 700, background: 'rgba(245, 158, 11, 0.12)', padding: '2px 7px', borderRadius: '5px' }}>
              UNLIMITED
            </span>
          </div>
        </div>
      </form>
    </div>
  );
};
