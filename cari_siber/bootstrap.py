import os
import sys
from datetime import datetime
from typing import Optional
from cari_siber.paths import get_logs_dir, get_user_data_dir, get_models_dir

class DesktopLogStream:
    """
    Safely captures stdout/stderr when pythonw / PyInstaller windowed mode has None.
    Writes to log file and optionally forwards lines to active subscribers (UI).
    """
    def __init__(self, log_filepath: str, original_stream=None):
        self.log_filepath = log_filepath
        self.original_stream = original_stream
        self._subscribers = []
        os.makedirs(os.path.dirname(log_filepath), exist_ok=True)

    def write(self, message: str):
        if not message:
            return
        # 1. Echo to original stream if it exists
        if self.original_stream and hasattr(self.original_stream, "write"):
            try:
                self.original_stream.write(message)
                if hasattr(self.original_stream, "flush"):
                    self.original_stream.flush()
            except Exception:
                pass

        # 2. Append to log file
        try:
            with open(self.log_filepath, "a", encoding="utf-8") as f:
                f.write(message)
        except Exception:
            pass

        # 3. Notify UI subscribers
        for line in message.splitlines():
            line_str = line.rstrip()
            if line_str:
                for sub in list(self._subscribers):
                    try:
                        sub(line_str)
                    except Exception:
                        pass

    def flush(self):
        if self.original_stream and hasattr(self.original_stream, "flush"):
            try:
                self.original_stream.flush()
            except Exception:
                pass

    def subscribe(self, callback):
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self._subscribers:
            self._subscribers.remove(callback)


GLOBAL_LOG_STREAM = None


def get_log_stream() -> Optional[DesktopLogStream]:
    """Returns the active global log stream instance."""
    global GLOBAL_LOG_STREAM
    return GLOBAL_LOG_STREAM


def setup_desktop_environment():
    """Initializes logging, matplotlib, numba, and offline model environments."""
    global GLOBAL_LOG_STREAM

    # 1. Configure Matplotlib Non-Interactive Backend
    user_dir = get_user_data_dir()
    mpl_dir = os.path.join(user_dir, "mpl_cache")
    os.makedirs(mpl_dir, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = mpl_dir
    os.environ["MPLBACKEND"] = "Agg"
    try:
        import matplotlib
        matplotlib.use("Agg", force=True)
    except Exception:
        pass

    # 2. Redirect numba and Hugging Face caches to writable user directory
    user_dir = get_user_data_dir()
    numba_dir = os.path.join(user_dir, "numba_cache")
    os.makedirs(numba_dir, exist_ok=True)
    os.environ["NUMBA_CACHE_DIR"] = numba_dir

    hf_dir = os.path.join(user_dir, "hf_cache")
    os.makedirs(hf_dir, exist_ok=True)
    os.environ["HF_HOME"] = hf_dir

    # Check if bundled IndoBERT model exists
    bundled_model = os.path.join(get_models_dir(), "indobert-base-p1")
    if os.path.isdir(bundled_model):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    # 3. Setup robust stdout/stderr logging
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(get_logs_dir(), f"cari_siber_{today_str}.log")

    GLOBAL_LOG_STREAM = DesktopLogStream(log_file, original_stream=sys.stdout)
    sys.stdout = GLOBAL_LOG_STREAM
    sys.stderr = GLOBAL_LOG_STREAM
    print(f"=== CaRI-Siber ID Desktop Session Started: {datetime.now()} ===")
