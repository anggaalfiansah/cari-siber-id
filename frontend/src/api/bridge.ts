import { Settings, RunHistoryItem, RunResult, PyWebViewEvent } from './types';

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
    ai_model: 'gemini-3.8-flash',
    gemini_api_key: 'mock-key',
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
};

export const api = new Proxy({} as any, {
  get: (_, prop: string) => {
    if (window.pywebview && window.pywebview.api && (window.pywebview.api as any)[prop]) {
      return (window.pywebview.api as any)[prop];
    }
    return (mockApi as any)[prop] || (async () => ({ success: false, error: 'API not ready' }));
  },
});
