import os
import sys
import webview

from cari_siber.paths import get_ui_dist_dir
from cari_siber.desktop.api import DesktopApi
from cari_siber.desktop.events import DesktopEventEmitter
from cari_siber.services.pipeline_runner import PipelineRunner
from cari_siber.services.history import HistoryService


def start_app_window(dev_mode: bool = False):
    """
    Launches the PyWebView desktop application window using Windows WebView2.
    """
    # 1. Initialize SQLite Database
    HistoryService.init_db()

    # 2. Setup Events & Runner
    event_emitter = DesktopEventEmitter()
    runner = PipelineRunner(event_emitter=event_emitter.emit)
    js_api = DesktopApi(runner)

    # 3. Determine URL
    if dev_mode:
        start_url = "http://localhost:5173"
        print("[INFO] Menjalankan dalam mode DEV (Vite dev server: http://localhost:5173)")
    else:
        dist_dir = get_ui_dist_dir()
        index_file = os.path.join(dist_dir, "index.html")
        if not os.path.exists(index_file):
            print(f"[ERROR] Frontend dist tidak ditemukan di: {index_file}")
            print("Harap jalankan 'npm run build' di folder frontend terlebih dahulu.")
            sys.exit(1)
        start_url = f"file:///{os.path.abspath(index_file).replace(os.sep, '/')}"
        print(f"[INFO] Memuat UI Desktop produksi dari: {start_url}")

    # 4. Create Window
    window = webview.create_window(
        title="CaRI-Siber ID - Cognitive Domain Intelligence",
        url=start_url,
        js_api=js_api,
        width=1280,
        height=820,
        min_size=(960, 640),
        background_color="#0F172A",
    )

    event_emitter.set_window(window)

    def on_closed():
        # Memastikan seluruh proses & thread worker latar belakang mati seketika saat jendela ditutup
        os._exit(0)

    window.events.closed += on_closed

    # 5. Start WebView
    try:
        webview.start(gui="edgechromium", debug=dev_mode)
    finally:
        os._exit(0)
