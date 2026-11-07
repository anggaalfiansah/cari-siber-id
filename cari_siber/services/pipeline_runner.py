import os
import json
import time
import shutil
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable

import pandas as pd

from cari_siber.paths import get_run_dir, get_resources_dir
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
        self._lock = threading.Lock()

    def is_busy(self) -> bool:
        with self._lock:
            return self._is_running

    def request_cancel(self):
        with self._lock:
            if self._is_running:
                self._cancel_requested = True
                self._emit({
                    "type": "progress",
                    "run_id": self.active_run_id or "",
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
        video_url: str = "",
        video_urls: Optional[list] = None,
        limit_comments: int = 1000,
        sort_by: str = "top",
        include_replies: bool = True,
        skip_scrape: bool = False,
        source_run_id: Optional[str] = None,
        search_keyword: str = "",
    ) -> str:
        with self._lock:
            if self._is_running:
                raise RuntimeError("Analisis lain sedang berjalan. Harap tunggu hingga selesai.")

            run_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())[:6]
            run_dir = get_run_dir(run_id)
            clean_keyword = str(search_keyword or "").strip()

            resolved_urls = []
            if video_urls and isinstance(video_urls, list):
                resolved_urls = [str(u).strip() for u in video_urls if str(u).strip()]
            elif video_url and str(video_url).strip():
                resolved_urls = [str(video_url).strip()]

            # Jika menggunakan korpus dari run sebelumnya (Reuse Corpus) atau Demo Dataset Militer
            if source_run_id:
                src_id_str = str(source_run_id).strip()
                if src_id_str.startswith("demo:"):
                    demo_filename = os.path.basename(src_id_str.split("demo:", 1)[1])
                    if not clean_keyword:
                        if "tni" in demo_filename.lower():
                            clean_keyword = "Operasi Pengamanan Perbatasan & Bakti Sosial"
                        elif "siber" in demo_filename.lower():
                            clean_keyword = "Pertahanan Siber & Mitigasi Hoaks Infrastruktur Kritis"
                    demo_csv_path = os.path.join(get_resources_dir(), demo_filename)
                    if os.path.exists(demo_csv_path):
                        target_scrap = os.path.join(run_dir, "scrap")
                        os.makedirs(target_scrap, exist_ok=True)
                        shutil.copy2(demo_csv_path, os.path.join(target_scrap, "youtube_comments_all_videos.csv"))
                        shutil.copy2(demo_csv_path, os.path.join(target_scrap, "youtube_comments_simulasi.csv"))
                        try:
                            demo_df = pd.read_csv(demo_csv_path)
                            if "video_id" in demo_df.columns:
                                meta_rows = []
                                for vid, vdf in demo_df.groupby("video_id"):
                                    vtitle = str(vdf["video_title"].iloc[0]) if "video_title" in vdf.columns else f"Simulasi Video {vid}"
                                    vchan = str(vdf["channel_name"].iloc[0]) if "channel_name" in vdf.columns else "Kanal Operasi Simulasi"
                                    meta_rows.append({
                                        "video_id": str(vid),
                                        "video_title": vtitle,
                                        "channel_name": vchan,
                                        "video_url": f"https://www.youtube.com/watch?v={vid}",
                                        "published_at": str(vdf["created_at"].iloc[0])[:10] if "created_at" in vdf.columns else "2026-10-01",
                                        "views": int(len(vdf) * 1850),
                                        "video_likes": int(len(vdf) * 95),
                                    })
                                if meta_rows:
                                    pd.DataFrame(meta_rows).to_csv(os.path.join(target_scrap, "youtube_videos_meta_all.csv"), index=False, encoding="utf-8-sig")
                                    pd.DataFrame([meta_rows[0]]).to_csv(os.path.join(target_scrap, f"youtube_video_meta_{meta_rows[0]['video_id']}.csv"), index=False, encoding="utf-8-sig")
                                    resolved_urls = [m["video_url"] for m in meta_rows]
                        except Exception as e:
                            print(f"[RUNNER WARNING] Gagal membuat meta simulasi: {e}")
                        skip_scrape = True
                        print(f"[RUNNER] Berhasil memuat Korpus Simulasi Militer ({demo_filename}) ke {run_id}.")
                else:
                    source_dir = get_run_dir(src_id_str)
                    source_scrap = os.path.join(source_dir, "scrap")
                    if not clean_keyword:
                        src_ctx = os.path.join(source_dir, "json", "run_context.json")
                        if os.path.exists(src_ctx):
                            try:
                                with open(src_ctx, "r", encoding="utf-8") as scf:
                                    clean_keyword = str(json.load(scf).get("search_keyword", "")).strip()
                            except Exception:
                                pass
                    if os.path.exists(source_scrap):
                        target_scrap = os.path.join(run_dir, "scrap")
                        os.makedirs(target_scrap, exist_ok=True)
                        for item in os.listdir(source_scrap):
                            s_path = os.path.join(source_scrap, item)
                            if os.path.isfile(s_path):
                                shutil.copy2(s_path, os.path.join(target_scrap, item))
                        skip_scrape = True
                        print(f"[RUNNER] Berhasil menyalin data korpus scraping dari Run {source_run_id} ke {run_id}.")

                        # Ekstrak info video jika resolved_urls belum ada
                        if not resolved_urls:
                            meta_all = os.path.join(target_scrap, "youtube_videos_meta_all.csv")
                            if os.path.exists(meta_all):
                                try:
                                    m_df = pd.read_csv(meta_all)
                                    if "video_id" in m_df.columns:
                                        resolved_urls = [f"https://www.youtube.com/watch?v={vid}" for vid in m_df["video_id"].dropna().unique()]
                                except Exception:
                                    pass

            primary_url = resolved_urls[0] if resolved_urls else (video_url or "https://www.youtube.com/watch?v=corpus_reused")

            # Simpan run_context.json agar kata kunci pencarian tersimpan permanen
            try:
                json_init_dir = os.path.join(run_dir, "json")
                os.makedirs(json_init_dir, exist_ok=True)
                with open(os.path.join(json_init_dir, "run_context.json"), "w", encoding="utf-8") as rcf:
                    json.dump(
                        {
                            "search_keyword": clean_keyword,
                            "video_count": len(resolved_urls) or 1,
                            "source_run_id": source_run_id or "",
                        },
                        rcf,
                        ensure_ascii=False,
                        indent=2,
                    )
            except Exception:
                pass

            # 1. Load settings & configure engine
            settings = AppSettings.load()
            AppConfig.configure_run(
                run_dir=run_dir,
                settings=settings,
                video_url=primary_url,
                video_urls=resolved_urls,
                limit_comments=limit_comments,
                sort_by=sort_by,
                include_replies=include_replies,
                search_keyword=clean_keyword,
            )

            # 2. Record to SQLite (Store primary url or campaign summary)
            if clean_keyword and len(resolved_urls) > 1:
                history_target = f"Kata Kunci: \"{clean_keyword}\" ({len(resolved_urls)} Video)"
            elif source_run_id:
                history_target = f"[Reuse {source_run_id[:15]}] {primary_url}" if len(resolved_urls) <= 1 else f"[Reuse {source_run_id[:15]}] {len(resolved_urls)} video korpus"
            else:
                history_target = primary_url if len(resolved_urls) <= 1 else f"{primary_url} (+{len(resolved_urls)-1} video lainnya)"
            HistoryService.create_run(run_id, history_target, run_dir)

            self.active_run_id = run_id
            self._cancel_requested = False
            self._is_running = True

            self.active_thread = threading.Thread(
                target=self._worker_thread,
                args=(run_id, run_dir, primary_url, skip_scrape),
                daemon=True,
            )
            self.active_thread.start()
            return run_id

    def _worker_thread(self, run_id: str, run_dir: str, video_url: str, skip_scrape: bool):
        t_pipeline_start = time.time()
        # Reset tracker token di awal run
        try:
            from cari_siber.engine.core.ai_client import reset_token_tracker, TOKEN_USAGE_TRACKER
            reset_token_tracker()
        except Exception:
            TOKEN_USAGE_TRACKER = {}

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
                target_vids = getattr(AppConfig, "YOUTUBE_VIDEO_URLS", [])
                if len(target_vids) > 1:
                    self._emit_step("Scraping Komentar", 1, 10, f"Mengunduh komentar dari {len(target_vids)} video target secara kolektif...")
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
            cross_intel = IntelligenceService.calculate_cross_video_intelligence(df_final, run_dir)

            # Simpan ringkasan CIB & Polarisasi ke berkas JSON run agar mandiri dan persisten
            json_dir = os.path.join(run_dir, "json")
            os.makedirs(json_dir, exist_ok=True)
            try:
                with open(os.path.join(json_dir, "cib_detection_summary.json"), "w", encoding="utf-8") as cjf:
                    json.dump({
                        "cib_threat_score": cib_metrics.cib_threat_score,
                        "cib_threat_level": cib_metrics.cib_threat_level.value,
                        "total_comments_analyzed": cib_metrics.total_comments_analyzed,
                        "unique_authors": cib_metrics.unique_authors,
                        "author_duplication_rate": cib_metrics.author_duplication_rate,
                        "rapid_burst_ratio": cib_metrics.rapid_burst_ratio,
                        "high_risk_bot_count": cib_metrics.high_risk_bot_count,
                    }, cjf, indent=2)

                with open(os.path.join(json_dir, "polarization_metrics.json"), "w", encoding="utf-8") as pjf:
                    json.dump({
                        "polarization_index": pol_metrics.polarization_index,
                        "sentiment_distribution": pol_metrics.sentiment_distribution,
                        "dominant_conflict_topics": pol_metrics.dominant_conflict_topics,
                        "silent_majority_consensus": pol_metrics.silent_majority_consensus,
                    }, pjf, indent=2)

                flagged_accounts = IntelligenceService.calculate_flagged_accounts(df_final)
                with open(os.path.join(json_dir, "flagged_accounts.json"), "w", encoding="utf-8") as faf:
                    json.dump(flagged_accounts, faf, indent=2)

                bot_networks = IntelligenceService.calculate_coordinated_bot_networks(df_final)
                with open(os.path.join(json_dir, "coordinated_bot_networks.json"), "w", encoding="utf-8") as bjf:
                    json.dump(bot_networks, bjf, indent=2)

                # Rekam Telemetri Eksekusi: Waktu Total, Token AI, & Model yang Digunakan
                t_pipeline_end = time.time()
                total_duration = max(0.1, round(t_pipeline_end - t_pipeline_start, 2))
                dur_minutes = int(total_duration // 60)
                dur_seconds = int(total_duration % 60)
                duration_formatted = f"{dur_minutes}m {dur_seconds}s" if dur_minutes > 0 else f"{total_duration:.1f}s"

                settings = AppSettings.load()
                used_provider = getattr(settings, "ai_provider", "custom") or "custom"
                used_model = getattr(settings, "ai_model", "") or getattr(AppConfig, "AI_MODEL", "") or "default-model"

                telemetry_data = {
                    "ai_provider": used_provider,
                    "ai_model": used_model,
                    "total_duration_sec": total_duration,
                    "duration_formatted": duration_formatted,
                    "prompt_tokens": int(TOKEN_USAGE_TRACKER.get("prompt_tokens", 0)),
                    "completion_tokens": int(TOKEN_USAGE_TRACKER.get("completion_tokens", 0)),
                    "total_tokens": int(TOKEN_USAGE_TRACKER.get("total_tokens", 0)),
                    "llm_calls_count": int(TOKEN_USAGE_TRACKER.get("calls", 0)),
                }

                with open(os.path.join(json_dir, "telemetry_summary.json"), "w", encoding="utf-8") as tf:
                    json.dump(telemetry_data, tf, indent=2)

            except Exception as j_err:
                print(f"[PIPELINE WARNING] Gagal menyimpan ringkasan metrik JSON: {j_err}")

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

            # Generate SHA-256 Digital Evidence Seal (Chain of Custody)
            forensic_manifest = HistoryService.generate_forensic_manifest(run_dir, run_id)
            sha256_hash = str(forensic_manifest.get("primary_sha256", ""))

            # Complete SQLite run
            HistoryService.complete_run(
                run_id=run_id,
                video_title=video_title,
                channel_name=channel_name,
                total_comments=len(df_final),
                cib_score=cib_metrics.cib_threat_score,
                cib_level=cib_metrics.cib_threat_level.value,
                polarization_index=pol_metrics.polarization_index,
                sha256_hash=sha256_hash,
            )

            # Emit lightweight completion event (frontend memuat data grafik on-demand via get_run_results)
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
            with self._lock:
                self._is_running = False

    def _emit_step(self, step_name: str, step_index: int, percent: int, message: str, run_id: str = ""):
        self._emit({
            "type": "progress",
            "run_id": run_id or self.active_run_id or "",
            "status": "RUNNING",
            "step_index": step_index,
            "percent": percent,
            "step_name": step_name,
            "message": message,
        })

    def _check_cancelled(self, run_id: str) -> bool:
        with self._lock:
            cancelled = self._cancel_requested
        if cancelled:
            print("[INFO] Pipeline dibatalkan oleh pengguna.")
            HistoryService.update_run_status(run_id, "CANCELLED", error="Dibatalkan oleh pengguna")
            self._emit({
                "type": "progress",
                "run_id": run_id,
                "status": "CANCELLED",
                "percent": 0,
                "step_name": "Dibatalkan",
                "message": "Analisis telah dibatalkan.",
            })
            return True
        return False
