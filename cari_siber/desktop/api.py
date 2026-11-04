import os
import subprocess
from typing import Dict, Any, Optional

from cari_siber.settings import AppSettings
from cari_siber.engine.core.config import AppConfig
from cari_siber.paths import get_run_dir
from cari_siber.services.history import HistoryService
from cari_siber.services.results import ResultsService
from cari_siber.services.pipeline_runner import PipelineRunner
from cari_siber.engine.core.ai_client import generate_text
from cari_siber.engine.reporters.youtube_comments import run_exporter


class DesktopApi:
    """
    Exposed Python API methods for pywebview `window.pywebview.api`.
    """
    def __init__(self, runner: PipelineRunner):
        self.runner = runner

    def get_settings(self) -> Dict[str, Any]:
        return AppSettings.load()

    def save_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        AppSettings.save(new_settings)
        return {"success": True, "message": "Pengaturan berhasil disimpan."}

    def test_ai_connection(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        provider = settings.get("ai_provider", "gemini").lower().strip()
        model = settings.get("ai_model", "gemini-3.8-flash").strip()
        api_key = settings.get(f"{provider}_api_key", "").strip()
        if provider == "custom":
            custom_base = settings.get("custom_base_url", "https://api.tokenai.id/v1").strip()
            AppConfig.CUSTOM_BASE_URL = custom_base
            AppConfig.CUSTOM_API_KEY = api_key

        try:
            resp = generate_text(
                prompt="Tes koneksi CaRI-Siber ID. Balas satu kata: 'OK'.",
                provider=provider,
                model=model,
                api_key=api_key,
                min_length=1,
                max_retries=1,
                timeout=12.0,
            )
            if resp:
                return {"success": True, "message": f"Koneksi {provider.upper()} ({model}) Berhasil! Respon: {resp.strip()[:60]}"}
            return {"success": False, "message": f"Tidak ada respon dari {provider} ({model})."}
        except Exception as e:
            return {"success": False, "message": f"Gagal terhubung: {str(e)}"}

    def start_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        video_url = payload.get("video_url", "").strip()
        raw_urls = payload.get("video_urls", [])
        video_urls = [str(u).strip() for u in raw_urls if str(u).strip() and str(u).strip().lower() != "undefined"]

        if (not video_url or video_url.lower() == "undefined") and video_urls:
            video_url = video_urls[0]

        limit_comments = int(payload.get("limit_comments", 1000))
        sort_by = payload.get("sort_by", "top")
        include_replies = bool(payload.get("include_replies", True))
        skip_scrape = bool(payload.get("skip_scrape", False))

        if not video_url:
            return {"success": False, "error": "URL Video YouTube wajib diisi atau dipilih."}

        try:
            run_id = self.runner.start_youtube_analysis(
                video_url=video_url,
                video_urls=video_urls if video_urls else None,
                limit_comments=limit_comments,
                sort_by=sort_by,
                include_replies=include_replies,
                skip_scrape=skip_scrape,
            )
            return {"success": True, "run_id": run_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cancel_run(self) -> Dict[str, Any]:
        self.runner.request_cancel()
        return {"success": True}

    def is_runner_busy(self) -> bool:
        return self.runner.is_busy()

    def list_history(self) -> list:
        try:
            return HistoryService.list_runs() or []
        except Exception as e:
            print(f"[API ERROR] list_history failed: {e}")
            return []

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        if not run_id:
            return None
        try:
            return HistoryService.get_run(run_id)
        except Exception as e:
            print(f"[API ERROR] get_run failed for {run_id}: {e}")
            return None

    def get_run_results(self, run_id: str) -> Optional[Dict[str, Any]]:
        if not run_id:
            return None
        try:
            run = HistoryService.get_run(run_id)
            run_dir = run["run_dir"] if run and run.get("run_dir") else get_run_dir(run_id)
            if not run_dir or not os.path.exists(run_dir):
                return None
            return ResultsService.load_run_results(run_dir)
        except Exception as e:
            print(f"[API ERROR] get_run_results failed for {run_id}: {e}")
            return None

    def delete_history(self, run_id: str) -> Dict[str, Any]:
        success = HistoryService.delete_run(run_id)
        return {"success": success}

    def export_xlsx(self, run_id: str) -> Dict[str, Any]:
        run = HistoryService.get_run(run_id)
        if not run:
            return {"success": False, "error": "Run ID tidak ditemukan."}

        try:
            xlsx_path = run_exporter(output_dir=run["run_dir"])
            return {"success": True, "path": xlsx_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_folder(self, run_id: str) -> Dict[str, Any]:
        run = HistoryService.get_run(run_id)
        if not run or not os.path.exists(run["run_dir"]):
            return {"success": False, "error": "Folder run tidak ditemukan."}

        try:
            folder = run["run_dir"]
            if hasattr(os, "startfile"):
                os.startfile(folder)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", folder])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", folder])
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_and_curate_videos(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        keyword = payload.get("keyword", "").strip()
        max_curated = int(payload.get("max_curated", 10))
        if not keyword:
            return {"success": False, "error": "Kata kunci pencarian tidak boleh kosong."}

        try:
            from cari_siber.services.discovery import VideoDiscoveryService
            res = VideoDiscoveryService.discover_and_curate(keyword=keyword, max_curated=max_curated)
            return res
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_author_comments(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        run_id = str(payload.get("run_id", "")).strip()
        author_key = str(payload.get("author_key", "")).strip()
        if not run_id or not author_key:
            return {"success": False, "error": "run_id dan author_key tidak boleh kosong."}

        try:
            run = HistoryService.get_run(run_id)
            run_dir = run["run_dir"] if run and run.get("run_dir") else get_run_dir(run_id)
            comments = ResultsService.get_comments_by_author(run_dir, author_key)
            return {"success": True, "comments": comments}
        except Exception as e:
            return {"success": False, "error": str(e)}
