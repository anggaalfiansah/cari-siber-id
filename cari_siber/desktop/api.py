import os
from datetime import datetime
import subprocess
import json
import pandas as pd
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from cari_siber.settings import AppSettings
from cari_siber.engine.core.config import AppConfig
from cari_siber.paths import get_run_dir
from cari_siber.services.history import HistoryService
from cari_siber.services.results import ResultsService
from cari_siber.services.pipeline_runner import PipelineRunner
from cari_siber.engine.core.ai_client import generate_text, generate_structured_json
from cari_siber.services.intelligence import IntelligenceService


class ThreatCalibrationSchema(BaseModel):
    whitelist_recommendations: List[str] = Field(
        default_factory=list,
        description="Daftar slogan resmi negara (TNI/POLRI), yel-yel nasionalisme, atau apresiasi spontan warga yang harus di-whitelist/diabaikan"
    )
    hostile_threat_keywords: List[str] = Field(
        default_factory=list,
        description="Daftar kata kunci/frasa propaganda separatis, hasutan SARA, atau kampanye disinformasi terkoordinasi musuh"
    )
    reasoning_summary: str = Field(
        default="",
        description="Penilaian singkat perwira analis intelijen siber mengenai alasan kalibrasi konteks ini"
    )
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
        import time
        provider = str(settings.get("provider") or settings.get("ai_provider") or "gemini").lower().strip()
        model = str(settings.get("model") or settings.get("ai_model") or "").strip() or ("gemini-2.5-flash" if provider == "gemini" else "deepseek-v4-flash")
        
        # Ambil api_key sesuai provider / objek profil
        api_key = str(settings.get("api_key") or settings.get(f"{provider}_api_key") or "").strip()
        if not api_key:
            api_key = str(settings.get("custom_api_key") or settings.get("gemini_api_key") or settings.get("openrouter_api_key") or "").strip()

        if provider == "custom":
            custom_base = str(settings.get("base_url") or settings.get("custom_base_url") or "https://api.tokenai.id/v1").strip()
            AppConfig.CUSTOM_BASE_URL = custom_base
            AppConfig.CUSTOM_API_KEY = api_key
        elif provider == "openrouter":
            AppConfig.OPENROUTER_API_KEY = api_key
        elif provider == "gemini":
            AppConfig.GEMINI_API_KEY = api_key

        t0 = time.time()
        try:
            resp = generate_text(
                prompt="Tes koneksi CaRI-Siber ID. Balas satu kata: 'OK'.",
                provider=provider,
                model=model,
                api_key=api_key,
                min_length=1,
                max_retries=1,
                timeout=20.0,
            )
            lat = round(time.time() - t0, 2)
            if resp:
                perf_note = "⚡ Sangat Cepat" if lat < 4.0 else ("⚠️ Cukup Lambat" if lat > 15.0 else "✓ Normal")
                return {
                    "success": True,
                    "latency_sec": lat,
                    "message": f"Koneksi Berhasil ({provider.upper()} / {model})! Latensi: {lat}s [{perf_note}]. Respon: {resp.strip()[:40]}",
                }
            return {"success": False, "message": f"Tidak ada respon dari {provider} ({model})."}
        except Exception as e:
            lat = round(time.time() - t0, 2)
            return {"success": False, "message": f"Gagal terhubung ({lat}s): {str(e)}"}

    def start_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        video_url = payload.get("video_url", "").strip()
        raw_urls = payload.get("video_urls", [])
        video_urls = [str(u).strip() for u in raw_urls if str(u).strip() and str(u).strip().lower() != "undefined"]
        source_run_id = str(payload.get("source_run_id", "")).strip() or None

        if (not video_url or video_url.lower() == "undefined") and video_urls:
            video_url = video_urls[0]

        limit_comments = int(payload.get("limit_comments", 1000))
        sort_by = payload.get("sort_by", "top")
        include_replies = bool(payload.get("include_replies", True))
        skip_scrape = bool(payload.get("skip_scrape", False))

        if not video_url and not source_run_id:
            return {"success": False, "error": "URL Video YouTube wajib diisi atau pilih data scraping sebelumnya."}

        try:
            run_id = self.runner.start_youtube_analysis(
                video_url=video_url,
                video_urls=video_urls if video_urls else None,
                limit_comments=limit_comments,
                sort_by=sort_by,
                include_replies=include_replies,
                skip_scrape=skip_scrape,
                source_run_id=source_run_id,
            )
            return {"success": True, "run_id": run_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_reusable_corpora(self) -> list:
        """
        Mendeteksi run-run yang memiliki data scraping komentar siap pakai
        sehingga pengguna dapat menggunakan kembali korpus komentar tanpa perlu re-scraping.
        """
        results = []
        try:
            from cari_siber.paths import get_runs_dir
            runs_dir = get_runs_dir()
            if not os.path.exists(runs_dir):
                return []

            for r_id in os.listdir(runs_dir):
                r_path = os.path.join(runs_dir, r_id)
                if not os.path.isdir(r_path):
                    continue

                scrap_dir = os.path.join(r_path, "scrap")
                if not os.path.exists(scrap_dir):
                    continue

                # Cari file CSV komentar
                csv_files = [
                    f for f in os.listdir(scrap_dir)
                    if f.startswith("youtube_comments_") and f.endswith(".csv")
                    and not f.endswith("_meta.csv") and not f.endswith("_meta_all.csv")
                ]
                if not csv_files:
                    continue

                # Ambil file terbesar (biasanya master corpus atau multi-video corpus)
                csv_files.sort(key=lambda x: os.path.getsize(os.path.join(scrap_dir, x)), reverse=True)
                primary_csv_name = csv_files[0]
                primary_csv_path = os.path.join(scrap_dir, primary_csv_name)
                size_bytes = os.path.getsize(primary_csv_path)
                if size_bytes < 50:
                    continue

                # Hitung jumlah baris komentar cepat (streaming lines)
                line_count = 0
                try:
                    with open(primary_csv_path, "r", encoding="utf-8", errors="ignore") as f:
                        for _ in f:
                            line_count += 1
                    line_count = max(0, line_count - 1) # minus header
                except Exception:
                    line_count = int(size_bytes / 250)

                # Deteksi jumlah video & judul dari metadata
                video_count = 1
                title = "YouTube Dataset"
                meta_all = os.path.join(scrap_dir, "youtube_videos_meta_all.csv")
                meta_single = os.path.join(scrap_dir, "youtube_video_meta.csv")

                if os.path.exists(meta_all):
                    try:
                        m_df = pd.read_csv(meta_all)
                        video_count = len(m_df)
                        if "title" in m_df.columns and not m_df.empty:
                            title = f"{m_df['title'].iloc[0]} (+{video_count-1} video lainnya)"
                    except Exception:
                        pass
                elif os.path.exists(meta_single):
                    try:
                        m_df = pd.read_csv(meta_single)
                        if "title" in m_df.columns and not m_df.empty:
                            title = str(m_df["title"].iloc[0])
                    except Exception:
                        pass

                # Timestamp pembuatan
                mtime = os.path.getmtime(primary_csv_path)
                created_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                results.append({
                    "run_id": r_id,
                    "created_at": created_at,
                    "comment_count": line_count,
                    "video_count": video_count,
                    "title": title,
                    "source_file": primary_csv_name,
                    "size_mb": round(size_bytes / (1024 * 1024), 2),
                })

            # Urutkan berdasarkan waktu modifikasi terbaru
            results.sort(key=lambda x: x["created_at"], reverse=True)
        except Exception as e:
            print(f"[API ERROR] list_reusable_corpora failed: {e}")
        return results

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

    def get_run(self, run_id: Any) -> Optional[Dict[str, Any]]:
        if isinstance(run_id, dict):
            run_id = run_id.get("run_id") or run_id.get("id")
        run_id = str(run_id).strip() if run_id else ""
        if not run_id:
            return None
        try:
            run = HistoryService.get_run(run_id)
            if run:
                res = dict(run)
                # Pastikan numerik terkonversi ke float murni
                if res.get("cib_score") is not None:
                    res["cib_score"] = float(res["cib_score"])
                if res.get("polarization_index") is not None:
                    res["polarization_index"] = float(res["polarization_index"])
                return res

            # Fallback jika run belum tersinkron di SQLite tapi foldernya ada
            run_dir = get_run_dir(run_id)
            if os.path.exists(run_dir):
                data = ResultsService.load_run_results(run_dir)
                if data:
                    meta = data.get("meta", {})
                    return {
                        "id": run_id,
                        "target_url": "",
                        "video_title": meta.get("video_title", "YouTube Video"),
                        "channel_name": meta.get("channel_name", ""),
                        "total_comments": meta.get("total_comments", 0),
                        "cib_score": float(data.get("cib_score", 0.0)),
                        "cib_level": str(data.get("cib_level", "LOW")),
                        "polarization_index": float(data.get("polarization_index", 0.0)),
                        "status": "COMPLETED",
                        "error_message": None,
                        "created_at": "",
                        "completed_at": "",
                        "run_dir": run_dir,
                    }
            return None
        except Exception as e:
            print(f"[API ERROR] get_run failed for {run_id}: {e}")
            return None

    def get_run_results(self, run_id: Any) -> Optional[Dict[str, Any]]:
        if isinstance(run_id, dict):
            run_id = run_id.get("run_id") or run_id.get("id")
        run_id = str(run_id).strip() if run_id else ""
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
        max_curated = int(payload.get("max_curated", 100))
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

    def get_chart_image(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        run_id = str(payload.get("run_id", "")).strip()
        chart_id = str(payload.get("chart_id", "")).strip()
        if not run_id or not chart_id:
            return {"success": False, "error": "run_id dan chart_id wajib diisi."}
        try:
            run_dir = get_run_dir(run_id)
            chart_path = os.path.join(run_dir, "charts", chart_id)
            if os.path.exists(chart_path):
                import base64
                with open(chart_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                return {"success": True, "data_uri": f"data:image/png;base64,{b64}"}
            return {"success": False, "error": "Chart tidak ditemukan."}
        except Exception as e:
            return {"success": False, "error": str(e)}


    def get_ai_threat_calibration(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agentic Context Calibrator:
        Menganalisis klaster komentar kembar (CIB) menggunakan LLM untuk membedakan
        antara slogan institusi/apresiasi wajar vs operasi ancaman kognitif berbahaya.
        """
        run_id = str(payload.get("run_id", "")).strip()
        if not run_id:
            return {"success": False, "error": "run_id wajib diisi."}

        try:
            run_dir = get_run_dir(run_id)
            botnet_json_path = os.path.join(run_dir, "json", "coordinated_bot_networks.json")
            botnets = []
            if os.path.exists(botnet_json_path):
                try:
                    with open(botnet_json_path, "r", encoding="utf-8") as f:
                        botnets = json.load(f)
                except Exception:
                    pass

            if not botnets:
                final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_final.csv")
                if not os.path.exists(final_csv):
                    final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_raw.csv")
                if os.path.exists(final_csv):
                    df = pd.read_csv(final_csv)
                    botnets = IntelligenceService.calculate_coordinated_bot_networks(df)

            if not botnets:
                return {
                    "success": True,
                    "whitelist_recommendations": [],
                    "hostile_threat_keywords": [],
                    "reasoning_summary": "Tidak ditemukan klaster template duplikat lintas akun pada run ini.",
                }

            # Ambil sampel klaster template teratas (maksimal 25)
            sample_items = []
            for idx, bn in enumerate(botnets[:25]):
                txt = bn.get("template_text", "")
                acc_cnt = bn.get("unique_accounts_count", 0)
                tot_cnt = bn.get("total_occurrences", 0)
                sample_items.append(f"{idx+1}. \"{txt}\" (Diposting oleh {acc_cnt} akun berbeda, total {tot_cnt} kali)")

            prompt_samples = "\n".join(sample_items)

            prompt = f"""Anda adalah Perwira Analis Intelijen Kognitif & Pertahanan Ruang Siber PUSSIBERAD TNI AD.
Tugas Anda adalah melakukan KALIBRASI KONTEKS & ELIMINASI SALAH TUDUH (False Positive Elimination) terhadap temuan klaster komentar kembar berikut:

DAFTAR KLASTER KOMENTAR KEMBAR:
{prompt_samples}

INSTRUKSI EVALUASI INTELIJEN MILITER:
1. 'whitelist_recommendations': Identifikasi frasa yang merupakan SLOGAN RESMI INSTITUSI NEGARA (TNI/POLRI), YEL-YEL PATRIOTIK, atau APRESIASI SPONTAN WARGA (misal 'TNI Bersama Rakyat', 'Terimakasih TNI', 'NKRI Harga Mati'). Frasa ini harus dikecualikan agar tidak salah dituduh sebagai bot farm musuh.
2. 'hostile_threat_keywords': Identifikasi kata kunci/frasa yang mengandung PROPAGANDA SEPARATIS (OPM/KKB), PROVOKASI DELEGITIMASI, HASUTAN KEKERASAN, atau POLA SERANGAN SIBER KOGNITIF ASIMETRIS yang wajib ditandai sebagai target ancaman (Hostile Threat).
3. 'reasoning_summary': Buat penjelasan ringkas doktrin intelijen (maksimal 3-4 kalimat) mengenai justifikasi kalibrasi ini untuk Komandan Satuan Siber.

Keluarkan hasil dalam format JSON terstruktur."""

            # Load active AI settings
            settings = AppSettings.load()
            provider = str(settings.get("provider") or settings.get("ai_provider") or "gemini").lower().strip()
            model = str(settings.get("model") or settings.get("ai_model") or "").strip()
            api_key = str(settings.get("api_key") or settings.get(f"{provider}_api_key") or "").strip()
            if not api_key:
                api_key = str(settings.get("custom_api_key") or settings.get("gemini_api_key") or settings.get("openrouter_api_key") or "").strip()

            if provider == "custom":
                custom_base = str(settings.get("base_url") or settings.get("custom_base_url") or "https://api.tokenai.id/v1").strip()
                AppConfig.CUSTOM_BASE_URL = custom_base
                AppConfig.CUSTOM_API_KEY = api_key
            elif provider == "openrouter":
                AppConfig.OPENROUTER_API_KEY = api_key
            elif provider == "gemini":
                AppConfig.GEMINI_API_KEY = api_key

            try:
                res = generate_structured_json(
                    prompt=prompt,
                    response_schema=ThreatCalibrationSchema,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                )
                wl = res.get("whitelist_recommendations", [])
                th = res.get("hostile_threat_keywords", [])
                rs = res.get("reasoning_summary", "")
                return {
                    "success": True,
                    "whitelist_recommendations": wl,
                    "hostile_threat_keywords": th,
                    "reasoning_summary": rs,
                }
            except Exception as ai_err:
                print(f"[API WARN] LLM calibration call failed: {ai_err}. Menggunakan kalibrasi heuristik otomatis.")
                fallback_wl = []
                fallback_th = []
                for bn in botnets:
                    t_low = bn.get("template_text", "").lower()
                    if any(k in t_low for k in ["tni", "polri", "nkri", "terima kasih", "terimakasih", "bravo", "rakyat"]):
                        fallback_wl.append(bn.get("template_text"))
                    if any(k in t_low for k in ["papua merdeka", "opm", "kkb", "pemberontak", "makzulkan", "hancurkan tni"]):
                        fallback_th.append(bn.get("template_text"))
                return {
                    "success": True,
                    "whitelist_recommendations": list(dict.fromkeys(fallback_wl))[:10],
                    "hostile_threat_keywords": list(dict.fromkeys(fallback_th))[:10],
                    "reasoning_summary": f"Kalibrasi Cepat PUSSIBERAD: Mengeliminasi false positive pada slogan kebangsaan & mendeteksi potensi kampanye asimetris (Engine: {str(ai_err)[:70]}).",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reanalyze_intelligence(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Instant Re-Analysis:
        Melakukan kalkulasi ulang forensik CIB, Jaringan Bot Massal, dan Akun Terduga
        secara instan (<2 dtk) menggunakan korpus komentar yang sudah ada di run_dir
        dengan parameter whitelist dan target ancaman yang telah dikalibrasi.
        """
        run_id = str(payload.get("run_id", "")).strip()
        custom_whitelist = payload.get("whitelist", [])
        custom_threats = payload.get("threats", [])

        if not run_id:
            return {"success": False, "error": "run_id wajib diisi."}

        try:
            run_dir = get_run_dir(run_id)
            final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_final.csv")
            if not os.path.exists(final_csv):
                final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_raw.csv")
            if not os.path.exists(final_csv):
                return {"success": False, "error": "File korpus CSV tidak ditemukan pada run ini."}

            df = pd.read_csv(final_csv)
            if df.empty:
                return {"success": False, "error": "Korpus CSV kosong."}

            # 1. Hitung ulang Jaringan Bot Massal
            botnets = IntelligenceService.calculate_coordinated_bot_networks(
                df,
                min_accounts=2,
                min_length=25,
                custom_whitelist=custom_whitelist,
                custom_threats=custom_threats,
            )

            # 2. Hitung ulang Akun Terduga (Flagged Accounts)
            flagged = IntelligenceService.calculate_flagged_accounts(
                df,
                custom_whitelist=custom_whitelist,
                custom_threats=custom_threats,
            )

            # 3. Hitung ulang Metrik CIB
            cib_metrics = IntelligenceService.calculate_cib_metrics(
                df,
                custom_whitelist=custom_whitelist,
                custom_threats=custom_threats,
            )

            # 4. Simpan kembali berkas JSON terkalibrasi ke run_dir
            json_dir = os.path.join(run_dir, "json")
            os.makedirs(json_dir, exist_ok=True)

            with open(os.path.join(json_dir, "coordinated_bot_networks.json"), "w", encoding="utf-8") as f:
                json.dump(botnets, f, indent=2, ensure_ascii=False)

            with open(os.path.join(json_dir, "flagged_accounts.json"), "w", encoding="utf-8") as f:
                json.dump(flagged, f, indent=2, ensure_ascii=False)

            cib_dict = {
                "cib_threat_score": cib_metrics.cib_threat_score,
                "cib_threat_level": cib_metrics.cib_threat_level.value,
                "total_comments_analyzed": cib_metrics.total_comments_analyzed,
                "unique_authors": cib_metrics.unique_authors,
                "author_duplication_rate": cib_metrics.author_duplication_rate,
                "rapid_burst_ratio": cib_metrics.rapid_burst_ratio,
                "high_risk_bot_count": cib_metrics.high_risk_bot_count,
            }
            with open(os.path.join(json_dir, "cib_detection_summary.json"), "w", encoding="utf-8") as f:
                json.dump(cib_dict, f, indent=2, ensure_ascii=False)

            # 5. Perbarui SQLite History jika run_id terdaftar
            try:
                HistoryService.update_cib_metrics(
                    run_id=run_id,
                    cib_score=cib_metrics.cib_threat_score,
                    cib_level=cib_metrics.cib_threat_level.value,
                )
            except Exception:
                pass

            return {
                "success": True,
                "cib_summary": cib_dict,
                "bot_networks_count": len(botnets),
                "flagged_accounts_count": len(flagged),
                "message": "Analisis intelijen siber berhasil diperbarui seketika.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
