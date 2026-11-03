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
    return ""

def extract_instagram_shortcode(url_or_id: str) -> str:
    """
    Mengekstrak shortcode Instagram (biasanya 9-14 karakter) dari URL postingan atau reel:
    https://www.instagram.com/p/{shortcode}/
    https://www.instagram.com/reel/{shortcode}/
    https://www.instagram.com/reels/{shortcode}/
    https://instagr.am/p/{shortcode}/
    atau shortcode langsung.
    """
    if not url_or_id:
        return ""
    text = url_or_id.strip().split("?")[0].rstrip("/")
    match = re.search(r'instagram\.com/(?:p|reel|reels)/([A-Za-z0-9_-]+)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    match_short = re.search(r'instagr\.am/(?:p|reel|reels)/([A-Za-z0-9_-]+)', text, re.IGNORECASE)
    if match_short:
        return match_short.group(1)
    match_direct = re.search(r'/(?:p|reel|reels)/([A-Za-z0-9_-]+)', text, re.IGNORECASE)
    if match_direct:
        return match_direct.group(1)
    if ("http" not in text) and re.fullmatch(r'[A-Za-z0-9_-]{9,15}', text):
        return text
    return ""

def detect_target_platform(url_or_id: str) -> str:
    """
    Mendeteksi platform media sosial dari URL/ID input: 'instagram' | 'youtube'
    """
    if not url_or_id:
        return "youtube"
    text = url_or_id.lower().strip()
    if "instagram.com" in text or "instagr.am" in text or "/reel/" in text or "/reels/" in text or "/p/" in text:
        return "instagram"
    return "youtube"


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
    CUSTOM_BASE_URL = "https://api.tokenai.id/v1"
    
    # 2. Target Config
    TARGET_PLATFORM = "youtube"  # 'youtube' | 'instagram'
    TARGET_URL = ""
    INSTAGRAM_SHORTCODE = ""
    INSTAGRAM_SESSION_USER = ""
    
    YOUTUBE_API_KEY = ""
    YOUTUBE_VIDEO_URL = ""
    YOUTUBE_VIDEO_ID = ""
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
    ACTIVE_AI_MODEL = "gemini-3.8-flash"
    AI_PROVIDER = "gemini"
    AI_MODEL = "gemini-3.8-flash"
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
    def configure_run(cls, run_dir: str, settings: dict = None, video_url: str = "", limit_comments: int = 1000, sort_by: str = "top", include_replies: bool = True):
        """Mengonfigurasi state engine untuk satu sesi pengerjaan analisis terisolasi."""
        os.makedirs(run_dir, exist_ok=True)
        cls.OUTPUT_DIR = run_dir
        cls.OUTPUT_YOUTUBE_DIR = run_dir
        cls.OUTPUT_TIKTOK_DIR = run_dir
        cls.OUTPUT_APP_REVIEWS_DIR = run_dir

        cls.TARGET_URL = video_url
        platform = detect_target_platform(video_url)
        cls.TARGET_PLATFORM = platform

        if platform == "instagram":
            shortcode = extract_instagram_shortcode(video_url)
            cls.INSTAGRAM_SHORTCODE = shortcode
            cls.YOUTUBE_VIDEO_URL = video_url
            cls.YOUTUBE_VIDEO_ID = shortcode or "instagram_post"
            cls.YOUTUBE_APP_NAME = f"Instagram - {shortcode}" if shortcode else "Instagram Post"
            cls.YOUTUBE_APP_DESC = "Komentar postingan/reels Instagram"
        else:
            cls.YOUTUBE_VIDEO_URL = video_url
            cls.YOUTUBE_VIDEO_ID = extract_youtube_video_id(video_url)
            cls.YOUTUBE_APP_NAME = f"YouTube - {cls.YOUTUBE_VIDEO_ID}" if cls.YOUTUBE_VIDEO_ID else "YouTube Video"
            cls.YOUTUBE_APP_DESC = "Komentar video YouTube"

        cls.YOUTUBE_LIMIT_COMMENTS = limit_comments
        cls.YOUTUBE_SORT = sort_by
        cls.YOUTUBE_INCLUDE_REPLIES = include_replies

        if settings:
            cls.ACTIVE_AI_PROVIDER = settings.get("ai_provider", "gemini")
            cls.ACTIVE_AI_MODEL = settings.get("ai_model", "gemini-3.8-flash")
            cls.AI_PROVIDER = cls.ACTIVE_AI_PROVIDER
            cls.AI_MODEL = cls.ACTIVE_AI_MODEL

            cls.GEMINI_API_KEY = settings.get("gemini_api_key", "").strip()
            cls.OPENROUTER_API_KEY = settings.get("openrouter_api_key", "").strip()
            cls.EDGEONE_API_KEY = settings.get("edgeone_api_key", "").strip()
            cls.CUSTOM_API_KEY = settings.get("custom_api_key", "").strip()
            cls.CUSTOM_BASE_URL = settings.get("custom_base_url", "https://api.tokenai.id/v1").strip()
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
