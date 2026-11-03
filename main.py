"""
CaRI-Siber ID - Cognitive Domain Intelligence Desktop Application
Entry Point (PyWebView + React Desktop Standalone)
"""

import os
import sys
import signal
import argparse

from cari_siber.bootstrap import setup_desktop_environment
from cari_siber.desktop.window import start_app_window

_global_ctrl_handler = None

def setup_exit_handlers():
    """Menangani Ctrl+C di terminal dan penutupan paksa agar proses langsung berhenti."""
    global _global_ctrl_handler
    if sys.platform == "win32":
        try:
            import ctypes
            def console_handler(ctrl_type):
                # 0 = CTRL_C_EVENT, 1 = CTRL_BREAK_EVENT, 2 = CTRL_CLOSE_EVENT
                os._exit(0)
                return True

            _global_ctrl_handler = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)(console_handler)
            ctypes.windll.kernel32.SetConsoleCtrlHandler(_global_ctrl_handler, True)
        except Exception:
            pass

    def signal_handler(sig, frame):
        os._exit(0)

    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception:
        pass


def main():
    setup_exit_handlers()

    parser = argparse.ArgumentParser(description="CaRI-Siber ID Desktop Application")
    parser.add_argument("--dev", action="store_true", help="Jalankan menghubungkan ke Vite Dev Server di localhost:5173")
    args = parser.parse_args()

    # 1. Setup Runtime & Logging
    setup_desktop_environment()

    # 2. Launch Desktop Window
    start_app_window(dev_mode=args.dev)


if __name__ == "__main__":
    main()
