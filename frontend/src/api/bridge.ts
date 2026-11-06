import { Settings, RunHistoryItem, RunResult, PyWebViewEvent, VideoDiscoveryResponse } from './types';

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
    ai_provider: 'gemini',
    ai_model: 'gemini-2.5-flash',
    gemini_api_key: 'mock-key',
    youtube_api_key: '',
    agentic_gates_enabled: true,
    default_comment_limit: 1000,
    default_sort_by: 'top',
    default_include_replies: true,
  }),
  save_settings: async () => ({ success: true, message: 'Mock save success' }),
  test_ai_connection: async () => ({ success: true, message: 'Mock connection OK' }),
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
        title: `Debat Hangat Terkait ${keyword || 'Isu Terkini'}`,
        channel: 'Kanal Berita Nasional',
        duration: '14:20',
        views: '240 rb x ditonton',
        published: '2 hari yang lalu',
        thumbnail: 'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=600&auto=format&fit=crop&q=60',
        relevance_score: 95,
        curation_reason: 'Diskusi panelis resmi dengan volume komentar publik dan perdebatan argumentatif tinggi.',
        is_recommended: true,
      },
      {
        video_id: 'mock2',
        url: 'https://www.youtube.com/watch?v=mock2',
        title: `Kupas Tuntas Dampak dan Polemik ${keyword || 'Kebijakan'}`,
        channel: 'Forum Investigasi Siber',
        duration: '22:15',
        views: '110 rb x ditonton',
        published: '5 hari yang lalu',
        thumbnail: 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&auto=format&fit=crop&q=60',
        relevance_score: 88,
        curation_reason: 'Memuat sudut pandang kontra-narasi dan polarisasi opini akar rumput.',
        is_recommended: false,
      },
    ],
  }),
    get_ai_threat_calibration: async (payload: { run_id: string }) => ({
    success: true,
    whitelist_recommendations: ['TNI Bersama Rakyat', 'Terimakasih tni', 'Bravo TNI', 'NKRI Harga Mati'],
    hostile_threat_keywords: ['papua merdeka', 'opm', 'kkb', 'pemberontak'],
    reasoning_summary: 'Sistem merekomendasikan whitelist slogan resmi TNI dan apresiasi masyarakat agar tidak terjadi salah tuduh (False Positive). Frasa separatis dan provokasi ditandai sebagai ancaman.',
  }),
  reanalyze_intelligence: async (payload: { run_id: string; whitelist: string[]; threats: string[] }) => ({
    success: true,
    message: 'Analisis intelijen siber berhasil diperbarui seketika.',
    bot_networks_count: 5,
    flagged_accounts_count: 12,
  }),
  list_reusable_corpora: async () => [
    {
      run_id: '20261106_103448_4004e2',
      created_at: '2026-11-06 10:34:48',
      comment_count: 10281,
      video_count: 100,
      title: '100 Video YouTube Terkurasi (10,281 Komentar)',
      source_file: 'youtube_comments_video_GpqlN-SBFqo.csv',
      size_mb: 4.8,
    },
  ],
};

export const api = new Proxy({} as any, {
  get: (_, prop: string) => {
    if (window.pywebview && window.pywebview.api && (window.pywebview.api as any)[prop]) {
      return (window.pywebview.api as any)[prop];
    }
    return (mockApi as any)[prop] || (async () => ({ success: false, error: 'API not ready' }));
  },
});
