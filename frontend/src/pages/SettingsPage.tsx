import React, { useState, useEffect } from 'react';
import {
  Save,
  CheckCircle,
  AlertCircle,
  Key,
  ShieldCheck,
  Zap,
  Eye,
  EyeOff,
  Info,
  Sparkles,
  Plus,
  Trash2,
  Edit2,
  Check,
  CheckCircle2,
  Server,
  Layers,
  X,
} from 'lucide-react';
import { Settings, AIAccountProfile } from '../api/types';
import { api, waitForPyWebView } from '../api/bridge';

const MODEL_PRESETS = [
  { label: 'Gemini 2.0 Flash (Sangat Cepat)', value: 'google/gemini-2.0-flash-001', provider: 'openrouter' },
  { label: 'Qwen 2.5 72B (Cerdas & Cepat)', value: 'qwen/qwen-2.5-72b-instruct', provider: 'openrouter' },
  { label: 'Llama 3.3 70B (Akurat)', value: 'meta-llama/llama-3.3-70b-instruct', provider: 'openrouter' },
  { label: 'Gemini 2.5 Flash Direct', value: 'gemini-2.5-flash', provider: 'gemini' },
  { label: 'DeepSeek V3/V4', value: 'deepseek-v4-flash', provider: 'custom' },
];

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    ai_provider: 'gemini',
    ai_model: 'gemini-2.5-flash',
    active_account_id: 'acc_default_1',
    ai_accounts: [],
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
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});

  // State untuk form Tambah / Edit Akun
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [accountForm, setAccountForm] = useState<{
    name: string;
    provider: string;
    model: string;
    base_url: string;
    api_key: string;
  }>({
    name: '',
    provider: 'openrouter',
    model: 'google/gemini-2.0-flash-001',
    base_url: 'https://openrouter.ai/api/v1',
    api_key: '',
  });

  // State hasil uji latensi per akun { [accId]: { testing: boolean, result: { success: boolean, message: string } } }
  const [accountTestStatus, setAccountTestStatus] = useState<Record<string, { testing: boolean; result?: { success: boolean; message: string } }>>({});

  const toggleKeyVisibility = (field: string) => {
    setShowKeys((prev) => ({ ...prev, [field]: !prev[field] }));
  };

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

  const handleSelectActiveAccount = async (account: AIAccountProfile) => {
    const updatedAccounts = (settings.ai_accounts || []).map((a) => ({
      ...a,
      is_active: a.id === account.id,
    }));

    const updatedSettings: Settings = {
      ...settings,
      active_account_id: account.id,
      ai_accounts: updatedAccounts,
      ai_provider: account.provider,
      ai_model: account.model,
      custom_base_url: account.base_url || settings.custom_base_url,
      custom_api_key: account.provider === 'custom' ? account.api_key : settings.custom_api_key,
      openrouter_api_key: account.provider === 'openrouter' ? account.api_key : settings.openrouter_api_key,
      gemini_api_key: account.provider === 'gemini' ? account.api_key : settings.gemini_api_key,
      edgeone_api_key: account.provider === 'edgeone' ? account.api_key : settings.edgeone_api_key,
    };

    setSettings(updatedSettings);
    try {
      await waitForPyWebView();
      await api.save_settings(updatedSettings);
      setSaveMessage(`Akun "${account.name}" berhasil diaktifkan untuk seluruh analisis!`);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal mengaktifkan akun: ' + err?.message);
    }
  };

  const openAddForm = () => {
    setEditingId(null);
    setAccountForm({
      name: `Akun AI Baru ${(settings.ai_accounts?.length || 0) + 1}`,
      provider: 'openrouter',
      model: 'google/gemini-2.0-flash-001',
      base_url: 'https://openrouter.ai/api/v1',
      api_key: '',
    });
    setIsFormOpen(true);
  };

  const openEditForm = (acc: AIAccountProfile) => {
    setEditingId(acc.id);
    setAccountForm({
      name: acc.name,
      provider: acc.provider,
      model: acc.model,
      base_url: acc.base_url || '',
      api_key: acc.api_key || '',
    });
    setIsFormOpen(true);
  };

  const handleSaveAccountForm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accountForm.name.trim()) {
      alert('Nama akun tidak boleh kosong.');
      return;
    }
    if (!accountForm.model.trim()) {
      alert('Nama model tidak boleh kosong.');
      return;
    }

    let updatedList = [...(settings.ai_accounts || [])];

    if (editingId) {
      // Edit mode
      updatedList = updatedList.map((a) => {
        if (a.id === editingId) {
          return {
            ...a,
            name: accountForm.name.trim(),
            provider: accountForm.provider,
            model: accountForm.model.trim(),
            base_url: accountForm.base_url.trim(),
            api_key: accountForm.api_key.trim(),
          };
        }
        return a;
      });
    } else {
      // Add mode
      const newId = `acc_${Date.now()}`;
      const isFirst = updatedList.length === 0;
      const newAcc: AIAccountProfile = {
        id: newId,
        name: accountForm.name.trim(),
        provider: accountForm.provider,
        model: accountForm.model.trim(),
        base_url: accountForm.base_url.trim(),
        api_key: accountForm.api_key.trim(),
        is_active: isFirst,
      };
      updatedList.push(newAcc);
    }

    const currentActiveId = settings.active_account_id || (updatedList[0] ? updatedList[0].id : undefined);
    const activeAcc = updatedList.find((a) => a.id === currentActiveId) || updatedList[0];

    const updatedSettings: Settings = {
      ...settings,
      ai_accounts: updatedList,
      active_account_id: activeAcc?.id,
      ai_provider: activeAcc?.provider || settings.ai_provider,
      ai_model: activeAcc?.model || settings.ai_model,
      custom_base_url: activeAcc?.base_url || settings.custom_base_url,
    };

    if (activeAcc?.provider === 'custom') updatedSettings.custom_api_key = activeAcc.api_key;
    if (activeAcc?.provider === 'openrouter') updatedSettings.openrouter_api_key = activeAcc.api_key;
    if (activeAcc?.provider === 'gemini') updatedSettings.gemini_api_key = activeAcc.api_key;

    setSettings(updatedSettings);
    setIsFormOpen(false);

    try {
      await waitForPyWebView();
      await api.save_settings(updatedSettings);
      setSaveMessage(editingId ? 'Akun AI berhasil diperbarui!' : 'Akun AI baru berhasil ditambahkan!');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal menyimpan akun: ' + err?.message);
    }
  };

  const handleDeleteAccount = async (accId: string) => {
    if ((settings.ai_accounts || []).length <= 1) {
      alert('Minimal harus ada 1 akun AI tersimpan.');
      return;
    }
    if (!confirm('Apakah Anda yakin ingin menghapus akun AI ini?')) return;

    const updatedList = (settings.ai_accounts || []).filter((a) => a.id !== accId);
    let newActiveId = settings.active_account_id;
    if (newActiveId === accId) {
      newActiveId = updatedList[0].id;
    }

    const activeAcc = updatedList.find((a) => a.id === newActiveId) || updatedList[0];
    const updatedSettings: Settings = {
      ...settings,
      ai_accounts: updatedList,
      active_account_id: activeAcc.id,
      ai_provider: activeAcc.provider,
      ai_model: activeAcc.model,
      custom_base_url: activeAcc.base_url || settings.custom_base_url,
    };

    setSettings(updatedSettings);
    try {
      await waitForPyWebView();
      await api.save_settings(updatedSettings);
      setSaveMessage('Akun berhasil dihapus.');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal menghapus akun: ' + err?.message);
    }
  };

  const handleTestAccountConnection = async (acc: AIAccountProfile) => {
    setAccountTestStatus((prev) => ({
      ...prev,
      [acc.id]: { testing: true },
    }));

    try {
      const res = await api.test_ai_connection({
        provider: acc.provider,
        model: acc.model,
        base_url: acc.base_url,
        api_key: acc.api_key,
      });
      setAccountTestStatus((prev) => ({
        ...prev,
        [acc.id]: { testing: false, result: res },
      }));
    } catch (err: any) {
      setAccountTestStatus((prev) => ({
        ...prev,
        [acc.id]: {
          testing: false,
          result: { success: false, message: err?.message || 'Uji koneksi gagal.' },
        },
      }));
    }
  };

  const handleSaveGlobal = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(false);
    try {
      await waitForPyWebView();
      await api.save_settings(settings);
      setSaveMessage('Pengaturan umum berhasil disimpan!');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal menyimpan pengaturan: ' + err?.message);
    }
  };

  const activeAccount = (settings.ai_accounts || []).find((a) => a.id === settings.active_account_id) || settings.ai_accounts?.[0];

  return (
    <div style={{ maxWidth: '860px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Page Header */}
      <div>
        <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
          Pengaturan Akun AI & Sistem
        </h1>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '2px' }}>
          Kelola multiple profil/akun provider AI (TokenAI, OpenRouter, Gemini, vLLM, Ollama). Cukup input 1x untuk tiap akun dan beralih akun aktif dengan 1 klik.
        </p>
      </div>

      {/* Info Tip Petunjuk Kecepatan */}
      <div style={{
        background: 'rgba(56, 189, 248, 0.08)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        borderRadius: '10px',
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        fontSize: '0.82rem',
        color: '#e2e8f0',
        lineHeight: 1.5,
      }}>
        <Info size={18} color="#38bdf8" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong style={{ color: '#38bdf8' }}>Fleksibilitas Multiple Akun AI:</strong>
          <div style={{ marginTop: '3px', color: '#cbd5e1' }}>
            Anda dapat menyimpan berbagai endpoint (misal satu akun OpenRouter dengan Gemini Flash untuk kecepatan tinggi, dan satu akun TokenAI/vLLM kustom). Tekan tombol <strong>"Gunakan Akun Ini"</strong> untuk memilih provider aktif yang akan digunakan oleh pipeline.
          </div>
        </div>
      </div>

      {saveSuccess && (
        <div style={{ padding: '12px 16px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
          <CheckCircle size={18} />
          <span>{saveMessage || 'Pengaturan berhasil disimpan!'}</span>
        </div>
      )}

      {/* ========================================================= */}
      {/* SECTION 1: DAFTAR AKUN AI (MULTIPLE ACCOUNTS SELECTOR)    */}
      {/* ========================================================= */}
      <div className="panel panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={18} color="#38bdf8" />
            <span>Daftar Akun Provider AI Tersimpan</span>
            <span style={{ fontSize: '0.75rem', background: 'rgba(2, 132, 199, 0.2)', color: '#38bdf8', padding: '2px 8px', borderRadius: '12px', border: '1px solid rgba(2, 132, 199, 0.4)' }}>
              {settings.ai_accounts?.length || 0} Akun
            </span>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={openAddForm}
            style={{ fontSize: '0.8rem', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Plus size={15} />
            <span>+ Tambah Akun AI Baru</span>
          </button>
        </div>

        {/* List of Account Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '12px' }}>
          {(settings.ai_accounts || []).map((acc, idx) => {
            const isActive = acc.id === settings.active_account_id;
            const testStatus = accountTestStatus[acc.id];

            return (
              <div
                key={acc.id}
                style={{
                  background: isActive ? 'rgba(2, 132, 199, 0.12)' : 'rgba(15, 23, 42, 0.65)',
                  border: isActive ? '2px solid #0284c7' : '1px solid rgba(51, 65, 85, 0.6)',
                  borderRadius: '10px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px',
                  boxShadow: isActive ? '0 0 16px rgba(2, 132, 199, 0.25)' : 'none',
                  transition: 'all 0.2s ease',
                }}
              >
                <div>
                  {/* Card Top: Name & Active Badge */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '6px',
                        background: isActive ? 'rgba(2, 132, 199, 0.3)' : 'rgba(51, 65, 85, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: isActive ? '#38bdf8' : '#94a3b8',
                        fontWeight: 700,
                        fontSize: '0.8rem',
                      }}>
                        #{idx + 1}
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.92rem', color: '#f8fafc' }}>
                          {acc.name}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          PROVIDER: <strong style={{ color: '#38bdf8' }}>{acc.provider}</strong>
                        </div>
                      </div>
                    </div>

                    {isActive ? (
                      <span style={{
                        background: 'rgba(16, 185, 129, 0.2)',
                        border: '1px solid #10b981',
                        color: '#34d399',
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        padding: '3px 8px',
                        borderRadius: '12px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}>
                        <Check size={12} /> AKTIF DIGUNAKAN
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleSelectActiveAccount(acc)}
                        style={{
                          background: 'rgba(51, 65, 85, 0.4)',
                          border: '1px solid rgba(71, 85, 105, 0.6)',
                          color: '#cbd5e1',
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          padding: '3px 10px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderColor = '#0284c7';
                          e.currentTarget.style.color = '#38bdf8';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderColor = 'rgba(71, 85, 105, 0.6)';
                          e.currentTarget.style.color = '#cbd5e1';
                        }}
                      >
                        Gunakan Akun Ini
                      </button>
                    )}
                  </div>

                  {/* Model & Endpoint Specs */}
                  <div style={{
                    marginTop: '10px',
                    background: 'rgba(9, 13, 22, 0.6)',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    fontSize: '0.76rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    fontFamily: 'monospace',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                      <span>Model:</span>
                      <strong style={{ color: '#f1f5f9' }}>{acc.model}</strong>
                    </div>
                    {acc.base_url && acc.provider === 'custom' && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.7rem' }}>
                        <span>Endpoint:</span>
                        <span style={{ color: '#94a3b8' }} title={acc.base_url}>{acc.base_url.replace('https://', '')}</span>
                      </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.7rem' }}>
                      <span>API Key:</span>
                      <span style={{ color: acc.api_key ? '#10b981' : '#f87171' }}>
                        {acc.api_key ? `Tersimpan (•••${acc.api_key.slice(-4)})` : 'Belum diisi'}
                      </span>
                    </div>
                  </div>

                  {/* Test Feedback for this account */}
                  {testStatus?.result && (
                    <div style={{
                      marginTop: '8px',
                      padding: '6px 10px',
                      borderRadius: '6px',
                      fontSize: '0.72rem',
                      background: testStatus.result.success ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      border: `1px solid ${testStatus.result.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                      color: testStatus.result.success ? '#34d399' : '#f87171',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}>
                      {testStatus.result.success ? <CheckCircle size={13} /> : <AlertCircle size={13} />}
                      <span style={{ lineHeight: 1.3 }}>{testStatus.result.message}</span>
                    </div>
                  )}
                </div>

                {/* Card Actions: Test, Edit, Delete */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(51, 65, 85, 0.4)', paddingTop: '10px' }}>
                  <button
                    type="button"
                    onClick={() => handleTestAccountConnection(acc)}
                    disabled={testStatus?.testing}
                    style={{
                      background: 'transparent',
                      border: '1px solid rgba(56, 189, 248, 0.4)',
                      color: '#38bdf8',
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      padding: '4px 10px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                    }}
                  >
                    <Zap size={13} />
                    <span>{testStatus?.testing ? 'Menguji...' : 'Uji Latensi'}</span>
                  </button>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <button
                      type="button"
                      onClick={() => openEditForm(acc)}
                      style={{
                        background: 'transparent',
                        border: '1px solid rgba(148, 163, 184, 0.3)',
                        color: '#cbd5e1',
                        fontSize: '0.72rem',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                      title="Edit pengaturan akun ini"
                    >
                      <Edit2 size={12} />
                      <span>Edit</span>
                    </button>

                    {(settings.ai_accounts || []).length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleDeleteAccount(acc.id)}
                        style={{
                          background: 'transparent',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          color: '#f87171',
                          fontSize: '0.72rem',
                          padding: '4px 8px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                        }}
                        title="Hapus akun ini"
                      >
                        <Trash2 size={12} />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Modal / Expander Form for Add or Edit Account */}
        {isFormOpen && (
          <div style={{
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid #0284c7',
            borderRadius: '10px',
            padding: '18px',
            marginTop: '8px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Key size={16} color="#38bdf8" />
                <span>{editingId ? 'Edit Profil Akun AI' : 'Tambah Profil Akun AI Baru'}</span>
              </div>
              <button
                type="button"
                onClick={() => setIsFormOpen(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveAccountForm} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Nama / Label Akun *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={accountForm.name}
                    onChange={(e) => setAccountForm({ ...accountForm, name: e.target.value })}
                    placeholder="misal: OpenRouter Gemini Flash atau TokenAI Cadangan"
                    required
                  />
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Provider AI</label>
                  <select
                    className="form-select"
                    value={accountForm.provider}
                    onChange={(e) => {
                      const val = e.target.value;
                      let defaultModel = accountForm.model;
                      let defaultUrl = accountForm.base_url;
                      if (val === 'openrouter') {
                        defaultModel = 'google/gemini-2.0-flash-001';
                        defaultUrl = 'https://openrouter.ai/api/v1';
                      } else if (val === 'gemini') {
                        defaultModel = 'gemini-2.5-flash';
                        defaultUrl = '';
                      } else if (val === 'custom') {
                        defaultModel = 'deepseek-v4-flash';
                        defaultUrl = 'https://api.tokenai.id/v1';
                      }
                      setAccountForm({
                        ...accountForm,
                        provider: val,
                        model: defaultModel,
                        base_url: defaultUrl,
                      });
                    }}
                  >
                    <option value="openrouter">OpenRouter Gateway (Banyak Model / Multi-Provider)</option>
                    <option value="custom">Custom OpenAI-Compatible (TokenAI.id, vLLM, Ollama, LM Studio)</option>
                    <option value="gemini">Google Gemini Direct (Resmi)</option>
                    <option value="edgeone">EdgeOne AI</option>
                  </select>
                </div>
              </div>

              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">Model Identifier *</label>
                <input
                  type="text"
                  className="form-input mono-font"
                  value={accountForm.model}
                  onChange={(e) => setAccountForm({ ...accountForm, model: e.target.value })}
                  placeholder="misal: google/gemini-2.0-flash-001 atau qwen/qwen-2.5-72b-instruct"
                  required
                />
              </div>

              {/* Quick Preset Chips inside Form */}
              <div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Sparkles size={12} color="#f59e0b" />
                  <span>Preset Rekomendasi:</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {MODEL_PRESETS.map((p) => (
                    <button
                      key={p.value}
                      type="button"
                      onClick={() => setAccountForm({
                        ...accountForm,
                        provider: p.provider,
                        model: p.value,
                        base_url: p.provider === 'custom' ? 'https://api.tokenai.id/v1' : (p.provider === 'openrouter' ? 'https://openrouter.ai/api/v1' : ''),
                      })}
                      style={{
                        background: accountForm.model === p.value ? 'rgba(56, 189, 248, 0.2)' : 'rgba(30, 41, 59, 0.8)',
                        border: `1px solid ${accountForm.model === p.value ? '#38bdf8' : 'rgba(71, 85, 105, 0.5)'}`,
                        color: accountForm.model === p.value ? '#38bdf8' : '#cbd5e1',
                        borderRadius: '6px',
                        padding: '3px 8px',
                        fontSize: '0.72rem',
                        cursor: 'pointer',
                      }}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Base URL jika custom */}
              {accountForm.provider === 'custom' && (
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Custom Base URL</label>
                  <input
                    type="text"
                    className="form-input mono-font"
                    value={accountForm.base_url}
                    onChange={(e) => setAccountForm({ ...accountForm, base_url: e.target.value })}
                    placeholder="https://api.tokenai.id/v1"
                  />
                  <span style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '3px', display: 'block' }}>
                    Contoh: <code>https://api.tokenai.id/v1</code>, <code>http://localhost:8000/v1</code>
                  </span>
                </div>
              )}

              {/* API Key */}
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">API Key untuk Akun Ini</label>
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                  <input
                    type={showKeys['form_key'] ? 'text' : 'password'}
                    className="form-input mono-font"
                    placeholder="sk-..."
                    value={accountForm.api_key}
                    onChange={(e) => setAccountForm({ ...accountForm, api_key: e.target.value })}
                    style={{ paddingRight: '40px' }}
                  />
                  <button
                    type="button"
                    onClick={() => toggleKeyVisibility('form_key')}
                    style={{ position: 'absolute', right: '10px', background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                  >
                    {showKeys['form_key'] ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '6px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsFormOpen(false)}
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <Save size={15} />
                  <span>{editingId ? 'Simpan Perubahan Akun' : 'Tambahkan Akun'}</span>
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* ========================================================= */}
      {/* SECTION 2: PENGATURAN UMUM LAINNYA (YOUTUBE & GATES)      */}
      {/* ========================================================= */}
      <form onSubmit={handleSaveGlobal} className="panel panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} color="#fbbf24" />
          <span>Pengaturan Tambahan & Kredensial Platform</span>
        </div>

        {/* YouTube API Key */}
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">YouTube Data API v3 Key (Opsional)</label>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <input
              type={showKeys['youtube'] ? 'text' : 'password'}
              className="form-input mono-font"
              placeholder="AIzaSy..."
              value={settings.youtube_api_key || ''}
              onChange={(e) => setSettings({ ...settings, youtube_api_key: e.target.value })}
              style={{ paddingRight: '40px' }}
            />
            <button
              type="button"
              onClick={() => toggleKeyVisibility('youtube')}
              style={{ position: 'absolute', right: '10px', background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
            >
              {showKeys['youtube'] ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
            Digunakan untuk pencarian cepat video. Jika dibiarkan kosong, sistem otomatis memakai web scraper tanpa batas kuota.
          </span>
        </div>

        {/* Hardened Gates */}
        <div style={{ borderTop: '1px solid rgba(51, 65, 85, 0.4)', paddingTop: '14px' }}>
          <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={16} color="#10b981" />
            <span>4 Agentic AI Hardened Verification Gates</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '10px' }}>
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

        <div style={{ borderTop: '1px solid rgba(51, 65, 85, 0.4)', paddingTop: '14px', display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" className="btn btn-primary" style={{ padding: '9px 24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Save size={16} />
            <span>Simpan Pengaturan Umum</span>
          </button>
        </div>
      </form>
    </div>
  );
};
