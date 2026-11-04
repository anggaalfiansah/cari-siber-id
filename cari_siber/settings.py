import os
import json
from typing import Dict, Any, Optional

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False

from cari_siber.paths import get_settings_json_path

SERVICE_NAME = "CaRI-Siber-ID"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "ai_provider": "gemini",
    "ai_model": "gemini-2.5-flash",
    "youtube_api_key": "",
    "custom_base_url": "https://api.tokenai.id/v1",
    "agentic_gates_enabled": True,
    "default_comment_limit": 1000,
    "default_sort_by": "top",
    "default_include_replies": True,
}


def _load_dotenv_fallback():
    """Memuat file .env lokal jika tersedia ke os.environ tanpa ketergantungan library luar."""
    search_dirs = [
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.getcwd(),
    ]
    for d in search_dirs:
        env_file = os.path.join(d, ".env")
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass
            break


class AppSettings:
    @staticmethod
    def load() -> Dict[str, Any]:
        """Loads non-secret settings and merges with secrets from keyring and environment."""
        _load_dotenv_fallback()
        settings = DEFAULT_SETTINGS.copy()
        json_path = get_settings_json_path()

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    settings.update(saved)
            except Exception as e:
                print(f"[WARNING] Gagal membaca settings.json: {e}")

        # Retrieve secret keys (prioritas: Keyring -> Environment -> saved settings)
        settings["gemini_api_key"] = AppSettings.get_secret("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "") or settings.get("gemini_api_key", "")
        settings["openrouter_api_key"] = AppSettings.get_secret("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "") or settings.get("openrouter_api_key", "")
        settings["edgeone_api_key"] = AppSettings.get_secret("EDGEONE_API_KEY") or os.environ.get("EDGEONE_API_KEY", "") or settings.get("edgeone_api_key", "")
        settings["custom_api_key"] = AppSettings.get_secret("CUSTOM_API_KEY") or os.environ.get("CUSTOM_API_KEY", "") or settings.get("custom_api_key", "")
        settings["youtube_api_key"] = AppSettings.get_secret("YOUTUBE_API_KEY") or os.environ.get("YOUTUBE_API_KEY", "") or settings.get("youtube_api_key", "")
        settings["custom_base_url"] = settings.get("custom_base_url", "https://api.tokenai.id/v1")
        return settings

    @staticmethod
    def save(new_settings: Dict[str, Any]) -> None:
        """Saves settings, securely storing API keys in Windows Credential Manager."""
        # 1. Extract and store secrets
        for key in ["gemini_api_key", "openrouter_api_key", "edgeone_api_key", "custom_api_key", "youtube_api_key"]:
            if key in new_settings:
                val = new_settings[key]
                if val:
                    AppSettings.set_secret(key.upper(), val)
                else:
                    AppSettings.delete_secret(key.upper())

        # 2. Write non-secret preferences to JSON
        to_save = {k: v for k, v in new_settings.items() if not k.endswith("_api_key")}
        json_path = get_settings_json_path()
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(to_save, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Gagal menyimpan settings.json: {e}")

    @staticmethod
    def get_secret(key_name: str) -> Optional[str]:
        if HAS_KEYRING:
            try:
                return keyring.get_password(SERVICE_NAME, key_name)
            except Exception:
                pass
        return None

    @staticmethod
    def set_secret(key_name: str, value: str) -> None:
        if HAS_KEYRING:
            try:
                keyring.set_password(SERVICE_NAME, key_name, value)
            except Exception as e:
                print(f"[WARNING] Gagal menyimpan secret ke keyring ({key_name}): {e}")

    @staticmethod
    def delete_secret(key_name: str) -> None:
        if HAS_KEYRING:
            try:
                keyring.delete_password(SERVICE_NAME, key_name)
            except Exception:
                pass
