import React, { useState } from 'react';
import { TopicItem } from '../api/types';
import { Search } from 'lucide-react';

interface TopicTableProps {
  topics: TopicItem[];
}

export const TopicTable: React.FC<TopicTableProps> = ({ topics }) => {
  const [filter, setFilter] = useState('');
  const [selectedSentiment, setSelectedSentiment] = useState('ALL');

  const filtered = topics.filter((t) => {
    const textSearch = (t.topic_name + ' ' + (t.sub_issue || '') + ' ' + (t.category || '') + ' ' + t.sample_comment).toLowerCase();
    const matchText = textSearch.includes(filter.toLowerCase());
    const matchSent = selectedSentiment === 'ALL' || t.sentiment.toUpperCase() === selectedSentiment;
    return matchText && matchSent;
  });

  const getSentimentBadge = (sent: string) => {
    switch (sent.toLowerCase()) {
      case 'positif':
        return <span className="badge badge-low">Positif</span>;
      case 'negatif':
        return <span className="badge badge-high">Negatif</span>;
      default:
        return <span className="badge" style={{ background: '#334155', color: '#cbd5e1' }}>Netral</span>;
    }
  };

  return (
    <div className="panel">
      <div className="panel-header" style={{ gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '240px' }}>
          <Search size={16} color="#64748b" />
          <input
            type="text"
            className="form-input"
            placeholder="Cari isu, kategori, atau kutipan komentar..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{ padding: '6px 12px', fontSize: '0.85rem' }}
          />
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['ALL', 'POSITIF', 'NETRAL', 'NEGATIF'].map((s) => (
            <button
              key={s}
              className="btn btn-secondary"
              onClick={() => setSelectedSentiment(s)}
              style={{
                padding: '4px 12px',
                fontSize: '0.75rem',
                background: selectedSentiment === s ? '#0284c7' : '#1e293b',
                color: selectedSentiment === s ? '#ffffff' : '#94a3b8',
                borderColor: selectedSentiment === s ? '#0284c7' : '#334155',
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div style={{ maxHeight: '420px', overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: '#090d16', color: '#38bdf8', textAlign: 'left', borderBottom: '2px solid #334155' }}>
              <th style={{ padding: '12px 14px', width: '45px' }}>#</th>
              <th style={{ padding: '12px 16px', width: '280px' }}>Sub-Isu & Pokok Bahasan</th>
              <th style={{ padding: '12px 14px', width: '140px' }}>Kategori</th>
              <th style={{ padding: '12px 14px', width: '90px' }}>Sentimen</th>
              <th style={{ padding: '12px 14px', width: '85px', textAlign: 'right' }}>Komentar</th>
              <th style={{ padding: '12px 16px' }}>Sampel Opini Nyata</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>
                  Tidak ada topik yang cocok dengan filter.
                </td>
              </tr>
            ) : (
              filtered.map((item, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid rgba(51, 65, 85, 0.25)',
                    background: idx % 2 === 0 ? 'transparent' : 'rgba(15, 23, 42, 0.3)',
                  }}
                >
                  <td style={{ padding: '12px 14px', color: '#64748b', fontFamily: 'monospace' }}>
                    {item.topic_id}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: '0.875rem' }}>
                      {item.sub_issue || item.topic_name}
                    </div>
                    {item.keywords && (
                      <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '3px' }}>
                        Kata Kunci: <span style={{ color: '#94a3b8' }}>{item.keywords}</span>
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span style={{
                      display: 'inline-block',
                      background: 'rgba(51, 65, 85, 0.4)',
                      border: '1px solid #334155',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      color: '#cbd5e1',
                    }}>
                      {item.category || 'Umum'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    {getSentimentBadge(item.sentiment)}
                  </td>
                  <td style={{ padding: '12px 14px', fontFamily: 'monospace', color: '#38bdf8', fontWeight: 600, textAlign: 'right' }}>
                    {item.total_comments.toLocaleString()}
                  </td>
                  <td style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '0.8rem', fontStyle: 'italic', maxWidth: '320px' }}>
                    "{item.sample_comment || '-'}"
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
