import os
import time
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable

import pandas as pd

from cari_siber.paths import get_run_dir
from cari_siber.settings import AppSettings
from cari_siber.bootstrap import get_log_stream
from cari_siber.services.history import HistoryService
from cari_siber.services.intelligence import IntelligenceService
from cari_siber.services.results import ResultsService
from cari_siber.engine.core.config import AppConfig
from cari_siber.engine.core.exceptions import PipelineError
from cari_siber.engine.core.agentic_gates import AgenticAuditLogger


class PipelineRunner:
    """
    Manages active pipeline execution in a dedicated background worker thread.
    Heavy pipeline modules are loaded lazily in the thread to ensure the GUI launches instantly.
    """
    def __init__(self, event_emitter: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.event_emitter = event_emitter
        self.active_thread: Optional[threading.Thread] = None
        self.active_run_id: Optional[str] = None
        self._cancel_requested = False
        self._is_running = False

    def is_busy(self) -> bool:
        return self._is_running

    def request_cancel(self):
        if self._is_running:
            self._cancel_requested = True
            self._emit({
                "type": "progress",
                "status": "CANCELLING",
                "percent": 0,
                "step_name": "Membatalkan...",
                "message": "Permintaan pembatalan diterima. Menunggu tahap saat ini selesai...",
            })

    def _emit(self, event: Dict[str, Any]):
        if self.event_emitter:
            try:
                self.event_emitter(event)
            except Exception:
                pass

    def start_youtube_analysis(
        self,
        video_url: str,
        limit_comments: int = 1000,
        sort_by: str = "top",
        include_replies: bool = True,
        skip_scrape: bool = False,
    ) -> str:
        if self._is_running:
            raise RuntimeError("Analisis lain sedang berjalan. Harap tunggu hingga selesai.")

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())[:6]
        run_dir = get_run_dir(run_id)

        # 1. Load settings & configure engine
        settings = AppSettings.load()
        AppConfig.configure_run(
            run_dir=run_dir,
            settings=settings,
            video_url=video_url,
            limit_comments=limit_comments,
            sort_by=sort_by,
            include_replies=include_replies,
        )

        # 2. Record to SQLite
        HistoryService.create_run(run_id, video_url, run_dir)

        self.active_run_id = run_id
        self._cancel_requested = False
        self._is_running = True

        self.active_thread = threading.Thread(
            target=self._worker_thread,
            args=(run_id, run_dir, video_url, skip_scrape),
            daemon=True,
        )
        self.active_thread.start()
        return run_id

    def _worker_thread(self, run_id: str, run_dir: str, video_url: str, skip_scrape: bool):
        # Lazy imports of pipelines inside background worker
        from cari_siber.engine.pipelines.youtube_comments.pipeline_scrape import run_scraper
        from cari_siber.engine.pipelines.youtube_comments.pipeline_topic import run_topic_modeling
        from cari_siber.engine.pipelines.youtube_comments.pipeline_label import run_ai_labeler
        from cari_siber.engine.pipelines.youtube_comments.pipeline_aggregation import run_aggregation
        from cari_siber.engine.pipelines.youtube_comments.pipeline_analysis import run_engagement_analysis
        from cari_siber.engine.pipelines.youtube_comments.pipeline_eda import run_eda
        from cari_siber.engine.pipelines.youtube_comments.pipeline_visualize import run_visualizer
        from cari_siber.engine.pipelines.youtube_comments.pipeline_narrate import run_narrator

        # Forward python prints to UI log
        log_stream = get_log_stream()
        def log_subscriber(msg: str):
            self._emit({"type": "log", "line": msg})

        if log_stream:
            log_stream.subscribe(log_subscriber)

        try:
            self._emit({
                "type": "progress",
                "status": "RUNNING",
                "run_id": run_id,
                "step_index": 0,
                "percent": 5,
                "step_name": "Inisialisasi",
                "message": f"Mempersiapkan analisis untuk: {video_url}",
            })

            AgenticAuditLogger.reset_log(run_dir)

            # Step 1: Scraping Komentar
            if self._check_cancelled(run_id): return
            if not skip_scrape:
                platform = getattr(AppConfig, "TARGET_PLATFORM", "youtube")
                if platform == "instagram":
                    from cari_siber.engine.pipelines.instagram_comments.pipeline_scrape import run_instagram_scraper
                    self._emit_step("Scraping Komentar", 1, 10, f"Mengunduh komentar dari Instagram target: {video_url}...")
                    run_instagram_scraper()
                else:
                    self._emit_step("Scraping Komentar", 1, 10, f"Mengunduh komentar dari YouTube target: {video_url}...")
                    run_scraper()
            else:
                self._emit_step("Scraping Komentar", 1, 20, "Melewati scraping (menggunakan data yang sudah ada)...")

            # Step 2: Normalisasi & BERTopic Topic Modeling
            if self._check_cancelled(run_id): return
            self._emit_step("Topic Modeling", 2, 35, "Normalisasi teks (Kamus Alay + Stopwords) & IndoBERT BERTopic...")
            run_topic_modeling()

            # Step 3: AI Semantic Labeling & 4 Hardened Gates
            if self._check_cancelled(run_id): return
            self._emit_step("AI Labeling & Audit Gates", 3, 55, "Pelabelan semantik AI & audit 4 Hardened Gates...")
            run_ai_labeler()

            # Step 4: Agregasi & Analisis Engagement
            if self._check_cancelled(run_id): return
            self._emit_step("Agregasi & Engagement", 4, 72, "Agregasi topik dan pemetaan engagement audiens...")
            run_aggregation()
            run_engagement_analysis()

            # Step 5: EDA & Visualisasi Chart
            if self._check_cancelled(run_id): return
            self._emit_step("EDA & Visualisasi", 5, 85, "Menghitung statistik ringkasan EDA & membuat 8 grafik...")
            run_eda()
            run_visualizer()

            # Step 6: Narasi AI
            if self._check_cancelled(run_id): return
            self._emit_step("Narasi Insight AI", 6, 92, "Menyusun laporan narasi intelijen kognitif...")
            run_narrator()

            # Step 7: Audit Intelijen Siber Kognitif (CIB & Polarisasi)
            if self._check_cancelled(run_id): return
            self._emit_step("Audit Intelijen Siber", 7, 96, "Menghitung metrik CIB (Buzzer/Bot) & indeks polarisasi...")

            final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_final.csv")
            if not os.path.exists(final_csv):
                final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_raw.csv")

            df_final = pd.read_csv(final_csv) if os.path.exists(final_csv) else pd.DataFrame()

            cib_metrics = IntelligenceService.calculate_cib_metrics(df_final)
            pol_metrics = IntelligenceService.calculate_polarization_metrics(df_final)

            # Metadata video
            eda_json = os.path.join(run_dir, "json", "youtube_eda_summary.json")
            video_title = "YouTube Video"
            channel_name = ""
            if os.path.exists(eda_json):
                import json
                try:
                    with open(eda_json, "r", encoding="utf-8") as jf:
                        jdata = json.load(jf)
                        video_title = jdata.get("meta", {}).get("video_title", video_title)
                        channel_name = jdata.get("meta", {}).get("channel_name", "")
                except Exception:
                    pass

            # Complete SQLite run
            HistoryService.complete_run(
                run_id=run_id,
                video_title=video_title,
                channel_name=channel_name,
                total_comments=len(df_final),
                cib_score=cib_metrics.cib_threat_score,
                cib_level=cib_metrics.cib_threat_level.value,
                polarization_index=pol_metrics.polarization_index,
            )

            # Emit completion event with full result object
            result_data = ResultsService.load_run_results(run_dir)
            self._emit({
                "type": "completed",
                "run_id": run_id,
                "status": "COMPLETED",
                "percent": 100,
                "step_name": "Selesai",
                "message": "Analisis intelijen kognitif selesai!",
                "summary": {
                    "video_title": video_title,
                    "channel_name": channel_name,
                    "total_comments": len(df_final),
                    "cib_score": cib_metrics.cib_threat_score,
                    "cib_level": cib_metrics.cib_threat_level.value,
                    "polarization_index": pol_metrics.polarization_index,
                    "sentiment_distribution": pol_metrics.sentiment_distribution,
                },
                "result": result_data,
            })

        except PipelineError as pe:
            err_msg = str(pe)
            print(f"[PIPELINE ERROR] {err_msg}")
            HistoryService.update_run_status(run_id, "FAILED", error=err_msg)
            self._emit({
                "type": "error",
                "run_id": run_id,
                "status": "FAILED",
                "message": err_msg,
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            err_msg = f"Terjadi kesalahan tak terduga: {str(e)}"
            HistoryService.update_run_status(run_id, "FAILED", error=err_msg)
            self._emit({
                "type": "error",
                "run_id": run_id,
                "status": "FAILED",
                "message": err_msg,
            })
        finally:
            if log_stream:
                log_stream.unsubscribe(log_subscriber)
            self._is_running = False

    def _emit_step(self, step_name: str, step_index: int, percent: int, message: str):
        self._emit({
            "type": "progress",
            "status": "RUNNING",
            "step_index": step_index,
            "percent": percent,
            "step_name": step_name,
            "message": message,
        })

    def _check_cancelled(self, run_id: str) -> bool:
        if self._cancel_requested:
            print("[INFO] Pipeline dibatalkan oleh pengguna.")
            HistoryService.update_run_status(run_id, "CANCELLED", error="Dibatalkan oleh pengguna")
            self._emit({
                "type": "progress",
                "status": "CANCELLED",
                "percent": 0,
                "step_name": "Dibatalkan",
                "message": "Analisis telah dibatalkan.",
            })
            return True
        return False
