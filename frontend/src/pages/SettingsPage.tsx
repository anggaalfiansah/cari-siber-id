import React, { useState, useEffect } from 'react';
import { Save, CheckCircle, AlertCircle, Key, ShieldCheck, Zap } from 'lucide-react';
import { Settings } from '../api/types';
import { api, waitForPyWebView } from '../api/bridge';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    ai_provider: 'gemini',
    ai_model: 'gemini-2.5-flash',
    gemini_api_key: '',
    openrouter_api_key: '',
    edgeone_api_key: '',
    custom_base_url: 'https://api.tokenai.id/v1',
    custom_api_key: '',
    youtube_api_key: '',
    agentic_gates_enabled: true,
    default_comment_limit: 1000,
    default_sort_by: 'top',
    default_include_replies: true,
  });

  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      await waitForPyWebView();
      const data = await api.get_settings();
      setSettings(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(false);
    try {
      await waitForPyWebView();
      await api.save_settings(settings);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal menyimpan pengaturan: ' + err?.message);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.test_ai_connection(settings);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ success: false, message: err?.message || 'Uji koneksi gagal.' });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div style={{ maxWidth: '780px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f8fafc' }}>Pengaturan & Kredensial AI</h1>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '2px' }}>
          Kunci API disimpan secara aman di Windows Credential Manager (keyring) lokal dan tidak disimpan di plain text.
        </p>
      </div>

      {saveSuccess && (
        <div style={{ padding: '12px 16px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
          <CheckCircle size={18} />
          <span>Pengaturan dan kredensial berhasil disimpan!</span>
        </div>
      )}

      {testResult && (
        <div style={{
          padding: '12px 16px',
          background: testResult.success ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          border: `1px solid ${testResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          color: testResult.success ? '#34d399' : '#f87171',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.85rem',
        }}>
          {testResult.success ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          <span>{testResult.message}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="panel panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* AI Provider Config */}
        <div>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={16} color="#38bdf8" />
            <span>Penyedia Model AI (Semantic Labeling & Insights)</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Provider Aktif</label>
              <select
                className="form-select"
                value={settings.ai_provider}
                onChange={(e) => {
                  const val = e.target.value;
                  const newModel = val === 'custom' && (!settings.ai_model || settings.ai_model.includes('gemini')) 
                    ? 'deepseek-v4-flash' 
                    : settings.ai_model;
                  setSettings({ ...settings, ai_provider: val, ai_model: newModel });
                }}
              >
                <option value="gemini">Google Gemini (Disarankan)</option>
                <option value="custom">Custom OpenAI-Compatible (TOKENAI.ID, vLLM, dll.)</option>
                <option value="openrouter">OpenRouter AI Gateway</option>
                <option value="edgeone">EdgeOne AI</option>
              </select>
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Nama Model</label>
              <input
                type="text"
                className="form-input"
                value={settings.ai_model}
                onChange={(e) => setSettings({ ...settings, ai_model: e.target.value })}
                placeholder={settings.ai_provider === 'custom' ? 'misal: deepseek-v4-flash' : 'misal: gemini-3.8-flash'}
              />
            </div>
          </div>

          {settings.ai_provider === 'custom' && (
            <div className="form-group" style={{ marginTop: '14px', marginBottom: 0 }}>
              <label className="form-label">Custom Base URL (OpenAI-Compatible Endpoint)</label>
              <input
                type="text"
                className="form-input mono-font"
                value={settings.custom_base_url || ''}
                onChange={(e) => setSettings({ ...settings, custom_base_url: e.target.value })}
                placeholder="https://api.tokenai.id/v1"
              />
              <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
                Contoh: <code>https://api.tokenai.id/v1</code>, <code>http://localhost:8000/v1</code> (vLLM / LM Studio)
              </span>
            </div>
          )}
        </div>

        {/* API Keys */}
        <div style={{ borderTop: '1px solid rgba(51, 65, 85, 0.4)', paddingTop: '16px' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Key size={16} color="#fbbf24" />
            <span>Kunci API (Credential Store)</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {settings.ai_provider === 'custom' && (
              <div className="form-group" style={{ margin: 0, background: 'rgba(56, 189, 248, 0.05)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                <label className="form-label" style={{ color: '#38bdf8' }}>Custom Provider API Key (TOKENAI.ID / Endpoint Aktif)</label>
                <input
                  type="password"
                  className="form-input mono-font"
                  placeholder="sk-..."
                  value={settings.custom_api_key || ''}
                  onChange={(e) => setSettings({ ...settings, custom_api_key: e.target.value })}
                />
              </div>
            )}

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Gemini API Key</label>
              <input
                type="password"
                className="form-input mono-font"
                placeholder="Masukkan API Key Gemini..."
                value={settings.gemini_api_key || ''}
                onChange={(e) => setSettings({ ...settings, gemini_api_key: e.target.value })}
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">OpenRouter API Key (Opsional)</label>
              <input
                type="password"
                className="form-input mono-font"
                placeholder="sk-or-v1-..."
                value={settings.openrouter_api_key || ''}
                onChange={(e) => setSettings({ ...settings, openrouter_api_key: e.target.value })}
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">EdgeOne API Key (Opsional)</label>
              <input
                type="password"
                className="form-input mono-font"
                placeholder="sk-..."
                value={settings.edgeone_api_key || ''}
                onChange={(e) => setSettings({ ...settings, edgeone_api_key: e.target.value })}
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">YouTube Data API v3 Key (Opsional)</label>
              <input
                type="password"
                className="form-input mono-font"
                placeholder="AIzaSy..."
                value={settings.youtube_api_key || ''}
                onChange={(e) => setSettings({ ...settings, youtube_api_key: e.target.value })}
              />
              <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
                Digunakan untuk pencarian cepat video. Jika kosong, sistem otomatis beralih ke pencarian web tanpa kuota API.
              </span>
            </div>
          </div>
        </div>

        {/* Hardened Gates */}
        <div style={{ borderTop: '1px solid rgba(51, 65, 85, 0.4)', paddingTop: '16px' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={16} color="#10b981" />
            <span>4 Agentic AI Hardened Verification Gates</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '12px' }}>
            Menjalankan verifikasi mandiri bebas halusinasi (Quality Gate, Topic Gate, Verification Gate, Report Gate).
          </p>

          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <input
              type="checkbox"
              checked={settings.agentic_gates_enabled}
              onChange={(e) => setSettings({ ...settings, agentic_gates_enabled: e.target.checked })}
            />
            Aktifkan 4 Agentic Gates Selama Analisis (Akurasi Tinggi)
          </label>
        </div>

        {/* Buttons */}
        <div style={{ borderTop: '1px solid rgba(51, 65, 85, 0.4)', paddingTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleTestConnection}
            disabled={testing}
          >
            <Zap size={16} />
            <span>{testing ? 'Menguji Koneksi...' : 'Uji Koneksi AI'}</span>
          </button>

          <button type="submit" className="btn btn-primary" style={{ padding: '10px 24px' }}>
            <Save size={16} />
            <span>Simpan Pengaturan</span>
          </button>
        </div>
      </form>
    </div>
  );
};
