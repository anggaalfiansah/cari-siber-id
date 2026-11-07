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
  Server,
  Layers,
  X,
  WifiOff,
  Cloud,
  Globe,
} from 'lucide-react';
import { Settings, AIAccountProfile } from '../api/types';
import { api, waitForPyWebView } from '../api/bridge';

const MODEL_PRESETS = [
  { label: 'Ollama Qwen 2.5 7B (Air-Gapped Lokal)', value: 'qwen2.5:7b', provider: 'custom', base_url: 'http://127.0.0.1:11434/v1' },
  { label: 'Ollama Llama 3.1 8B (Air-Gapped Lokal)', value: 'llama3.1:8b', provider: 'custom', base_url: 'http://127.0.0.1:11434/v1' },
  { label: 'Gemini 2.5 Flash Direct (Resmi)', value: 'gemini-2.5-flash', provider: 'gemini', base_url: '' },
  { label: 'OpenRouter Gemini 2.0 Flash', value: 'google/gemini-2.0-flash-001', provider: 'openrouter', base_url: 'https://openrouter.ai/api/v1' },
  { label: 'OpenRouter Qwen 2.5 72B Instruct', value: 'qwen/qwen-2.5-72b-instruct', provider: 'openrouter', base_url: 'https://openrouter.ai/api/v1' },
];

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    ai_provider: 'gemini',
    ai_model: 'gemini-2.5-flash',
    active_account_id: 'acc_default_1',
    ai_accounts: [],
    gemini_api_key: '',
    openrouter_api_key: '',
    custom_base_url: 'http://127.0.0.1:11434/v1',
    custom_api_key: '',
    youtube_api_key: '',
    agentic_gates_enabled: true,
    default_comment_limit: 1000,
    default_sort_by: 'top',
    default_include_replies: true,
  });

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
    provider: 'custom',
    model: 'qwen2.5:7b',
    base_url: 'http://127.0.0.1:11434/v1',
    api_key: 'local-airgap',
  });

  const [accountTestStatus, setAccountTestStatus] = useState<
    Record<string, { testing: boolean; result?: { success: boolean; message: string } }>
  >({});

  const toggleKeyVisibility = (field: string) => {
    setShowKeys((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      await waitForPyWebView();
      const data = await api.get_settings();
      setSettings(data);
    } catch (e) {
      console.error(e);
    }
  };

  const applyOperationalReadinessProfile = async (profileType: 'airgap' | 'gemini' | 'openrouter') => {
    let profileAcc: AIAccountProfile;
    const existingList = [...(settings.ai_accounts || [])];

    if (profileType === 'airgap') {
      const found = existingList.find((a) => a.provider === 'custom' && (a.base_url || '').includes('127.0.0.1'));
      profileAcc = found || {
        id: 'acc_airgap_local',
        name: 'Intranet Militer Air-Gapped (Local Ollama / vLLM)',
        provider: 'custom',
        model: 'qwen2.5:7b',
        base_url: 'http://127.0.0.1:11434/v1',
        api_key: 'local-airgap',
        is_active: true,
      };
    } else if (profileType === 'gemini') {
      const found = existingList.find((a) => a.provider === 'gemini');
      profileAcc = found || {
        id: 'acc_gemini_official',
        name: 'Google Gemini Official (Cloud Cepat)',
        provider: 'gemini',
        model: 'gemini-2.5-flash',
        base_url: '',
        api_key: settings.gemini_api_key || '',
        is_active: true,
      };
    } else {
      const found = existingList.find((a) => a.provider === 'openrouter');
      profileAcc = found || {
        id: 'acc_openrouter_gw',
        name: 'OpenRouter Multi-Model Gateway',
        provider: 'openrouter',
        model: 'google/gemini-2.0-flash-001',
        base_url: 'https://openrouter.ai/api/v1',
        api_key: settings.openrouter_api_key || '',
        is_active: true,
      };
    }

    const existsInList = existingList.some((a) => a.id === profileAcc.id);
    const nextAccounts = (existsInList ? existingList : [profileAcc, ...existingList]).map((a) => ({
      ...a,
      is_active: a.id === profileAcc.id,
    }));

    const updatedSettings: Settings = {
      ...settings,
      active_account_id: profileAcc.id,
      ai_accounts: nextAccounts,
      ai_provider: profileAcc.provider,
      ai_model: profileAcc.model,
      custom_base_url: profileAcc.base_url || 'http://127.0.0.1:11434/v1',
      custom_api_key: profileAcc.provider === 'custom' ? (profileAcc.api_key || 'local-airgap') : settings.custom_api_key,
    };

    setSettings(updatedSettings);
    try {
      await waitForPyWebView();
      await api.save_settings(updatedSettings);
      setSaveMessage(`Profil Kesiapan "${profileAcc.name}" diaktifkan!`);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal menerapkan profil: ' + err?.message);
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
    };

    setSettings(updatedSettings);
    try {
      await waitForPyWebView();
      await api.save_settings(updatedSettings);
      setSaveMessage(`Profil "${account.name}" berhasil diaktifkan untuk seluruh operasi!`);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal mengaktifkan akun: ' + err?.message);
    }
  };

  const openAddForm = () => {
    setEditingId(null);
    setAccountForm({
      name: `Profil AI #${(settings.ai_accounts?.length || 0) + 1}`,
      provider: 'custom',
      model: 'qwen2.5:7b',
      base_url: 'http://127.0.0.1:11434/v1',
      api_key: 'local-airgap',
    });
    setIsFormOpen(true);
  };

  const openEditForm = (acc: AIAccountProfile) => {
    setEditingId(acc.id);
    setAccountForm({
      name: acc.name,
      provider: acc.provider === 'edgeone' ? 'custom' : acc.provider,
      model: acc.model,
      base_url: acc.base_url || (acc.provider === 'custom' ? 'http://127.0.0.1:11434/v1' : ''),
      api_key: acc.api_key || '',
    });
    setIsFormOpen(true);
  };

  const handleSaveAccountForm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accountForm.name.trim()) {
      alert('Nama profil tidak boleh kosong.');
      return;
    }
    if (!accountForm.model.trim()) {
      alert('Model Identifier tidak boleh kosong.');
      return;
    }

    let updatedList = [...(settings.ai_accounts || [])];

    if (editingId) {
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
      setSaveMessage(editingId ? 'Profil AI berhasil diperbarui!' : 'Profil AI baru berhasil ditambahkan!');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal menyimpan profil: ' + err?.message);
    }
  };

  const handleDeleteAccount = async (accId: string) => {
    if ((settings.ai_accounts || []).length <= 1) {
      alert('Minimal harus ada 1 profil AI tersimpan.');
      return;
    }
    if (!confirm('Apakah Anda yakin ingin menghapus profil AI ini?')) return;

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
      setSaveMessage('Profil berhasil dihapus.');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal menghapus profil: ' + err?.message);
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
      setSaveMessage('Konfigurasi sistem berhasil disimpan!');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert('Gagal menyimpan pengaturan: ' + err?.message);
    }
  };

  const isLocalAirGapActive =
    settings.ai_provider === 'custom' &&
    ((settings.custom_base_url || '').includes('127.0.0.1') || (settings.custom_base_url || '').includes('localhost'));

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Page Header */}
      <div>
        <h1 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
          5. Konfigurasi Sistem & Profil Kesiapan AI
        </h1>
        <p style={{ fontSize: '0.84rem', color: '#94a3b8', marginTop: '2px' }}>
          Dukungan penuh operasi Intranet Militer Air-Gapped (Ollama / vLLM Lokal tanpa internet) maupun Cloud API Kecepatan Tinggi.
        </p>
      </div>

      {/* ========================================================= */}
      {/* PROFIL KESIAPAN OPERASI (1-CLICK READINESS PROFILES)      */}
      {/* ========================================================= */}
      <div className="panel panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={18} color="#10b981" />
          <span>Preset Cepat Profil Kesiapan Operasi (1-Klik Aktivasi)</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
          {/* Card 1: Intranet Air-Gapped */}
          <button
            type="button"
            onClick={() => applyOperationalReadinessProfile('airgap')}
            style={{
              textAlign: 'left',
              padding: '14px',
              borderRadius: '10px',
              background: isLocalAirGapActive ? 'rgba(16, 185, 129, 0.14)' : 'rgba(15, 23, 42, 0.7)',
              border: isLocalAirGapActive ? '2px solid #10b981' : '1px solid rgba(51, 65, 85, 0.6)',
              cursor: 'pointer',
              color: '#f8fafc',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', fontWeight: 700, color: '#34d399' }}>
                <WifiOff size={15} /> 1. Mode Intranet / Air-Gapped
              </span>
              {isLocalAirGapActive && <span style={{ fontSize: '0.65rem', background: '#10b981', color: '#052e16', fontWeight: 800, padding: '2px 6px', borderRadius: '8px' }}>AKTIF</span>}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#cbd5e1', lineHeight: 1.4 }}>
              Endpoint lokal <code>http://127.0.0.1:11434/v1</code> (Ollama / vLLM). 100% kedaulatan data di jaringan tertutup tanpa API key eksternal.
            </div>
          </button>

          {/* Card 2: Google Gemini Official */}
          <button
            type="button"
            onClick={() => applyOperationalReadinessProfile('gemini')}
            style={{
              textAlign: 'left',
              padding: '14px',
              borderRadius: '10px',
              background: settings.ai_provider === 'gemini' ? 'rgba(2, 132, 199, 0.14)' : 'rgba(15, 23, 42, 0.7)',
              border: settings.ai_provider === 'gemini' ? '2px solid #0284c7' : '1px solid rgba(51, 65, 85, 0.6)',
              cursor: 'pointer',
              color: '#f8fafc',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8' }}>
                <Cloud size={15} /> 2. Google Gemini Official
              </span>
              {settings.ai_provider === 'gemini' && <span style={{ fontSize: '0.65rem', background: '#0284c7', color: '#fff', fontWeight: 800, padding: '2px 6px', borderRadius: '8px' }}>AKTIF</span>}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#cbd5e1', lineHeight: 1.4 }}>
              Model <code>gemini-2.5-flash</code> resmi kecepatan tinggi untuk pemrosesan korpus OSINT publik skala besar.
            </div>
          </button>

          {/* Card 3: OpenRouter Gateway */}
          <button
            type="button"
            onClick={() => applyOperationalReadinessProfile('openrouter')}
            style={{
              textAlign: 'left',
              padding: '14px',
              borderRadius: '10px',
              background: settings.ai_provider === 'openrouter' ? 'rgba(168, 85, 247, 0.14)' : 'rgba(15, 23, 42, 0.7)',
              border: settings.ai_provider === 'openrouter' ? '2px solid #a855f7' : '1px solid rgba(51, 65, 85, 0.6)',
              cursor: 'pointer',
              color: '#f8fafc',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', fontWeight: 700, color: '#c084fc' }}>
                <Globe size={15} /> 3. OpenRouter Multi-Model
              </span>
              {settings.ai_provider === 'openrouter' && <span style={{ fontSize: '0.65rem', background: '#a855f7', color: '#fff', fontWeight: 800, padding: '2px 6px', borderRadius: '8px' }}>AKTIF</span>}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#cbd5e1', lineHeight: 1.4 }}>
              Gateway fleksibel untuk memilih Qwen 2.5 72B, Llama 3.3 70B, atau Gemini Flash melalui satu API key.
            </div>
          </button>
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
            <span>Daftar Profil Endpoint AI Tersimpan</span>
            <span style={{ fontSize: '0.75rem', background: 'rgba(2, 132, 199, 0.2)', color: '#38bdf8', padding: '2px 8px', borderRadius: '12px', border: '1px solid rgba(2, 132, 199, 0.4)' }}>
              {settings.ai_accounts?.length || 0} Profil
            </span>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={openAddForm}
            style={{ fontSize: '0.8rem', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Plus size={15} />
            <span>+ Tambah Profil Endpoint AI</span>
          </button>
        </div>

        {/* List of Account Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '12px' }}>
          {(settings.ai_accounts || []).map((acc, idx) => {
            const isActive = acc.id === settings.active_account_id;
            const testStatus = accountTestStatus[acc.id];
            const isLocal = acc.provider === 'custom' && ((acc.base_url || '').includes('127.0.0.1') || (acc.base_url || '').includes('localhost'));

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
                          MODE: <strong style={{ color: '#38bdf8' }}>{isLocal ? 'LOCAL AIR-GAPPED' : acc.provider}</strong>
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
                        }}
                      >
                        Aktifkan Profil
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
                        <span style={{ color: '#94a3b8' }} title={acc.base_url}>{acc.base_url}</span>
                      </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.7rem' }}>
                      <span>Otentikasi:</span>
                      <span style={{ color: (acc.api_key || isLocal) ? '#10b981' : '#f87171' }}>
                        {isLocal ? 'Intranet Lokal (Tanpa Key)' : (acc.api_key ? `Tersimpan (•••${acc.api_key.slice(-4)})` : 'Belum diisi')}
                      </span>
                    </div>
                  </div>

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

                {/* Card Actions */}
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
                    <span>{testStatus?.testing ? 'Menguji...' : 'Uji Koneksi & Latensi'}</span>
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
                <span>{editingId ? 'Edit Profil Endpoint AI' : 'Tambah Profil Endpoint AI Baru'}</span>
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
                  <label className="form-label">Nama / Label Profil *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={accountForm.name}
                    onChange={(e) => setAccountForm({ ...accountForm, name: e.target.value })}
                    placeholder="misal: Server Intranet Puskodal (Ollama)"
                    required
                  />
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">Arsitektur Provider AI</label>
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
                        defaultModel = 'qwen2.5:7b';
                        defaultUrl = 'http://127.0.0.1:11434/v1';
                      }
                      setAccountForm({
                        ...accountForm,
                        provider: val,
                        model: defaultModel,
                        base_url: defaultUrl,
                      });
                    }}
                  >
                    <option value="custom">Intranet Lokal Air-Gapped / OpenAI-Compatible (Ollama, vLLM, LM Studio)</option>
                    <option value="gemini">Google Gemini Direct (Resmi)</option>
                    <option value="openrouter">OpenRouter Multi-Model Gateway</option>
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
                  placeholder="misal: qwen2.5:7b atau gemini-2.5-flash"
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
                        base_url: p.base_url,
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
                  <label className="form-label">Endpoint Base URL (Intranet / Local Server)</label>
                  <input
                    type="text"
                    className="form-input mono-font"
                    value={accountForm.base_url}
                    onChange={(e) => setAccountForm({ ...accountForm, base_url: e.target.value })}
                    placeholder="http://127.0.0.1:11434/v1"
                  />
                  <span style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '3px', display: 'block' }}>
                    Standar Air-Gapped: <code>http://127.0.0.1:11434/v1</code> (Ollama) atau <code>http://localhost:8000/v1</code> (vLLM).
                  </span>
                </div>
              )}

              {/* API Key */}
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">API Key (Opsional untuk Server Lokal Intranet)</label>
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                  <input
                    type={showKeys['form_key'] ? 'text' : 'password'}
                    className="form-input mono-font"
                    placeholder="Kosongkan jika menggunakan Ollama/vLLM lokal..."
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
                  <span>{editingId ? 'Simpan Perubahan' : 'Tambahkan Profil'}</span>
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
          <span>Parameter Akuisisi & Verifikasi Otonom</span>
        </div>

        {/* YouTube API Key */}
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">YouTube Data API v3 Key (Opsional)</label>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <input
              type={showKeys['youtube'] ? 'text' : 'password'}
              className="form-input mono-font"
              placeholder="AIzaSy... (Kosongkan untuk memakai ekstraktor web langsung / mode offline)"
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
            Jika dibiarkan kosong, sistem otomatis menggunakan ekstraktor tanpa kuota atau mode korpus lokal offline.
          </span>
        </div>

        {/* Hardened Gates */}
        <div style={{ borderTop: '1px solid rgba(51, 65, 85, 0.4)', paddingTop: '14px' }}>
          <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={16} color="#10b981" />
            <span>4 Agentic AI Hardened Verification Gates</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '10px' }}>
            Menjalankan audit silang otonom & self-healing bebas halusinasi (Gate 1: Quality Gate, Gate 2: Topic Gate, Gate 3: Verification Gate, Gate 4: Report Gate).
          </p>

          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <input
              type="checkbox"
              checked={settings.agentic_gates_enabled}
              onChange={(e) => setSettings({ ...settings, agentic_gates_enabled: e.target.checked })}
            />
            Aktifkan 4 Agentic Verification Gates Selama Operasi (Standar Forensik PUSSIBERAD)
          </label>
        </div>

        <div style={{ borderTop: '1px solid rgba(51, 65, 85, 0.4)', paddingTop: '14px', display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" className="btn btn-primary" style={{ padding: '9px 24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Save size={16} />
            <span>Simpan Konfigurasi Sistem</span>
          </button>
        </div>
      </form>
    </div>
  );
};
