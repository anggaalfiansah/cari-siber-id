export interface AIAccountProfile {
  id: string;
  name: string;
  provider: string;
  model: string;
  base_url?: string;
  api_key?: string;
  is_active?: boolean;
}

export interface Settings {
  ai_provider: string;
  ai_model: string;
  active_account_id?: string;
  ai_accounts?: AIAccountProfile[];
  gemini_api_key?: string;
  openrouter_api_key?: string;
  edgeone_api_key?: string;
  custom_base_url?: string;
  custom_api_key?: string;
  youtube_api_key?: string;
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
  file_uri?: string;
  data_uri?: string;
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

export interface AuthorCommentItem {
  comment_id: string;
  comment_text: string;
  like_count: number;
  reply_count: number;
  ai_sentiment: string;
  topic_name?: string;
  business_category?: string;
  sub_issue?: string;
  video_id?: string;
  video_title?: string;
  created_at?: string;
  is_reply?: boolean;
  is_hearted?: boolean;
  is_pinned?: boolean;
}

export interface FlaggedAccountItem {
  username: string;
  author_channel_id: string;
  author_channel_url: string;
  avatar?: string;
  videos_count: number;
  total_comments: number;
  total_likes_received?: number;
  total_replies_received?: number;
  target_video_ids: string[];
  target_video_titles: string[];
  sample_comments: string[];
  all_comments: AuthorCommentItem[];
  cib_risk_level: 'SUSPICIOUS' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  threat_tags?: string[];
  inauthenticity_score?: number;
  bot_score?: number;
  provocation_score?: number;
  actor_type?: 'PROVOCATEUR_HIGH_IMPACT' | 'PROVOCATEUR_AGITATOR' | 'BUZZER_COORDINATED' | 'SPAM_BOT' | 'HYBRID_THREAT' | 'COORDINATED_BOT_NETWORK';
  actor_label?: string;
  detected_keywords?: string[];
  is_coordinated_bot?: boolean;
  coordinated_peer_count?: number;
  score_breakdown?: {
    copypasta?: number;
    cross_video?: number;
    temporal?: number;
    dialogue?: number;
    network?: number;
    prov_lexicon?: number;
    prov_thread?: number;
    prov_resonance?: number;
    prov_sentiment?: number;
  };
  sentiment_breakdown?: { Positif: number; Netral: number; Negatif: number };
}

export interface CrossVideoBuzzer {
  username: string;
  author_channel_id: string;
  author_channel_url: string;
  videos_count: number;
  total_comments: number;
  total_likes_received?: number;
  target_video_ids: string[];
  target_video_titles: string[];
  sample_comments: string[];
  all_comments?: AuthorCommentItem[];
  cib_risk_level: 'SUSPICIOUS' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  threat_tags?: string[];
  inauthenticity_score?: number;
  score_breakdown?: {
    copypasta: number;
    cross_video: number;
    temporal: number;
    dialogue: number;
  };
  sentiment_breakdown?: { Positif: number; Netral: number; Negatif: number };
}

export interface VideoComparisonRow {
  video_id: string;
  video_title: string;
  channel_name: string;
  total_comments: number;
  unique_commenters: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  net_sentiment: number;
  top_topic: string;
  cib_score: number;
}

export interface CrossVideoIntelligence {
  is_multi_video: boolean;
  total_videos: number;
  total_comments: number;
  unique_authors_overall: number;
  shared_authors_count: number;
  sentiment_divergence_score: number;
  audience_overlap_ratio: number;
  cross_video_buzzers: CrossVideoBuzzer[];
  flagged_accounts?: FlaggedAccountItem[];
  video_comparison_matrix: VideoComparisonRow[];
}

export interface TelemetryInfo {
  ai_provider: string;
  ai_model: string;
  total_duration_sec: number;
  duration_formatted: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  llm_calls_count: number;
}

export interface RunResult {
  meta: {
    video_title: string;
    channel_name: string;
    total_comments: number;
    unique_authors_total?: number;
    cib_score?: number;
    cib_level?: string;
    polarization_index?: number;
    run_dir: string;
    telemetry?: TelemetryInfo;
  };
  telemetry?: TelemetryInfo;
  cib_score?: number;
  cib_level?: string;
  polarization_index?: number;
  unique_authors_total?: number;
  cib_metrics?: any;
  polarization_metrics?: any;
  topics: TopicItem[];
  charts: ChartItem[];
  narrative_md: string;
  interactive_data: InteractiveData;
  flagged_accounts?: FlaggedAccountItem[];
  coordinated_bot_networks?: CoordinatedBotNetwork[];
  corpus_comments?: AuthorCommentItem[];
  cross_video?: CrossVideoIntelligence;
}

export interface CoordinatedBotNetwork {
  template_text: string;
  normalized_key: string;
  unique_accounts_count: number;
  total_occurrences: number;
  unique_videos_count: number;
  target_video_titles: string[];
  accounts: string[];
  coordination_level: 'CRITICAL_MASS' | 'HIGH_COORDINATION' | 'MEDIUM_COORDINATION';
  coordination_badge: string;
  sample_occurrences?: Array<{
    raw_text: string;
    username: string;
    video_title: string;
    created_at: string;
    like_count?: number;
  }>;
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

export interface CuratedVideoItem {
  video_id: string;
  url: string;
  title: string;
  channel: string;
  duration?: string;
  views?: string;
  published?: string;
  thumbnail?: string;
  relevance_score?: number;
  curation_reason?: string;
  is_recommended?: boolean;
}

export interface VideoDiscoveryResponse {
  success: boolean;
  keyword?: string;
  total_candidates_found?: number;
  curated_videos?: CuratedVideoItem[];
  error?: string;
}

export interface ReusableCorpus {
  run_id: string;
  created_at: string;
  comment_count: number;
  video_count: number;
  title: string;
  source_file: string;
  size_mb: number;
}


