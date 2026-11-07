import os
import re
from cari_siber.paths import get_user_data_dir, get_resources_dir

def _slugify(text: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', text).strip('_').lower()
    return re.sub(r'_+', '_', slug)

def extract_youtube_video_id(url_or_id: str) -> str:
    """
    Mengekstrak 11 karakter Video ID dari berbagai format URL YouTube:
    watch?v=, youtu.be/, shorts/, embed/, live/, atau ID mentah.
    Mengembalikan string kosong jika tidak dikenali.
    """
    if not url_or_id:
        return ""
    text = url_or_id.strip()
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', text):
        return text
    patterns = [
        r'[?&]v=([A-Za-z0-9_-]{11})',
        r'youtu\.be/([A-Za-z0-9_-]{11})',
        r'/(?:shorts|embed|live|v)/([A-Za-z0-9_-]{11})',
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            return match.group(1)
    # Fallback untuk ID korpus simulasi/impor (mis. watch?v=TNI_PATROLI_01 atau SIBER_PERTAHANAN_01)
    sim_match = re.search(r'[?&]v=([A-Za-z0-9_-]{3,40})', text)
    if sim_match:
        return sim_match.group(1)
    if re.fullmatch(r'[A-Za-z0-9_-]{3,40}', text) and not text.startswith(("http", "www", "demo")):
        return text
    return ""


class AppConfig:
    """
    Kelas Konfigurasi Utama untuk CaRI-Siber ID Desktop.
    Mendukung isolasi run_dir dinamis per analisis agar riwayat tidak tertimpa.
    """
    
    # 1. API Keys & Credentials
    GEMINI_API_KEY = ""
    OPENROUTER_API_KEY = ""
    EDGEONE_API_KEY = ""
    CUSTOM_API_KEY = ""
    CUSTOM_BASE_URL = "http://127.0.0.1:11434/v1"
    
    # 2. Target Config
    TARGET_PLATFORM = "youtube"
    TARGET_URL = ""
    
    YOUTUBE_API_KEY = ""
    YOUTUBE_VIDEO_URL = ""
    YOUTUBE_VIDEO_URLS = []
    YOUTUBE_VIDEO_ID = ""
    SEARCH_KEYWORD = ""
    YOUTUBE_APP_NAME = "YouTube Video"
    YOUTUBE_APP_DESC = "Komentar video YouTube"
    YOUTUBE_LIMIT_COMMENTS = 1000
    YOUTUBE_SORT = "top"
    YOUTUBE_INCLUDE_REPLIES = True
    
    # 3. Direktori Output Default
    OUTPUT_DIR = os.path.join(get_user_data_dir(), "output")
    OUTPUT_YOUTUBE_DIR = os.path.join(OUTPUT_DIR, "youtube")
    OUTPUT_TIKTOK_DIR = os.path.join(OUTPUT_DIR, "tiktok")
    OUTPUT_APP_REVIEWS_DIR = os.path.join(OUTPUT_DIR, "app_reviews")
    
    # 4. Pengaturan AI Model
    ACTIVE_AI_PROVIDER = "gemini"
    ACTIVE_AI_MODEL = "gemini-2.5-flash"
    AI_PROVIDER = "gemini"
    AI_MODEL = "gemini-2.5-flash"
    AI_OVERWRITE = True
    AI_NARRATION_MODEL = ""
    
    # 5. Pengaturan EDA & Visualisasi
    EDA_TOP_N = 10
    EDA_USE_WORDCLOUD = True
    
    # 6. Pengaturan Export Laporan (Hanya XLSX aktif)
    EXPORT_XLSX = True
    EXPORT_PDF = False
    EXPORT_PPTX = False
    EXPORT_HTML = False

    # 7. Pengaturan Agentic AI Hardened Gates
    AGENTIC_GATES_ENABLED = True
    AGENTIC_MAX_RETRIES = 2
    AGENTIC_QUALITY_MIN_WORDS = 2
    AGENTIC_TOPIC_MAX_OUTLIER_RATIO = 0.35
    AGENTIC_TOPIC_MAX_SIMILARITY = 0.85
    AGENTIC_VERIFY_MIN_CONFIDENCE_RATE = 0.70
    AGENTIC_VERIFY_LLM_REROUTE_BATCH = 30

    @classmethod
    def configure_run(
        cls,
        run_dir: str,
        settings: dict = None,
        video_url: str = "",
        video_urls: list = None,
        limit_comments: int = 1000,
        sort_by: str = "top",
        include_replies: bool = True,
        search_keyword: str = "",
    ):
        """Mengonfigurasi state engine untuk satu sesi pengerjaan analisis terisolasi."""
        os.makedirs(run_dir, exist_ok=True)
        cls.OUTPUT_DIR = run_dir
        cls.OUTPUT_YOUTUBE_DIR = run_dir
        cls.OUTPUT_TIKTOK_DIR = run_dir
        cls.OUTPUT_APP_REVIEWS_DIR = run_dir

        resolved_urls = []
        if video_urls and isinstance(video_urls, list):
            resolved_urls = [str(u).strip() for u in video_urls if str(u).strip()]
        elif video_url and str(video_url).strip():
            resolved_urls = [str(video_url).strip()]

        cls.YOUTUBE_VIDEO_URLS = resolved_urls
        primary_url = resolved_urls[0] if resolved_urls else (video_url or "")
        cls.TARGET_URL = primary_url
        cls.TARGET_PLATFORM = "youtube"
        cls.SEARCH_KEYWORD = str(search_keyword or "").strip()

        cls.YOUTUBE_VIDEO_URL = primary_url
        cls.YOUTUBE_VIDEO_ID = extract_youtube_video_id(primary_url)
        if len(resolved_urls) > 1:
            if cls.SEARCH_KEYWORD:
                cls.YOUTUBE_APP_NAME = f"Isu Pencarian: {cls.SEARCH_KEYWORD} ({len(resolved_urls)} Video)"
                cls.YOUTUBE_APP_DESC = f"Koleksi {len(resolved_urls)} video YouTube untuk kata kunci '{cls.SEARCH_KEYWORD}'"
            else:
                cls.YOUTUBE_APP_NAME = f"Korpus Multi-Video ({len(resolved_urls)} Video)"
                cls.YOUTUBE_APP_DESC = f"Koleksi {len(resolved_urls)} video YouTube"
        else:
            cls.YOUTUBE_APP_NAME = f"YouTube - {cls.YOUTUBE_VIDEO_ID}" if cls.YOUTUBE_VIDEO_ID else "YouTube Video"
            cls.YOUTUBE_APP_DESC = "Komentar video YouTube"

        cls.YOUTUBE_LIMIT_COMMENTS = limit_comments
        cls.YOUTUBE_SORT = sort_by
        cls.YOUTUBE_INCLUDE_REPLIES = include_replies

        if settings:
            cls.ACTIVE_AI_PROVIDER = settings.get("ai_provider", "gemini")
            cls.ACTIVE_AI_MODEL = settings.get("ai_model", "gemini-2.5-flash")
            cls.AI_PROVIDER = cls.ACTIVE_AI_PROVIDER
            cls.AI_MODEL = cls.ACTIVE_AI_MODEL

            cls.GEMINI_API_KEY = settings.get("gemini_api_key", "").strip()
            cls.OPENROUTER_API_KEY = settings.get("openrouter_api_key", "").strip()
            cls.EDGEONE_API_KEY = settings.get("edgeone_api_key", "").strip()
            cls.CUSTOM_API_KEY = settings.get("custom_api_key", "").strip()
            cls.CUSTOM_BASE_URL = settings.get("custom_base_url", "http://127.0.0.1:11434/v1").strip()
            cls.YOUTUBE_API_KEY = settings.get("youtube_api_key", "").strip()
            cls.AGENTIC_GATES_ENABLED = bool(settings.get("agentic_gates_enabled", True))

    @classmethod
    def get_csv_output_dir(cls):
        path = os.path.join(cls.OUTPUT_DIR, "csv")
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_json_output_dir(cls):
        path = os.path.join(cls.OUTPUT_DIR, "json")
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_charts_output_dir(cls):
        path = os.path.join(cls.OUTPUT_DIR, "charts")
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_reports_output_dir(cls):
        path = os.path.join(cls.OUTPUT_DIR, "reports")
        os.makedirs(path, exist_ok=True)
        return path


Config = AppConfig
