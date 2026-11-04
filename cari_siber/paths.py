import os
import sys

def is_frozen() -> bool:
    """Returns True if running inside a PyInstaller frozen bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_app_dir() -> str:
    """Returns the base directory of the application bundle or repo."""
    if is_frozen():
        return sys._MEIPASS
    # Root of repo: two levels up from cari_siber/paths.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resources_dir() -> str:
    """Directory containing bundled static resources (dictionaries, stopwords, config)."""
    return os.path.join(get_app_dir(), "resources")


def get_ui_dist_dir() -> str:
    """Directory containing the compiled Vite/React static assets."""
    if is_frozen():
        return os.path.join(sys._MEIPASS, "cari_siber", "ui_dist")
    return os.path.join(get_app_dir(), "cari_siber", "ui_dist")


def get_models_dir() -> str:
    """Directory containing the bundled IndoBERT offline model."""
    if is_frozen():
        return os.path.join(sys._MEIPASS, "models")
    return os.path.join(get_app_dir(), "models")


def get_user_data_dir() -> str:
    """
    Writable user directory across platforms.
    - Windows: %LOCALAPPDATA%/CaRI-Siber-ID
    - macOS: ~/Library/Application Support/CaRI-Siber-ID
    - Linux: ~/.local/share/CaRI-Siber-ID
    Falls back to <app_dir>/.user_data if restricted (portable or dev mode).
    """
    candidate = None
    if sys.platform == "win32":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            candidate = os.path.join(local_app_data, "CaRI-Siber-ID")
    elif sys.platform == "darwin":
        candidate = os.path.expanduser("~/Library/Application Support/CaRI-Siber-ID")
    else:
        candidate = os.path.expanduser("~/.local/share/CaRI-Siber-ID")

    if candidate:
        try:
            os.makedirs(candidate, exist_ok=True)
            test_file = os.path.join(candidate, ".write_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            return candidate
        except Exception:
            pass

    # Fallback to local workspace / app directory
    fallback_dir = os.path.join(get_app_dir(), ".user_data")
    os.makedirs(fallback_dir, exist_ok=True)
    return fallback_dir


def get_history_db_path() -> str:
    return os.path.join(get_user_data_dir(), "history.db")


def get_settings_json_path() -> str:
    return os.path.join(get_user_data_dir(), "settings.json")


def get_user_learned_slang_path() -> str:
    return os.path.join(get_user_data_dir(), "kamus-alay-learned.csv")


def get_user_custom_stopwords_path() -> str:
    return os.path.join(get_user_data_dir(), "stopwords.txt")


def get_logs_dir() -> str:
    logs_dir = os.path.join(get_user_data_dir(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def get_run_dir(run_id: str) -> str:
    runs_dir = os.path.join(get_user_data_dir(), "runs", run_id)
    os.makedirs(runs_dir, exist_ok=True)
    return runs_dir
