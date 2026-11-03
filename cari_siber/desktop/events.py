import json
from typing import Dict, Any, Optional

class DesktopEventEmitter:
    def __init__(self):
        self.window = None

    def set_window(self, window):
        self.window = window

    def emit(self, event: Dict[str, Any]):
        if not self.window:
            return
        try:
            payload = json.dumps(event)
            # Safe call in webview context
            self.window.evaluate_js(f"if (window.__cariEmit) {{ window.__cariEmit({payload}); }}")
        except Exception:
            pass
