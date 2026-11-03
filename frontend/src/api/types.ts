export interface Settings {
  ai_provider: string;
  ai_model: string;
  gemini_api_key?: string;
  openrouter_api_key?: string;
  edgeone_api_key?: string;
  custom_base_url?: string;
  custom_api_key?: string;
  agentic_gates_enabled: boolean;
  default_comment_limit: number;
  default_sort_by: string;
  default_include_replies: boolean;
}

export interface RunHistoryItem {
  id: string;
  target_url: string;
  video_title?: string;
  channel_name?: string;
  total_comments: number;
  cib_score: number;
  cib_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  polarization_index: number;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  error_message?: string;
  created_at: string;
  completed_at?: string;
  run_dir: string;
}

export interface TopicItem {
  topic_id: number;
  topic_name: string;
  category?: string;
  sub_issue?: string;
  keywords?: string;
  sentiment: string;
  total_comments: number;
  sample_comment: string;
}

export interface ChartItem {
  id: string;
  title: string;
  data_uri: string;
}

export interface InteractiveData {
  sentiment: Array<{ name: string; value: number; color: string }>;
  topics: Array<{
    topic: string;
    full_topic: string;
    category?: string;
    keywords?: string;
    count: number;
    sentiment: string;
  }>;
}

export interface RunResult {
  meta: {
    video_title: string;
    channel_name: string;
    total_comments: number;
    run_dir: string;
  };
  topics: TopicItem[];
  charts: ChartItem[];
  narrative_md: string;
  interactive_data: InteractiveData;
}

export interface ProgressEvent {
  type: 'progress';
  status: string;
  run_id?: string;
  step_index?: number;
  percent: number;
  step_name: string;
  message: string;
}

export interface LogEvent {
  type: 'log';
  line: string;
}

export interface CompletedEvent {
  type: 'completed';
  run_id: string;
  status: string;
  percent: number;
  step_name: string;
  message: string;
  summary: {
    video_title: string;
    channel_name: string;
    total_comments: number;
    cib_score: number;
    cib_level: string;
    polarization_index: number;
    sentiment_distribution: Record<string, number>;
  };
  result: RunResult;
}

export interface ErrorEvent {
  type: 'error';
  run_id?: string;
  status: string;
  message: string;
}

export type PyWebViewEvent = ProgressEvent | LogEvent | CompletedEvent | ErrorEvent;
