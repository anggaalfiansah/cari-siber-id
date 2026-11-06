import React, { useState, useEffect } from 'react';
import {
  X,
  ExternalLink,
  Search,
  ThumbsUp,
  MessageCircle,
  Pin,
  Heart,
  CornerDownRight,
  ShieldAlert,
  Calendar,
  Video,
  Copy,
  Check,
  Filter,
} from 'lucide-react';
import { FlaggedAccountItem, AuthorCommentItem } from '../api/types';
import { api } from '../api/bridge';

interface AccountCommentsModalProps {
  account: FlaggedAccountItem | null;
  runId?: string | null;
  onClose: () => void;
}

const renderHighlightedText = (text: string, keywords?: string[]) => {
  if (!keywords || keywords.length === 0 || !text) return text;
  const pattern = new RegExp(`(${keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
  const parts = text.split(pattern);
  return parts.map((part, i) => {
    const isHit = keywords.some(k => k.toLowerCase() === part.toLowerCase());
    if (isHit) {
      return (
        <mark
          key={i}
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

export const AccountCommentsModal: React.FC<AccountCommentsModalProps> = ({
  account,
  runId,
  onClose,
}) => {
  const [comments, setComments] = useState<AuthorCommentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sentimentFilter, setSentimentFilter] = useState<'ALL' | 'Positif' | 'Netral' | 'Negatif'>('ALL');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (!account) return;

    if (account.all_comments && account.all_comments.length > 0) {
      setComments(account.all_comments);
    } else if (runId) {
      setLoading(true);
      api.get_author_comments({
        run_id: runId,
        author_key: account.author_channel_id || account.username,
      })
        .then((res: any) => {
          if (res?.success && Array.isArray(res.comments)) {
            setComments(res.comments);
          }
        })
        .catch((err: any) => console.error('Gagal mengambil komentar akun:', err))
        .finally(() => setLoading(false));
    }
  }, [account, runId]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!account) return null;

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredComments = comments.filter((c) => {
    if (sentimentFilter !== 'ALL' && c.ai_sentiment !== sentimentFilter) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchText = (c.comment_text || '').toLowerCase().includes(q);
      const matchTopic = (c.topic_name || '').toLowerCase().includes(q);
      const matchIssue = (c.sub_issue || '').toLowerCase().includes(q);
      const matchVideo = (c.video_title || '').toLowerCase().includes(q);
      return matchText || matchTopic || matchIssue || matchVideo;
    }
    return true;
  });

  const risk = account.cib_risk_level;
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

  const posCount = account.sentiment_breakdown?.Positif ?? comments.filter((c) => c.ai_sentiment === 'Positif').length;
  const netCount = account.sentiment_breakdown?.Netral ?? comments.filter((c) => c.ai_sentiment === 'Netral').length;
  const negCount = account.sentiment_breakdown?.Negatif ?? comments.filter((c) => c.ai_sentiment === 'Negatif').length;
  const totalLikes = account.total_likes_received ?? comments.reduce((acc, c) => acc + (c.like_count || 0), 0);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(5, 8, 16, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '920px',
          maxHeight: '90vh',
          background: '#0d1322',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          borderRadius: '14px',
          boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.8), 0 0 30px rgba(2, 132, 199, 0.15)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Modal */}
        <div
          style={{
            padding: '20px 24px',
            background: 'linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
            borderBottom: '1px solid rgba(51, 65, 85, 0.6)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #0284c7 0%, #1e1b4b 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.25rem',
                fontWeight: 700,
                color: '#f8fafc',
                border: '2px solid rgba(56, 189, 248, 0.4)',
                boxShadow: '0 4px 12px rgba(2, 132, 199, 0.3)',
              }}
            >
              {account.username.charAt(0).toUpperCase() || 'U'}
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                  {account.username}
                </h2>
                {account.actor_label && (
                  <span
                    style={{
                      background: account.actor_type?.startsWith('PROVOCATEUR')
                        ? 'rgba(239, 68, 68, 0.2)'
                        : account.actor_type === 'HYBRID_THREAT'
                        ? 'rgba(168, 85, 247, 0.2)'
                        : 'rgba(2, 132, 199, 0.2)',
                      color: account.actor_type?.startsWith('PROVOCATEUR')
                        ? '#fca5a5'
                        : account.actor_type === 'HYBRID_THREAT'
                        ? '#c084fc'
                        : '#38bdf8',
                      border: `1px solid ${
                        account.actor_type?.startsWith('PROVOCATEUR')
                          ? '#ef4444'
                          : account.actor_type === 'HYBRID_THREAT'
                          ? '#a855f7'
                          : '#0284c7'
                      }`,
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '12px',
                    }}
                  >
                    {account.actor_label}
                  </span>
                )}
                <span
                  style={{
                    background: riskBg,
                    color: riskColor,
                    border: `1px solid ${riskColor}`,
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '12px',
                    letterSpacing: '0.5px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <ShieldAlert size={11} />
                  <span>RISIKO {risk}</span>
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px', flexWrap: 'wrap' }}>
                {account.author_channel_url ? (
                  <a
                    href={account.author_channel_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      fontSize: '0.75rem',
                      color: '#38bdf8',
                      textDecoration: 'none',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontWeight: 500,
                    }}
                  >
                    <span>Buka Kanal YouTube</span>
                    <ExternalLink size={12} />
                  </a>
                ) : (
                  <span className="mono-font" style={{ fontSize: '0.72rem', color: '#64748b' }}>
                    ID: {account.author_channel_id}
                  </span>
                )}

                {account.threat_tags && account.threat_tags.length > 0 && (
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {account.threat_tags.map((rawTag, idx) => {
                      const tag = rawTag.includes('<0 dtk') ? rawTag.replace('<0 dtk', 'Posting Cepat') : rawTag;
                      const isDisarm = tag.startsWith('DISARM');
                      const isBotnet = tag.toLowerCase().includes('bot massal');
                      const isBurst = tag.toLowerCase().includes('burst');
                      const isCopypasta = tag.toLowerCase().includes('copypasta');
                      return (
                        <span
                          key={idx}
                          style={{
                            fontSize: '0.68rem',
                            background: isDisarm
                              ? 'rgba(225, 29, 72, 0.22)'
                              : isBotnet
                              ? 'rgba(239, 68, 68, 0.2)'
                              : isBurst
                              ? 'rgba(245, 158, 11, 0.2)'
                              : isCopypasta
                              ? 'rgba(168, 85, 247, 0.2)'
                              : 'rgba(2, 132, 199, 0.15)',
                            color: isDisarm
                              ? '#fda4af'
                              : isBotnet
                              ? '#fca5a5'
                              : isBurst
                              ? '#fcd34d'
                              : isCopypasta
                              ? '#d8b4fe'
                              : '#7dd3fc',
                            padding: '1px 7px',
                            borderRadius: '4px',
                            border: `1px solid ${
                              isDisarm
                                ? '#f43f5e'
                                : isBotnet
                                ? 'rgba(239, 68, 68, 0.4)'
                                : isBurst
                                ? 'rgba(245, 158, 11, 0.4)'
                                : isCopypasta
                                ? 'rgba(168, 85, 247, 0.4)'
                                : 'rgba(2, 132, 199, 0.3)'
                            }`,
                            fontWeight: isDisarm || isBotnet || isBurst ? 700 : 500,
                            letterSpacing: isDisarm ? '0.2px' : 'normal',
                          }}
                        >
                          {tag}
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'rgba(51, 65, 85, 0.4)',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.15s ease',
            }}
            title="Tutup (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        {/* Quick Stats Dossier Strip (Dual-Engine: Provokasi vs Bot) */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '10px',
            padding: '12px 24px',
            background: 'rgba(15, 23, 42, 0.6)',
            borderBottom: '1px solid rgba(51, 65, 85, 0.4)',
          }}
        >
          <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(51, 65, 85, 0.3)' }}>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 600 }}>TOTAL KOMENTAR</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
              {comments.length || account.total_comments}
            </div>
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(51, 65, 85, 0.3)' }}>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 600 }}>VIDEO DIMASUKI</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
              {account.videos_count || 1} Video
            </div>
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(51, 65, 85, 0.3)' }}>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 600 }}>TOTAL LIKES DITERIMA</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fbbf24', marginTop: '2px' }}>
              {totalLikes.toLocaleString()}
            </div>
          </div>

          {/* Engine 2: Skor Provokasi */}
          <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.35)' }}>
            <div style={{ fontSize: '0.7rem', color: '#f87171', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span>🔥 SKOR PROVOKASI</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '2px' }}>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f87171' }}>
                {account.provocation_score ?? 0}
              </span>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>/ 100</span>
            </div>
            {account.score_breakdown && (
              <div style={{ fontSize: '0.62rem', color: '#fca5a5', marginTop: '2px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                <span>Hasut: {account.score_breakdown.prov_lexicon ?? 0}</span>
                <span>• Utas: {account.score_breakdown.prov_thread ?? 0}</span>
                <span>• Like: {account.score_breakdown.prov_resonance ?? 0}</span>
              </div>
            )}
          </div>

          {/* Engine 1: Skor Bot */}
          <div style={{ background: 'rgba(2, 132, 199, 0.08)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(2, 132, 199, 0.35)' }}>
            <div style={{ fontSize: '0.7rem', color: '#38bdf8', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span>🤖 SKOR BOT</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '2px' }}>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#38bdf8' }}>
                {account.bot_score ?? 0}
              </span>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>/ 100</span>
            </div>
            {account.score_breakdown && (
              <div style={{ fontSize: '0.62rem', color: '#7dd3fc', marginTop: '2px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                <span>Copy: {account.score_breakdown.copypasta ?? 0}</span>
                <span>• Vid: {account.score_breakdown.cross_video ?? 0}</span>
                <span>• Spd: {account.score_breakdown.temporal ?? 0}</span>
              </div>
            )}
          </div>
        </div>

        {/* Filter and Search Bar */}
        <div
          style={{
            padding: '12px 24px',
            background: 'rgba(15, 23, 42, 0.3)',
            borderBottom: '1px solid rgba(51, 65, 85, 0.3)',
            display: 'flex',
            gap: '12px',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
          }}
        >
          {/* Search Box */}
          <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
            <Search size={14} color="#64748b" style={{ position: 'absolute', left: '10px', top: '9px' }} />
            <input
              type="text"
              placeholder="Cari teks komentar, topik, atau judul video..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '6px 10px 6px 32px',
                background: 'rgba(30, 41, 59, 0.6)',
                border: '1px solid rgba(51, 65, 85, 0.6)',
                borderRadius: '6px',
                color: '#f8fafc',
                fontSize: '0.8rem',
                outline: 'none',
              }}
            />
          </div>

          {/* Sentiment Filter Pills */}
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Filter size={12} />
              <span>Filter:</span>
            </span>
            {(['ALL', 'Positif', 'Netral', 'Negatif'] as const).map((sent) => {
              const active = sentimentFilter === sent;
              const color =
                sent === 'Positif' ? '#10b981' : sent === 'Negatif' ? '#ef4444' : sent === 'Netral' ? '#94a3b8' : '#38bdf8';
              return (
                <button
                  key={sent}
                  onClick={() => setSentimentFilter(sent)}
                  style={{
                    background: active ? `${color}22` : 'transparent',
                    border: `1px solid ${active ? color : 'rgba(51, 65, 85, 0.5)'}`,
                    color: active ? color : '#94a3b8',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {sent === 'Negatif' ? 'Hasutan / SARA / Delegitimasi' : sent === 'ALL' ? 'Semua Sentimen' : sent}
                </button>
              );
            })}
          </div>
        </div>

        {/* Comments Scrollable Body */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '18px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8', fontSize: '0.85rem' }}>
              Memuat seluruh arsip komentar akun...
            </div>
          ) : filteredComments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b', fontSize: '0.85rem' }}>
              Tidak ada komentar yang cocok dengan filter pencarian.
            </div>
          ) : (
            filteredComments.map((c, index) => {
              const sentColor =
                c.ai_sentiment === 'Positif' ? '#10b981' : c.ai_sentiment === 'Negatif' ? '#ef4444' : '#94a3b8';
              const sentBg =
                c.ai_sentiment === 'Positif'
                  ? 'rgba(16, 185, 129, 0.12)'
                  : c.ai_sentiment === 'Negatif'
                  ? 'rgba(239, 68, 68, 0.12)'
                  : 'rgba(148, 163, 184, 0.12)';

              return (
                <div
                  key={c.comment_id || index}
                  style={{
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(51, 65, 85, 0.5)',
                    borderRadius: '10px',
                    padding: '14px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {/* Top Meta Row */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span
                        style={{
                          background: sentBg,
                          color: sentColor,
                          border: `1px solid ${sentColor}44`,
                          padding: '2px 8px',
                          borderRadius: '6px',
                          fontSize: '0.7rem',
                          fontWeight: 700,
                        }}
                      >
                        {c.ai_sentiment}
                      </span>

                      {c.business_category && (
                        <span
                          style={{
                            background: 'rgba(30, 41, 59, 0.7)',
                            color: '#cbd5e1',
                            padding: '2px 8px',
                            borderRadius: '6px',
                            fontSize: '0.7rem',
                          }}
                        >
                          {c.business_category}
                        </span>
                      )}

                      {c.sub_issue && (
                        <span style={{ fontSize: '0.7rem', color: '#38bdf8', fontStyle: 'italic' }}>
                          • {c.sub_issue}
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.72rem', color: '#64748b' }}>
                      {c.created_at && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Calendar size={11} />
                          <span>{c.created_at}</span>
                        </span>
                      )}

                      <button
                        onClick={() => handleCopy(c.comment_id || String(index), c.comment_text)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: copiedId === (c.comment_id || String(index)) ? '#10b981' : '#64748b',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '3px',
                          fontSize: '0.7rem',
                        }}
                        title="Salin teks komentar"
                      >
                        {copiedId === (c.comment_id || String(index)) ? <Check size={12} /> : <Copy size={12} />}
                        <span>{copiedId === (c.comment_id || String(index)) ? 'Tersalin' : 'Salin'}</span>
                      </button>
                    </div>
                  </div>

                  {/* Video Title (if multi-video) */}
                  {c.video_title && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.72rem', color: '#94a3b8' }}>
                      <Video size={11} color="#0284c7" />
                      <span style={{ fontWeight: 600, color: '#e2e8f0' }}>Video:</span>
                      <span style={{ color: '#cbd5e1' }}>{c.video_title}</span>
                      {c.video_id && <span className="mono-font" style={{ color: '#0284c7' }}>({c.video_id})</span>}
                    </div>
                  )}

                  {/* Comment Text */}
                  <div
                    style={{
                      fontSize: '0.85rem',
                      color: '#f1f5f9',
                      lineHeight: 1.55,
                      whiteSpace: 'pre-wrap',
                      background: 'rgba(30, 41, 59, 0.35)',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      borderLeft: `3px solid ${sentColor}`,
                    }}
                  >
                    "{renderHighlightedText(c.comment_text, account.detected_keywords)}"
                  </div>

                  {/* Bottom Stats & Indicators */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.72rem', color: '#94a3b8' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: c.like_count > 0 ? '#fbbf24' : '#94a3b8' }}>
                      <ThumbsUp size={12} />
                      <span>{c.like_count.toLocaleString()} Suka</span>
                    </span>

                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MessageCircle size={12} />
                      <span>{c.reply_count} Balasan</span>
                    </span>

                    {c.is_reply && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '3px', color: '#38bdf8' }}>
                        <CornerDownRight size={11} />
                        <span>Komentar Balasan (Reply)</span>
                      </span>
                    )}

                    {c.is_pinned && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '3px', color: '#fbbf24' }}>
                        <Pin size={11} />
                        <span>Disematkan Kreator</span>
                      </span>
                    )}

                    {c.is_hearted && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '3px', color: '#f43f5e' }}>
                        <Heart size={11} />
                        <span>Diberi Heart oleh Kanal</span>
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '12px 24px',
            background: 'rgba(15, 23, 42, 0.8)',
            borderTop: '1px solid rgba(51, 65, 85, 0.4)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.78rem',
            color: '#64748b',
          }}
        >
          <span>Menampilkan {filteredComments.length} dari {comments.length} komentar</span>
          <button
            className="btn btn-secondary"
            onClick={onClose}
            style={{ fontSize: '0.78rem', padding: '6px 14px' }}
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};
