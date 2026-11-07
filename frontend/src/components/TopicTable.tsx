import React, { useState } from 'react';
import { TopicItem } from '../api/types';
import { Search } from 'lucide-react';

interface TopicTableProps {
  topics?: TopicItem[];
}

export const TopicTable: React.FC<TopicTableProps> = ({ topics }) => {
  const [filter, setFilter] = useState('');
  const [selectedSentiment, setSelectedSentiment] = useState('ALL');

  const safeTopics = Array.isArray(topics) ? topics : [];

  const filtered = safeTopics.filter((t) => {
    const textSearch = (String(t.topic_name || '') + ' ' + String(t.sub_issue || '') + ' ' + String(t.threat_domain || t.category || '') + ' ' + String(t.sample_comment || '')).toLowerCase();
    const matchText = textSearch.includes(filter.toLowerCase());
    const matchSent = selectedSentiment === 'ALL' || String(t.sentiment || '').toUpperCase() === selectedSentiment;
    return matchText && matchSent;
  });

  const getSentimentBadge = (sent?: string) => {
    switch (String(sent || '').toLowerCase()) {
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
            placeholder="Cari isu, domain ancaman, atau kutipan komentar..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{ padding: '6px 12px', fontSize: '0.85rem' }}
          />
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[
            { id: 'ALL', label: 'SEMUA' },
            { id: 'POSITIF', label: 'POSITIF' },
            { id: 'NETRAL', label: 'NETRAL' },
            { id: 'NEGATIF', label: 'HASUTAN / SARA / DELEGITIMASI' },
          ].map((s) => (
            <button
              key={s.id}
              className="btn btn-secondary"
              onClick={() => setSelectedSentiment(s.id)}
              style={{
                padding: '4px 12px',
                fontSize: '0.75rem',
                background: selectedSentiment === s.id ? (s.id === 'NEGATIF' ? '#dc2626' : '#0284c7') : '#1e293b',
                color: selectedSentiment === s.id ? '#ffffff' : '#94a3b8',
                borderColor: selectedSentiment === s.id ? (s.id === 'NEGATIF' ? '#dc2626' : '#0284c7') : '#334155',
                fontWeight: selectedSentiment === s.id ? 700 : 500,
              }}
            >
              {s.label}
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
              <th style={{ padding: '12px 14px', width: '170px' }}>Domain Ancaman</th>
              <th style={{ padding: '12px 14px', width: '90px' }}>Sentimen</th>
              <th style={{ padding: '12px 14px', width: '85px', textAlign: 'right' }}>Komentar</th>
              <th style={{ padding: '12px 16px' }}>Sampel Opini Nyata</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>
                  Tidak ada topik yang cocok dengan filter atau data masih kosong.
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
                      <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>
                        Kata Kunci: {item.keywords}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '12px 14px', color: '#cbd5e1' }}>
                    {item.threat_domain || item.category || 'Opini & Respons Publik'}
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    {getSentimentBadge(item.sentiment)}
                  </td>
                  <td style={{ padding: '12px 14px', textAlign: 'right', fontFamily: 'monospace', color: '#38bdf8', fontWeight: 600 }}>
                    {(Number(item.total_comments) || 0).toLocaleString()}
                  </td>
                  <td style={{ padding: '12px 16px', color: '#94a3b8', fontStyle: 'italic', maxWidth: '340px' }}>
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
