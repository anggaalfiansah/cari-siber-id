import React, { useState } from 'react';
import {
  Play,
  Youtube,
  AlertCircle,
  Search,
  Sparkles,
  CheckCircle2,
  RefreshCw,
  SlidersHorizontal,
  Flame,
  TrendingUp,
  CheckSquare,
  Square,
  Plus,
  Trash2,
  Layers,
  Infinity as InfinityIcon,
} from 'lucide-react';
import { api } from '../api/bridge';
import { CuratedVideoItem, ReusableCorpus } from '../api/types';

interface NewAnalysisPageProps {
  onRunStarted: (runId: string) => void;
  isBusy: boolean;
  initialReuseRunId?: string;
  onClearReuseRunId?: () => void;
}

export const NewAnalysisPage: React.FC<NewAnalysisPageProps> = ({
  onRunStarted,
  isBusy,
  initialReuseRunId,
  onClearReuseRunId,
}) => {
  // Discovery vs Manual vs Reuse tab
  const [activeTab, setActiveTab] = useState<'discovery' | 'manual' | 'reuse'>(
    initialReuseRunId ? 'reuse' : 'discovery'
  );

  // Reuse Scraped Corpus state
  const [reusableCorpora, setReusableCorpora] = useState<ReusableCorpus[]>([]);
  const [selectedCorpus, setSelectedCorpus] = useState<ReusableCorpus | null>(null);
  const [isLoadingCorpora, setIsLoadingCorpora] = useState(false);

  // Discovery mode state
  const [searchKeyword, setSearchKeyword] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [curatedVideos, setCuratedVideos] = useState<CuratedVideoItem[]>([]);
  const [selectedVideos, setSelectedVideos] = useState<CuratedVideoItem[]>([]);
  const [discoveryStats, setDiscoveryStats] = useState<{ totalFound: number; keyword: string } | null>(null);

  // Manual extra URLs added by user
  const [extraUrls, setExtraUrls] = useState<string[]>([]);
  const [newExtraInput, setNewExtraInput] = useState('');

  // Manual mode state (textarea for multi-URL support)
  const [manualUrlsText, setManualUrlsText] = useState('');

  // Common analysis configuration
  // 0 means Unlimited
  const [limit, setLimit] = useState(1000);
  const [sortBy, setSortBy] = useState('top');
  const [includeReplies, setIncludeReplies] = useState(true);
  const [skipScrape, setSkipScrape] = useState(false);

  // Status & error handling
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Sample quick suggestion topics
  const sampleTopics = [
    'Disinformasi Operasi Pengamanan Perbatasan TNI',
    'Isu Propaganda Separatisme Ruang Siber Papua',
    'Operasi Penggiringan Opini Netralitas Militer',
    'Serangan Siber & Phishing Mengatasnamakan Instansi Pertahanan',
  ];

  const loadReusableCorpora = async () => {
    setIsLoadingCorpora(true);
    try {
      const list = await api.list_reusable_corpora();
      if (Array.isArray(list)) {
        setReusableCorpora(list);
        if (initialReuseRunId) {
          const match = list.find((c: ReusableCorpus) => c.run_id === initialReuseRunId);
          if (match) {
            setSelectedCorpus(match);
          } else if (list.length > 0) {
            setSelectedCorpus(list[0]);
          }
        } else if (list.length > 0 && !selectedCorpus) {
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
      setActiveTab('reuse');
      if (reusableCorpora.length > 0) {
        const match = reusableCorpora.find((c) => c.run_id === initialReuseRunId);
        if (match) setSelectedCorpus(match);
      }
    }
  }, [initialReuseRunId, reusableCorpora]);

  const handleSearchCurate = async (keywordToSearch?: string) => {
    const kw = (keywordToSearch || searchKeyword).trim();
    if (!kw) {
      setError('Silakan masukkan kata kunci atau isu yang ingin dicari.');
      return;
    }
    setError('');
    setIsSearching(true);
    setCuratedVideos([]);
    setSelectedVideos([]);

    try {
      // Request hingga 100 curated videos untuk korpus multi-video skala penuh
      const res = await api.search_and_curate_videos({ keyword: kw, max_curated: 100 });
      if (res.success && res.curated_videos) {
        setCuratedVideos(res.curated_videos);
        setDiscoveryStats({
          totalFound: res.total_candidates_found || res.curated_videos.length,
          keyword: kw,
        });
        // Auto-select top 5 video pertama secara default
        const topSlice = res.curated_videos.slice(0, Math.min(5, res.curated_videos.length));
        setSelectedVideos(topSlice);
      } else {
        setError(res.error || 'Tidak ditemukan video yang relevan untuk isu ini.');
      }
    } catch (err: any) {
      setError(err?.message || 'Gagal melakukan pencarian dan kurasi video.');
    } finally {
      setIsSearching(false);
    }
  };

  const toggleSelectVideo = (video: CuratedVideoItem) => {
    const exists = selectedVideos.some((v) => v.video_id === video.video_id);
    if (exists) {
      setSelectedVideos(selectedVideos.filter((v) => v.video_id !== video.video_id));
    } else {
      setSelectedVideos([...selectedVideos, video]);
    }
  };

  const selectTopN = (n: number) => {
    const top = curatedVideos.slice(0, Math.min(n, curatedVideos.length));
    setSelectedVideos(top);
  };

  const selectAll = () => {
    setSelectedVideos([...curatedVideos]);
  };

  const deselectAll = () => {
    setSelectedVideos([]);
  };

  const handleAddExtraUrl = () => {
    const trimmed = newExtraInput.trim();
    if (trimmed && !extraUrls.includes(trimmed)) {
      setExtraUrls([...extraUrls, trimmed]);
      setNewExtraInput('');
    }
  };

  const handleRemoveExtraUrl = (urlToRemove: string) => {
    setExtraUrls(extraUrls.filter((u) => u !== urlToRemove));
  };

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();

    if (activeTab === 'reuse') {
      if (!selectedCorpus) {
        setError('Silakan pilih salah satu korpus scraping yang tersedia di daftar.');
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
          setError(res.error || 'Gagal memulai analisis dari korpus.');
        }
      } catch (err: any) {
        setError(err?.message || 'Terjadi kesalahan sistem saat memulai pipeline.');
      } finally {
        setLoading(false);
      }
      return;
    }

    let targetUrls: string[] = [];

    if (activeTab === 'discovery') {
      const curatedUrls = selectedVideos
        .map((v: any) => v.url || v.video_url || (v.video_id ? `https://www.youtube.com/watch?v=${v.video_id}` : ''))
        .filter((u: string) => Boolean(u && u.trim()));
      targetUrls = [...curatedUrls, ...extraUrls];
    } else {
      // Manual mode: split lines or commas
      targetUrls = manualUrlsText
        .split('\n')
        .map((l) => l.trim())
        .filter((l) => l.length > 0 && (l.startsWith('http') || l.includes('youtube') || l.includes('youtu.be')));
    }

    if (targetUrls.length === 0) {
      setError('Silakan pilih minimal 1 video terkurasi atau masukkan URL video target.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const res = await api.start_run({
        video_url: targetUrls[0],
        video_urls: targetUrls,
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
      setError(err?.message || 'Terjadi kesalahan sistem saat memulai pipeline.');
    } finally {
      setLoading(false);
    }
  };

  const totalDiscoverySelected = selectedVideos.length + extraUrls.length;

  return (
    <div style={{ maxWidth: '920px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Page Header */}
      <div>
        <h1 style={{ fontSize: '1.45rem', fontWeight: '700', color: '#f8fafc', letterSpacing: '-0.02em' }}>
          Mulai Analisis Ruang Siber Baru
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#94a3b8', marginTop: '4px' }}>
          Platform intelijen isu: kurasi multi-video (5, 10, s.d. unlimited), deteksi narasi manipulasi bot/buzzer terkoordinasi (CIB), audit irisan komentator, dan pemetaan polarisasi opini.
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Mode Switcher Tabs */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '10px',
          background: 'rgba(15, 23, 42, 0.6)',
          padding: '6px',
          borderRadius: '12px',
          border: '1px solid rgba(51, 65, 85, 0.5)',
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab('discovery')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '12px 14px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            background: activeTab === 'discovery' ? '#0284c7' : 'transparent',
            color: activeTab === 'discovery' ? '#ffffff' : '#94a3b8',
            fontWeight: 600,
            fontSize: '0.86rem',
          }}
        >
          <Sparkles size={17} color={activeTab === 'discovery' ? '#ffffff' : '#38bdf8'} />
          <span>Kurasi Isu AI (Otomatis)</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('manual')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '12px 14px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            background: activeTab === 'manual' ? '#0284c7' : 'transparent',
            color: activeTab === 'manual' ? '#ffffff' : '#94a3b8',
            fontWeight: 600,
            fontSize: '0.86rem',
          }}
        >
          <Youtube size={17} color={activeTab === 'manual' ? '#ffffff' : '#f43f5e'} />
          <span>Input URL Manual (Multi-Video)</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setActiveTab('reuse');
            loadReusableCorpora();
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '12px 14px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            background: activeTab === 'reuse' ? '#0284c7' : 'transparent',
            color: activeTab === 'reuse' ? '#ffffff' : '#94a3b8',
            fontWeight: 600,
            fontSize: '0.86rem',
            position: 'relative',
          }}
        >
          <Layers size={17} color={activeTab === 'reuse' ? '#ffffff' : '#10b981'} />
          <span>[SIMULASI MILITER] Data Tersimpan</span>
          {reusableCorpora.length > 0 && (
            <span
              style={{
                background: activeTab === 'reuse' ? 'rgba(255, 255, 255, 0.25)' : 'rgba(16, 185, 129, 0.2)',
                color: activeTab === 'reuse' ? '#ffffff' : '#10b981',
                fontSize: '0.72rem',
                padding: '1px 6px',
                borderRadius: '999px',
                fontWeight: 700,
              }}
            >
              {reusableCorpora.length}
            </span>
          )}
        </button>
      </div>

      {/* DISCOVERY MODE SECTION */}
      {activeTab === 'discovery' && (
        <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div>
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Search size={16} color="#38bdf8" />
              <span>Kata Kunci Isu / Kebijakan Publik / Topik Diskusi</span>
            </label>
            <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Contoh: kebijakan hilirisasi nikel, revisi uu pilkada, kenaikan ppn 12%..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSearchCurate();
                  }
                }}
                disabled={isSearching || isBusy}
                autoFocus
              />
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => handleSearchCurate()}
                disabled={isSearching || isBusy || !searchKeyword.trim()}
                style={{ padding: '0 20px', whiteSpace: 'nowrap' }}
              >
                {isSearching ? (
                  <>
                    <RefreshCw size={16} className="spin" />
                    <span>Mengkurasikan...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    <span>Cari & Kurasi (AI)</span>
                  </>
                )}
              </button>
            </div>

            {/* Quick Topic Chips */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <TrendingUp size={12} /> Contoh Isu:
              </span>
              {sampleTopics.map((topic) => (
                <button
                  key={topic}
                  type="button"
                  onClick={() => {
                    setSearchKeyword(topic);
                    handleSearchCurate(topic);
                  }}
                  disabled={isSearching || isBusy}
                  style={{
                    background: 'rgba(30, 41, 59, 0.7)',
                    border: '1px solid rgba(51, 65, 85, 0.6)',
                    color: '#94a3b8',
                    padding: '3px 10px',
                    borderRadius: '12px',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#0284c7';
                    e.currentTarget.style.color = '#38bdf8';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(51, 65, 85, 0.6)';
                    e.currentTarget.style.color = '#94a3b8';
                  }}
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>

          {/* Searching Spinner State */}
          {isSearching && (
            <div
              style={{
                padding: '24px',
                textAlign: 'center',
                background: 'rgba(2, 132, 199, 0.05)',
                border: '1px dashed rgba(2, 132, 199, 0.3)',
                borderRadius: '8px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <RefreshCw size={24} color="#38bdf8" className="spin" />
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#f8fafc' }}>
                Menelusuri YouTube & Melakukan Kurasi Relevansi AI (Multi-Video Corpus)
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', maxWidth: '520px' }}>
                Engine sedang memindai kandidat video, memfilter konten musik/sensasional, dan menyusun peringkat video dengan potensi diskursus opini publik tertinggi...
              </div>
            </div>
          )}

          {/* Curated Results List */}
          {curatedVideos.length > 0 && !isSearching && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '6px' }}>
              {/* Toolbar & Quick Selection Buttons */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'rgba(30, 41, 59, 0.5)',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: '1px solid rgba(51, 65, 85, 0.5)',
                  flexWrap: 'wrap',
                  gap: '10px',
                }}
              >
                <div style={{ fontSize: '0.85rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Layers size={16} color="#38bdf8" />
                  <span>
                    Ditemukan <strong style={{ color: '#38bdf8' }}>{discoveryStats?.totalFound}</strong> kandidat •{' '}
                    <strong style={{ color: '#10b981' }}>{curatedVideos.length} Video Terkurasi</strong>:
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => selectTopN(5)}
                    style={{
                      background: selectedVideos.length === 5 ? '#0284c7' : 'rgba(2, 132, 199, 0.15)',
                      border: '1px solid #0284c7',
                      color: selectedVideos.length === 5 ? '#ffffff' : '#38bdf8',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    ⚡ Top 5
                  </button>

                  <button
                    type="button"
                    onClick={() => selectTopN(10)}
                    style={{
                      background: selectedVideos.length === 10 ? '#10b981' : 'rgba(16, 185, 129, 0.15)',
                      border: '1px solid #10b981',
                      color: selectedVideos.length === 10 ? '#ffffff' : '#10b981',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    🎯 Top 10
                  </button>

                  <button
                    type="button"
                    onClick={() => selectTopN(25)}
                    style={{
                      background: selectedVideos.length === 25 ? '#8b5cf6' : 'rgba(139, 92, 246, 0.15)',
                      border: '1px solid #8b5cf6',
                      color: selectedVideos.length === 25 ? '#ffffff' : '#a78bfa',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    🔥 Top 25
                  </button>

                  <button
                    type="button"
                    onClick={() => selectTopN(50)}
                    style={{
                      background: selectedVideos.length === 50 ? '#f59e0b' : 'rgba(245, 158, 11, 0.15)',
                      border: '1px solid #f59e0b',
                      color: selectedVideos.length === 50 ? '#ffffff' : '#fbbf24',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    ⚡ Top 50
                  </button>

                  <button
                    type="button"
                    onClick={selectAll}
                    style={{
                      background: selectedVideos.length === curatedVideos.length ? '#0284c7' : 'rgba(148, 163, 184, 0.15)',
                      border: '1px solid #0284c7',
                      color: selectedVideos.length === curatedVideos.length ? '#ffffff' : '#38bdf8',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    💯 Pilih Semua ({curatedVideos.length} Video)
                  </button>

                  {selectedVideos.length > 0 && (
                    <button
                      type="button"
                      onClick={deselectAll}
                      style={{
                        background: 'transparent',
                        border: '1px solid rgba(239, 68, 68, 0.4)',
                        color: '#f87171',
                        padding: '5px 12px',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      Batal Pilih
                    </button>
                  )}
                </div>
              </div>

              {/* Responsive Modern 2-Column Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(370px, 1fr))',
                gap: '12px',
              }}>
                {curatedVideos.map((item, idx) => {
                  const isSelected = selectedVideos.some((v) => v.video_id === item.video_id);
                  const score = item.relevance_score ?? 80;
                  const scoreColor = score >= 90 ? '#10b981' : score >= 75 ? '#38bdf8' : '#fbbf24';

                  return (
                    <div
                      key={item.video_id}
                      onClick={() => toggleSelectVideo(item)}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        background: isSelected ? 'rgba(2, 132, 199, 0.12)' : 'rgba(15, 23, 42, 0.65)',
                        border: isSelected ? '2px solid #0284c7' : '1px solid rgba(51, 65, 85, 0.6)',
                        boxShadow: isSelected ? '0 0 14px rgba(2, 132, 199, 0.25)' : 'none',
                        borderRadius: '10px',
                        padding: '12px',
                        cursor: 'pointer',
                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                        position: 'relative',
                        justifyContent: 'space-between',
                      }}
                    >
                      {/* Top Badges & Selector */}
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                              {isSelected ? (
                                <CheckSquare size={19} color="#0284c7" />
                              ) : (
                                <Square size={19} color="#475569" />
                              )}
                            </div>
                            <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 700 }}>
                              #{idx + 1}
                            </span>
                            {item.is_recommended && (
                              <span
                                style={{
                                  background: 'rgba(16, 185, 129, 0.18)',
                                  border: '1px solid rgba(16, 185, 129, 0.5)',
                                  color: '#34d399',
                                  fontSize: '0.65rem',
                                  fontWeight: 700,
                                  padding: '2px 6px',
                                  borderRadius: '6px',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '3px',
                                }}
                              >
                                <Flame size={11} /> PRIORITAS
                              </span>
                            )}
                          </div>

                          <span
                            style={{
                              background: 'rgba(30, 41, 59, 0.9)',
                              border: `1px solid ${scoreColor}`,
                              color: scoreColor,
                              fontSize: '0.68rem',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: '12px',
                            }}
                          >
                            Relevansi {score}%
                          </span>
                        </div>

                        {/* Thumbnail & Video Header */}
                        <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                          <div
                            style={{
                              position: 'relative',
                              width: '120px',
                              height: '68px',
                              flexShrink: 0,
                              borderRadius: '6px',
                              overflow: 'hidden',
                              background: '#0f172a',
                            }}
                          >
                            {item.thumbnail ? (
                              <img
                                src={item.thumbnail}
                                alt={item.title}
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                              />
                            ) : (
                              <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <Youtube size={26} color="#64748b" />
                              </div>
                            )}
                            {item.duration && (
                              <span
                                style={{
                                  position: 'absolute',
                                  bottom: '3px',
                                  right: '3px',
                                  background: 'rgba(0,0,0,0.85)',
                                  color: '#ffffff',
                                  fontSize: '0.62rem',
                                  fontWeight: 600,
                                  padding: '1px 4px',
                                  borderRadius: '3px',
                                }}
                              >
                                {item.duration}
                              </span>
                            )}
                          </div>

                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div
                              style={{
                                fontWeight: 600,
                                fontSize: '0.84rem',
                                color: '#f8fafc',
                                lineHeight: 1.3,
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                              }}
                              title={item.title}
                            >
                              {item.title}
                            </div>
                            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>
                              <strong style={{ color: '#cbd5e1' }}>{item.channel}</strong>
                              {item.views && ` • ${item.views}`}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Curation Reason */}
                      {item.curation_reason && (
                        <div
                          style={{
                            fontSize: '0.72rem',
                            color: '#7dd3fc',
                            background: 'rgba(2, 132, 199, 0.08)',
                            borderLeft: '2px solid #0284c7',
                            padding: '4px 8px',
                            borderRadius: '0 4px 4px 0',
                            marginTop: '8px',
                            lineHeight: 1.35,
                          }}
                        >
                          💡 <em>{item.curation_reason}</em>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Extra URLs addition (Unlimited user expansion) */}
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.4)',
                  border: '1px dashed rgba(51, 65, 85, 0.6)',
                  borderRadius: '8px',
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Plus size={14} color="#38bdf8" />
                  <span>Tambah URL Video Tambahan (Opsional / Unlimited)</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={newExtraInput}
                    onChange={(e) => setNewExtraInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddExtraUrl();
                      }
                    }}
                    style={{ fontSize: '0.82rem', padding: '6px 12px' }}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleAddExtraUrl}
                    style={{ fontSize: '0.8rem', padding: '6px 14px', whiteSpace: 'nowrap' }}
                  >
                    Tambah
                  </button>
                </div>

                {extraUrls.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                    {extraUrls.map((url) => (
                      <div
                        key={url}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          background: 'rgba(30, 41, 59, 0.6)',
                          padding: '4px 10px',
                          borderRadius: '4px',
                          fontSize: '0.78rem',
                          color: '#38bdf8',
                        }}
                      >
                        <span className="mono-font">{url}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveExtraUrl(url)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#f87171' }}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* MANUAL MODE SECTION */}
      {activeTab === 'manual' && (
        <div className="panel panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Daftar URL Video YouTube Target (1 URL per baris) *</label>
            <textarea
              className="form-input"
              rows={5}
              placeholder={`https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...`}
              value={manualUrlsText}
              onChange={(e) => setManualUrlsText(e.target.value)}
              disabled={isBusy || loading}
              style={{ resize: 'vertical', fontFamily: 'monospace', fontSize: '0.85rem' }}
              autoFocus
            />
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
              Masukkan 1 URL atau banyak URL video sekaligus (minimal 5, ideal 10, hingga tidak terbatas).
            </div>
          </div>
        </div>
      )}

      {/* REUSE SCRAPED CORPUS SECTION */}
      {activeTab === 'reuse' && (
        <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Prominent Fail-Safe Demo Scenario Banner for Jury Presentation */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.2) 0%, rgba(15, 23, 42, 0.75) 100%)',
              border: '1px solid rgba(56, 189, 248, 0.45)',
              borderRadius: '10px',
              padding: '16px 18px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '14px',
            }}
          >
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '8px',
                background: 'rgba(2, 132, 199, 0.25)',
                border: '1px solid rgba(56, 189, 248, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38bdf8',
                flexShrink: 0,
              }}
            >
              <Layers size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <span
                  style={{
                    background: 'rgba(2, 132, 199, 0.3)',
                    color: '#38bdf8',
                    border: '1px solid #0284c7',
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    padding: '2px 8px',
                    borderRadius: '6px',
                    letterSpacing: '0.5px',
                  }}
                >
                  FAIL-SAFE DEMO
                </span>
                <span style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.98rem' }}>
                  [MODE SKENARIO SIMULASI MILITER] Audit Korpus Operasi CIB 3.500 Komentar
                </span>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginTop: '6px', lineHeight: 1.5 }}>
                Mode peragaan tanpa ketergantungan koneksi internet: Eksekusi instan seluruh pipeline deep learning (IndoBERT + BERTopic), 4 Agentic AI Hardened Gates, dan pemetaan jaringan bot/buzzer CIB secara deterministik dalam hitungan detik.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} color="#10b981" />
                <span>Pilih Dataset Komentar yang Pernah Di-Scrap</span>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginTop: '3px' }}>
                Gunakan hasil scraping sebelumnya tanpa perlu mengunduh ulang ribuan komentar dari YouTube.
              </p>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={loadReusableCorpora}
              disabled={isLoadingCorpora || isBusy}
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            >
              <RefreshCw size={13} className={isLoadingCorpora ? 'spin' : ''} />
              <span>Segarkan Daftar</span>
            </button>
          </div>

          {isLoadingCorpora ? (
            <div style={{ textAlign: 'center', padding: '30px', color: '#94a3b8', fontSize: '0.85rem' }}>
              <RefreshCw size={20} className="spin" style={{ margin: '0 auto 8px', color: '#38bdf8' }} />
              <div>Memindai riwayat berkas scraping komentar...</div>
            </div>
          ) : reusableCorpora.length === 0 ? (
            <div
              style={{
                background: 'rgba(51, 65, 85, 0.25)',
                border: '1px dashed rgba(100, 116, 139, 0.3)',
                borderRadius: '8px',
                padding: '24px',
                textAlign: 'center',
                color: '#94a3b8',
                fontSize: '0.85rem',
              }}
            >
              <AlertCircle size={24} color="#94a3b8" style={{ margin: '0 auto 8px' }} />
              <div>Belum ada korpus komentar yang tersimpan di disk.</div>
              <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px' }}>
                Jalankan scraping baru terlebih dahulu lewat tab Kurasi Isu atau Input Manual.
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '360px', overflowY: 'auto' }}>
              {reusableCorpora.map((corpus) => {
                const isSelected = selectedCorpus?.run_id === corpus.run_id;
                return (
                  <div
                    key={corpus.run_id}
                    onClick={() => setSelectedCorpus(corpus)}
                    style={{
                      border: isSelected ? '1px solid #0284c7' : '1px solid rgba(51, 65, 85, 0.6)',
                      background: isSelected ? 'rgba(2, 132, 199, 0.12)' : 'rgba(15, 23, 42, 0.5)',
                      borderRadius: '10px',
                      padding: '14px 16px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '14px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                      <div
                        style={{
                          width: '20px',
                          height: '20px',
                          borderRadius: '50%',
                          border: isSelected ? '5px solid #38bdf8' : '2px solid #64748b',
                          background: '#0b0f19',
                          flexShrink: 0,
                        }}
                      />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.88rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {corpus.title}
                        </div>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '4px', flexWrap: 'wrap' }}>
                          <span style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: '#94a3b8', background: 'rgba(51, 65, 85, 0.4)', padding: '1px 6px', borderRadius: '4px' }}>
                            Run ID: {corpus.run_id}
                          </span>
                          <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                            {corpus.created_at}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexShrink: 0 }}>
                      <span
                        style={{
                          background: 'rgba(16, 185, 129, 0.15)',
                          color: '#34d399',
                          border: '1px solid rgba(16, 185, 129, 0.3)',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: '6px',
                        }}
                      >
                        {corpus.comment_count.toLocaleString()} Komentar
                      </span>
                      <span
                        style={{
                          background: 'rgba(56, 189, 248, 0.15)',
                          color: '#38bdf8',
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          padding: '3px 8px',
                          borderRadius: '6px',
                        }}
                      >
                        {corpus.video_count} Video
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {selectedCorpus && (
            <div
              style={{
                background: 'rgba(2, 132, 199, 0.1)',
                border: '1px solid rgba(2, 132, 199, 0.3)',
                borderRadius: '8px',
                padding: '12px 14px',
                fontSize: '0.82rem',
                color: '#7dd3fc',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <Sparkles size={16} color="#38bdf8" />
              <span>
                Korpus terpilih: <strong>{selectedCorpus.comment_count.toLocaleString()} komentar</strong> dari <strong>{selectedCorpus.video_count} video</strong> (Run: <code>{selectedCorpus.run_id}</code>). Tahap 1 (Scraping) akan dilewati dan pipeline langsung mengeksekusi Topic Modeling!
              </span>
            </div>
          )}
        </div>
      )}

      {/* SELECTED TARGET CONFIRMATION BANNER */}
      {totalDiscoverySelected > 0 && activeTab === 'discovery' && (
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: '10px',
            padding: '14px 18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '8px',
                background: 'rgba(16, 185, 129, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#10b981',
                flexShrink: 0,
              }}
            >
              <CheckCircle2 size={24} />
            </div>
            <div>
              <div style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 700 }}>
                KORPUS TERPILIH UNTUK AUDIT SIBER KOLEKTIF:
              </div>
              <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc', marginTop: '2px' }}>
                {totalDiscoverySelected} Video YouTube ({selectedVideos.length} Terkurasi + {extraUrls.length} Manual)
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                Kanal:{' '}
                {Array.from(new Set(selectedVideos.map((v) => v.channel))).slice(0, 4).join(', ')}
                {selectedVideos.length > 4 ? ` (+${selectedVideos.length - 4} kanal lainnya)` : ''}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CONFIGURATION & EXECUTION FORM */}
      <form
        onSubmit={handleStartAnalysis}
        className="panel panel-body"
        style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
          <SlidersHorizontal size={16} color="#38bdf8" />
          <span style={{ fontWeight: 600, fontSize: '0.9rem', color: '#f8fafc' }}>
            Parameter Pengambilan Komentar & Hardened Gates
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>Batas Komentar per Video</span>
              {limit === 0 && (
                <span
                  style={{
                    background: 'rgba(16, 185, 129, 0.2)',
                    color: '#10b981',
                    fontSize: '0.68rem',
                    padding: '1px 6px',
                    borderRadius: '8px',
                    fontWeight: 700,
                  }}
                >
                  UNLIMITED
                </span>
              )}
            </label>
            <select
              className="form-select"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              disabled={isBusy || loading}
            >
              <option value={100}>100 Komentar (Uji Cepat / Rapid Test)</option>
              <option value={500}>500 Komentar (Standar)</option>
              <option value={1000}>1.000 Komentar (Rekomendasi Riset)</option>
              <option value={2500}>2.500 Komentar (Komprehensif)</option>
              <option value={5000}>5.000 Komentar (Skala Luas)</option>
              <option value={10000}>10.000 Komentar (Dataset Besar)</option>
              <option value={0}>♾️ Unlimited (Seluruh Komentar Sampai Habis)</option>
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Urutan Pengambilan Komentar</label>
            <select
              className="form-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              disabled={isBusy || loading}
            >
              <option value="top">Top (Terpopuler & Interaksi Tertinggi)</option>
              <option value="new">New (Kronologis Komentar Terbaru)</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '24px', paddingTop: '4px', flexWrap: 'wrap' }}>
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              color: '#cbd5e1',
            }}
          >
            <input
              type="checkbox"
              checked={includeReplies}
              onChange={(e) => setIncludeReplies(e.target.checked)}
              disabled={isBusy || loading}
            />
            Sertakan Balasan Komentar (Replies Thread)
          </label>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              color: '#cbd5e1',
            }}
          >
            <input
              type="checkbox"
              checked={skipScrape}
              onChange={(e) => setSkipScrape(e.target.checked)}
              disabled={isBusy || loading}
            />
            Gunakan Cache Scrape Lokal (Skip Scrape)
          </label>
        </div>

        {/* Action Button */}
        <div
          style={{
            borderTop: '1px solid rgba(51, 65, 85, 0.4)',
            paddingTop: '16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
            {activeTab === 'reuse'
              ? selectedCorpus
                ? `Korpus siap: ${selectedCorpus.comment_count.toLocaleString()} komentar (${selectedCorpus.video_count} video) dari Run ${selectedCorpus.run_id}.`
                : 'Pilih korpus komentar di atas untuk melanjutkan analisis tanpa scraping.'
              : activeTab === 'discovery'
              ? totalDiscoverySelected > 0
                ? `${totalDiscoverySelected} video siap dianalisis secara kolektif.`
                : 'Pilih minimal 1 video (disarankan 5–10 video) di atas.'
              : manualUrlsText.trim()
              ? 'Daftar video siap dianalisis.'
              : 'Masukkan daftar URL video target di atas.'}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={
              isBusy ||
              loading ||
              (activeTab === 'reuse'
                ? !selectedCorpus
                : activeTab === 'discovery'
                ? totalDiscoverySelected === 0
                : !manualUrlsText.trim())
            }
            style={{ padding: '10px 24px', fontSize: '0.95rem' }}
          >
            <Play size={18} />
            <span>
              {isBusy
                ? 'Operasi Lain Sedang Berjalan'
                : loading
                ? 'Mempersiapkan Pipeline...'
                : activeTab === 'reuse'
                ? `Jalankan Analisis Korpus (${selectedCorpus?.comment_count.toLocaleString() || ''} Komentar)`
                : activeTab === 'discovery' && totalDiscoverySelected > 1
                ? `Jalankan Analisis Kolektif (${totalDiscoverySelected} Video)`
                : 'Jalankan Analisis Kognitif'}
            </span>
          </button>
        </div>
      </form>
    </div>
  );
};
