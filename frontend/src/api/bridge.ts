import { Settings, RunHistoryItem, RunResult, PyWebViewEvent, VideoDiscoveryResponse, ImportCorpusResponse } from './types';

declare global {
  interface Window {
    pywebview?: {
      api: {
        get_settings: () => Promise<Settings>;
        save_settings: (s: Settings) => Promise<{ success: boolean; message?: string }>;
        test_ai_connection: (s: Settings) => Promise<{ success: boolean; message: string }>;
        start_run: (payload: any) => Promise<{ success: boolean; run_id?: string; error?: string }>;
        cancel_run: () => Promise<{ success: boolean }>;
        is_runner_busy: () => Promise<boolean>;
        list_history: () => Promise<RunHistoryItem[]>;
        get_run: (id: string) => Promise<RunHistoryItem | null>;
        get_run_results: (id: string) => Promise<RunResult | null>;
        delete_history: (id: string) => Promise<{ success: boolean }>;
        export_xlsx: (id: string) => Promise<{ success: boolean; path?: string; error?: string }>;
        open_folder: (id: string) => Promise<{ success: boolean; error?: string }>;
        get_author_comments: (payload: { run_id: string; author_key: string }) => Promise<{ success: boolean; comments?: any[]; error?: string }>;
        search_and_curate_videos: (payload: { keyword: string; max_curated?: number }) => Promise<VideoDiscoveryResponse>;
        list_reusable_corpora: () => Promise<any[]>;
        import_external_corpus: (payload: { filename: string; content_base64?: string; content_text?: string; title?: string }) => Promise<ImportCorpusResponse>;
        get_ai_threat_calibration: (payload: { run_id: string }) => Promise<any>;
        reanalyze_intelligence: (payload: { run_id: string; whitelist: string[]; threats: string[] }) => Promise<any>;
        regenerate_narrative: (payload: { run_id: string }) => Promise<{ success: boolean; narrative_md?: string; message?: string; error?: string }>;
      };
    };
    __cariEmit?: (event: PyWebViewEvent) => void;
  }
}

type EventListener = (event: PyWebViewEvent) => void;
const listeners: EventListener[] = [];

// Setup global listener hook called from Python window.evaluate_js
window.__cariEmit = (event: PyWebViewEvent) => {
  listeners.forEach((fn) => {
    try {
      fn(event);
    } catch (e) {
      console.error('Error in PyWebView event listener:', e);
    }
  });
};

export function subscribePyWebViewEvents(listener: EventListener): () => void {
  listeners.push(listener);
  return () => {
    const idx = listeners.indexOf(listener);
    if (idx !== -1) listeners.splice(idx, 1);
  };
}

export function waitForPyWebView(): Promise<boolean> {
  if (window.pywebview && window.pywebview.api) {
    return Promise.resolve(true);
  }
  return new Promise((resolve) => {
    const onReady = () => {
      window.removeEventListener('pywebviewready', onReady);
      resolve(true);
    };
    window.addEventListener('pywebviewready', onReady);
    // Timeout fallback for local browser development
    setTimeout(() => resolve(false), 2000);
  });
}

// Fallback Mock API if run in regular browser without pywebview
const mockApi = {
  get_settings: async (): Promise<Settings> => ({
    ai_provider: 'custom',
    ai_model: 'qwen2.5:7b',
    custom_base_url: 'http://127.0.0.1:11434/v1',
    gemini_api_key: '',
    youtube_api_key: '',
    agentic_gates_enabled: true,
    default_comment_limit: 1000,
    default_sort_by: 'top',
    default_include_replies: true,
  }),
  save_settings: async () => ({ success: true, message: 'Mock save success' }),
  test_ai_connection: async () => ({ success: true, message: 'Mock connection OK (Intranet Air-Gapped Ready)' }),
  start_run: async () => ({ success: true, run_id: 'mock_run_1' }),
  cancel_run: async () => ({ success: true }),
  is_runner_busy: async () => false,
  list_history: async (): Promise<RunHistoryItem[]> => [],
  get_run: async () => null,
  get_run_results: async () => null,
  delete_history: async () => ({ success: true }),
  export_xlsx: async () => ({ success: true, path: 'C:/mock/report.xlsx' }),
  open_folder: async () => ({ success: true }),
  get_author_comments: async () => ({ success: true, comments: [] }),
  search_and_curate_videos: async ({ keyword }: { keyword: string }): Promise<VideoDiscoveryResponse> => ({
    success: true,
    keyword,
    total_candidates_found: 12,
    curated_videos: [
      {
        video_id: 'mock1',
        url: 'https://www.youtube.com/watch?v=mock1',
        title: `Pemantauan Opini Ruang Siber: ${keyword || 'Operasi Pertahanan'}`,
        channel: 'Kanal Berita Nasional',
        duration: '14:20',
        views: '240 rb x ditonton',
        published: '2 hari yang lalu',
        thumbnail: 'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=600&auto=format&fit=crop&q=60',
        relevance_score: 95,
        curation_reason: 'Diskusi publik dengan volume interaksi dan dinamika narasi tinggi.',
        is_recommended: true,
      },
    ],
  }),
  get_ai_threat_calibration: async () => ({
    success: true,
    whitelist_recommendations: ['NKRI Harga Mati', 'Terima Kasih Petugas', 'Tetap Semangat'],
    hostile_threat_keywords: ['papua merdeka', 'opm', 'kkb', 'pemberontak', 'diretas'],
    reasoning_summary: 'Sistem merekomendasikan whitelist slogan kebangsaan dan apresiasi masyarakat agar tidak terjadi salah tuduh (False Positive). Frasa separatis dan provokasi ditandai sebagai ancaman.',
  }),
  reanalyze_intelligence: async () => ({
    success: true,
    message: 'Analisis intelijen siber berhasil diperbarui seketika.',
    bot_networks_count: 5,
    flagged_accounts_count: 12,
  }),
  list_reusable_corpora: async () => [
    {
      run_id: 'demo:sample_corpus_tni.csv',
      created_at: 'PRELOADED-SIMULASI',
      comment_count: 45,
      video_count: 3,
      title: '[SIMULASI OPERASI] Operasi Pengamanan Perbatasan & Bakti Sosial (3 Video Multi-CIB)',
      source_file: 'sample_corpus_tni.csv',
      size_mb: 0.02,
      sha256_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      is_demo: true,
    },
    {
      run_id: 'demo:sample_corpus_siber_ot.csv',
      created_at: 'PRELOADED-SIMULASI',
      comment_count: 17,
      video_count: 2,
      title: '[SIMULASI SIBER IT/OT] Pertahanan Siber & Mitigasi Hoaks Infrastruktur Kritis (2 Video)',
      source_file: 'sample_corpus_siber_ot.csv',
      size_mb: 0.01,
      sha256_hash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4',
      is_demo: true,
    },
  ],
  import_external_corpus: async ({ filename }: { filename: string }): Promise<ImportCorpusResponse> => ({
    success: true,
    run_id: 'import_mock_001',
    comment_count: 50,
    video_count: 1,
    title: `Impor Bukti Digital: ${filename}`,
    sha256_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    message: 'Berhasil mengimpor 50 bukti komentar.',
  }),
};

export const api = new Proxy({} as any, {
  get: (_, prop: string) => {
    if (window.pywebview && window.pywebview.api && (window.pywebview.api as any)[prop]) {
      return (window.pywebview.api as any)[prop];
    }
    return (mockApi as any)[prop] || (async () => ({ success: false, error: 'API not ready' }));
  },
});
