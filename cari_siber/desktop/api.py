import os
import sys
import io
import base64
import uuid
from datetime import datetime
import subprocess
import json
import pandas as pd
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from cari_siber.settings import AppSettings
from cari_siber.engine.core.config import AppConfig
from cari_siber.paths import get_run_dir, get_runs_dir, get_resources_dir
from cari_siber.services.history import HistoryService
from cari_siber.services.results import ResultsService
from cari_siber.services.pipeline_runner import PipelineRunner
from cari_siber.engine.core.ai_client import generate_text, generate_structured_json
from cari_siber.services.intelligence import IntelligenceService
from cari_siber.engine.reporters.youtube_comments import run_exporter


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
        model = str(settings.get("model") or settings.get("ai_model") or "").strip() or (
            "gemini-2.5-flash" if provider == "gemini" else "qwen2.5:7b"
        )

        # Ambil api_key sesuai provider / objek profil
        api_key = str(settings.get("api_key") or settings.get(f"{provider}_api_key") or "").strip()
        if not api_key:
            api_key = str(
                settings.get("custom_api_key")
                or settings.get("gemini_api_key")
                or settings.get("openrouter_api_key")
                or ""
            ).strip()

        if provider == "custom":
            custom_base = str(
                settings.get("base_url") or settings.get("custom_base_url") or "http://127.0.0.1:11434/v1"
            ).strip()
            AppConfig.CUSTOM_BASE_URL = custom_base
            AppConfig.CUSTOM_API_KEY = api_key
        elif provider == "openrouter":
            AppConfig.OPENROUTER_API_KEY = api_key
        elif provider == "gemini":
            AppConfig.GEMINI_API_KEY = api_key

        t0 = time.time()
        try:
            resp = generate_text(
                prompt="Tes koneksi CaRI-Siber ID. Balas satu kata: 'SIAP'.",
                provider=provider,
                model=model,
                api_key=api_key,
                min_length=1,
                max_retries=1,
                timeout=20.0,
            )
            lat = round(time.time() - t0, 2)
            if resp:
                perf_note = "Sangat Cepat" if lat < 4.0 else ("Cukup Lambat" if lat > 15.0 else "Normal")
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
            return {"success": False, "error": "URL Video YouTube wajib diisi atau pilih korpus bukti lokal/simulasi."}

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
        Mendeteksi korpus simulasi militer bawaan (resources/) dan run-run yang memiliki
        data scraping komentar siap pakai sehingga pengguna dapat melakukan operasi analisis
        secara full offline / air-gapped tanpa perlu scraping ulang.
        """
        results = []
        try:
            # 1. Muat Dataset Simulasi Militer bawaan (Pre-loaded Offline Demo Corpora)
            res_dir = get_resources_dir()
            demo_specs = [
                (
                    "sample_corpus_tni.csv",
                    "[SIMULASI MILITER] Operasi Pengamanan Perbatasan & Bakti Teritorial TNI AD (3 Video Multi-CIB)",
                ),
                (
                    "sample_corpus_siber_ot.csv",
                    "[SIMULASI SIBER IT/OT] Pertahanan Siber PUSSIBERAD & Mitigasi Hoaks Infrastruktur Komando (2 Video)",
                ),
            ]
            for fname, label_title in demo_specs:
                fpath = os.path.join(res_dir, fname)
                if os.path.exists(fpath):
                    try:
                        df_demo = pd.read_csv(fpath)
                        v_cnt = int(df_demo["video_id"].nunique()) if "video_id" in df_demo.columns else 1
                        c_cnt = len(df_demo)
                        s_bytes = os.path.getsize(fpath)
                        sha256_val = HistoryService.compute_sha256(fpath)
                        results.append({
                            "run_id": f"demo:{fname}",
                            "created_at": "PRELOADED-SIMULASI",
                            "comment_count": c_cnt,
                            "video_count": v_cnt,
                            "title": label_title,
                            "source_file": fname,
                            "size_mb": round(max(0.01, s_bytes / (1024 * 1024)), 2),
                            "sha256_hash": sha256_val,
                            "is_demo": True,
                        })
                    except Exception:
                        pass

            # 2. Muat Korpus dari Direktori Runs Pengguna
            runs_dir = get_runs_dir()
            if not os.path.exists(runs_dir):
                return results

            user_corpora = []
            for r_id in os.listdir(runs_dir):
                r_path = os.path.join(runs_dir, r_id)
                if not os.path.isdir(r_path):
                    continue

                scrap_dir = os.path.join(r_path, "scrap")
                if not os.path.exists(scrap_dir):
                    continue

                csv_files = [
                    f for f in os.listdir(scrap_dir)
                    if f.startswith("youtube_comments_") and f.endswith(".csv")
                    and not f.endswith("_meta.csv") and not f.endswith("_meta_all.csv")
                ]
                if not csv_files:
                    continue

                csv_files.sort(key=lambda x: os.path.getsize(os.path.join(scrap_dir, x)), reverse=True)
                primary_csv_name = csv_files[0]
                primary_csv_path = os.path.join(scrap_dir, primary_csv_name)
                size_bytes = os.path.getsize(primary_csv_path)
                if size_bytes < 50:
                    continue

                line_count = 0
                try:
                    with open(primary_csv_path, "r", encoding="utf-8", errors="ignore") as f:
                        for _ in f:
                            line_count += 1
                    line_count = max(0, line_count - 1)
                except Exception:
                    line_count = int(size_bytes / 250)

                video_count = 1
                title = "Korpus Bukti Digital"
                meta_all = os.path.join(scrap_dir, "youtube_videos_meta_all.csv")
                meta_single = os.path.join(scrap_dir, "youtube_video_meta.csv")

                if os.path.exists(meta_all):
                    try:
                        m_df = pd.read_csv(meta_all)
                        video_count = len(m_df)
                        t_col = "video_title" if "video_title" in m_df.columns else ("title" if "title" in m_df.columns else None)
                        if t_col and not m_df.empty:
                            first_t = str(m_df[t_col].iloc[0])
                            title = f"{first_t} (+{video_count-1} video lainnya)" if video_count > 1 else first_t
                    except Exception:
                        pass
                elif os.path.exists(meta_single):
                    try:
                        m_df = pd.read_csv(meta_single)
                        t_col = "video_title" if "video_title" in m_df.columns else ("title" if "title" in m_df.columns else None)
                        if t_col and not m_df.empty:
                            title = str(m_df[t_col].iloc[0])
                    except Exception:
                        pass

                mtime = os.path.getmtime(primary_csv_path)
                created_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                sha256_val = HistoryService.compute_sha256(primary_csv_path)

                user_corpora.append({
                    "run_id": r_id,
                    "created_at": created_at,
                    "comment_count": line_count,
                    "video_count": video_count,
                    "title": title,
                    "source_file": primary_csv_name,
                    "size_mb": round(max(0.01, size_bytes / (1024 * 1024)), 2),
                    "sha256_hash": sha256_val,
                    "is_demo": False,
                })

            user_corpora.sort(key=lambda x: x["created_at"], reverse=True)
            results.extend(user_corpora)
        except Exception as e:
            print(f"[API ERROR] list_reusable_corpora failed: {e}")
        return results

    def import_external_corpus(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Impor korpus bukti digital eksternal (.CSV, .JSON, .XLSX) lintas platform
        (YouTube, X/Twitter, TikTok, Telegram, log intelijen) untuk dianalisis secara offline.
        """
        filename = str(payload.get("filename", "external_corpus.csv")).strip()
        content_b64 = str(payload.get("content_base64", "")).strip()
        content_text = str(payload.get("content_text", "")).strip()
        custom_title = str(payload.get("title", "")).strip()

        if not content_b64 and not content_text:
            return {"success": False, "error": "Konten berkas kosong atau tidak ditemukan."}

        try:
            raw_bytes = base64.b64decode(content_b64) if content_b64 else content_text.encode("utf-8")
            ext = os.path.splitext(filename)[1].lower()

            if ext == ".json":
                parsed_json = json.loads(raw_bytes.decode("utf-8", errors="replace"))
                if isinstance(parsed_json, dict):
                    for k in ["comments", "data", "items", "records", "rows", "messages"]:
                        if k in parsed_json and isinstance(parsed_json[k], list):
                            parsed_json = parsed_json[k]
                            break
                df_raw = pd.DataFrame(parsed_json if isinstance(parsed_json, list) else [parsed_json])
            elif ext in (".xlsx", ".xls"):
                df_raw = pd.read_excel(io.BytesIO(raw_bytes))
            else:
                df_raw = pd.read_csv(io.BytesIO(raw_bytes))

            if df_raw.empty:
                return {"success": False, "error": "Berkas yang diimpor tidak memiliki baris data."}

            # Normalisasi nama kolom lintas platform (YouTube, X, TikTok, Telegram, OSINT Dump)
            col_map = {str(c).lower().strip(): c for c in df_raw.columns}

            def _pick_col(candidates: List[str], default_val: Any = ""):
                for cand in candidates:
                    if cand in col_map:
                        return df_raw[col_map[cand]]
                return pd.Series([default_val] * len(df_raw))

            df_norm = pd.DataFrame()
            df_norm["comment_text"] = _pick_col(
                ["comment_text", "text", "body", "content", "message", "ulasan", "komentar", "tweet", "caption"],
                "",
            ).fillna("").astype(str)

            # Filter baris dengan teks kosong
            df_norm = df_norm[df_norm["comment_text"].str.strip().ne("")].reset_index(drop=True)
            if df_norm.empty:
                return {"success": False, "error": "Tidak ditemukan kolom teks komentar (comment_text / text / body / komentar)."}

            df_norm["comment_id"] = _pick_col(
                ["comment_id", "id", "post_id", "tweet_id", "message_id"],
                "",
            ).reindex(df_norm.index, fill_value="")
            df_norm["comment_id"] = [
                str(val) if str(val).strip() else f"ext_{i+1:05d}"
                for i, val in enumerate(df_norm["comment_id"])
            ]

            df_norm["username"] = _pick_col(
                ["username", "author", "user", "screen_name", "handle", "sender", "nama", "author_name"],
                "@anonim",
            ).reindex(df_norm.index, fill_value="@anonim").fillna("@anonim").astype(str)

            df_norm["author_channel_id"] = _pick_col(
                ["author_channel_id", "user_id", "author_id", "account_id", "sender_id"],
                "",
            ).reindex(df_norm.index, fill_value="").fillna("").astype(str)
            df_norm["author_channel_id"] = [
                aid if str(aid).strip() else f"ID_{uname}"
                for aid, uname in zip(df_norm["author_channel_id"], df_norm["username"])
            ]

            df_norm["author_channel_url"] = _pick_col(
                ["author_channel_url", "profile_url", "user_url"],
                "",
            ).reindex(df_norm.index, fill_value="").fillna("").astype(str)

            df_norm["like_count"] = pd.to_numeric(
                _pick_col(["like_count", "likes", "favorite_count", "upvotes", "reactions", "jumlah_like"], 0).reindex(df_norm.index, fill_value=0),
                errors="coerce",
            ).fillna(0).astype(int)

            df_norm["reply_count"] = pd.to_numeric(
                _pick_col(["reply_count", "replies", "comments_count", "retweets", "jumlah_balasan"], 0).reindex(df_norm.index, fill_value=0),
                errors="coerce",
            ).fillna(0).astype(int)

            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df_norm["created_at"] = _pick_col(
                ["created_at", "timestamp", "date", "published_at", "time", "waktu", "tanggal"],
                now_iso,
            ).reindex(df_norm.index, fill_value=now_iso).fillna(now_iso).astype(str)

            df_norm["is_reply"] = _pick_col(["is_reply"], False).reindex(df_norm.index, fill_value=False)
            df_norm["is_hearted"] = _pick_col(["is_hearted"], False).reindex(df_norm.index, fill_value=False)
            df_norm["is_pinned"] = _pick_col(["is_pinned"], False).reindex(df_norm.index, fill_value=False)
            df_norm["is_official"] = _pick_col(["is_official"], False).reindex(df_norm.index, fill_value=False)

            default_vid = os.path.splitext(os.path.basename(filename))[0][:24] or "EXT_CORPUS_01"
            df_norm["video_id"] = _pick_col(
                ["video_id", "source_id", "thread_id", "channel_id", "post_id"],
                default_vid,
            ).reindex(df_norm.index, fill_value=default_vid).fillna(default_vid).astype(str)

            default_vtitle = custom_title or f"Impor Bukti Digital: {os.path.basename(filename)}"
            df_norm["video_title"] = _pick_col(
                ["video_title", "title", "source_title", "campaign", "topik"],
                default_vtitle,
            ).reindex(df_norm.index, fill_value=default_vtitle).fillna(default_vtitle).astype(str)

            df_norm["channel_name"] = _pick_col(
                ["channel_name", "platform", "source", "kanal", "media"],
                "Korpus Multi-Platform Eksternal",
            ).reindex(df_norm.index, fill_value="Korpus Multi-Platform Eksternal").fillna("Korpus Multi-Platform Eksternal").astype(str)

            # Simpan ke dalam direktori run baru agar siap dieksekusi maupun digunakan berulang
            import_run_id = "import_" + datetime.now().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())[:4]
            import_run_dir = get_run_dir(import_run_id)
            scrap_dir = os.path.join(import_run_dir, "scrap")
            os.makedirs(scrap_dir, exist_ok=True)

            all_csv_path = os.path.join(scrap_dir, "youtube_comments_all_videos.csv")
            df_norm.to_csv(all_csv_path, index=False, encoding="utf-8-sig")

            # Buat metadata video
            meta_rows = []
            for vid, vdf in df_norm.groupby("video_id"):
                meta_rows.append({
                    "video_id": str(vid),
                    "video_title": str(vdf["video_title"].iloc[0]),
                    "channel_name": str(vdf["channel_name"].iloc[0]),
                    "video_url": f"https://www.youtube.com/watch?v={vid}",
                    "published_at": str(vdf["created_at"].iloc[0])[:10],
                    "views": int(len(vdf) * 100),
                    "video_likes": int(vdf["like_count"].sum()),
                })
            if meta_rows:
                pd.DataFrame(meta_rows).to_csv(os.path.join(scrap_dir, "youtube_videos_meta_all.csv"), index=False, encoding="utf-8-sig")
                pd.DataFrame([meta_rows[0]]).to_csv(os.path.join(scrap_dir, f"youtube_video_meta_{meta_rows[0]['video_id']}.csv"), index=False, encoding="utf-8-sig")

            manifest = HistoryService.generate_forensic_manifest(import_run_dir, import_run_id)
            sha256_val = manifest.get("primary_sha256", "")

            return {
                "success": True,
                "run_id": import_run_id,
                "comment_count": len(df_norm),
                "video_count": len(meta_rows),
                "title": default_vtitle,
                "sha256_hash": sha256_val,
                "message": f"Berhasil mengimpor {len(df_norm)} bukti komentar ({len(meta_rows)} sumber/video). Segel SHA-256: {sha256_val[:16]}...",
            }
        except Exception as e:
            return {"success": False, "error": f"Gagal memproses berkas korpus: {str(e)}"}

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
                if res.get("cib_score") is not None:
                    res["cib_score"] = float(res["cib_score"])
                if res.get("polarization_index") is not None:
                    res["polarization_index"] = float(res["polarization_index"])
                return res

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
                        "sha256_hash": str(data.get("sha256_hash", "")),
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
                subprocess.Popen(["open", folder])
            else:
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

            settings = AppSettings.load()
            provider = str(settings.get("provider") or settings.get("ai_provider") or "gemini").lower().strip()
            model = str(settings.get("model") or settings.get("ai_model") or "").strip()
            api_key = str(settings.get("api_key") or settings.get(f"{provider}_api_key") or "").strip()
            if not api_key:
                api_key = str(
                    settings.get("custom_api_key")
                    or settings.get("gemini_api_key")
                    or settings.get("openrouter_api_key")
                    or ""
                ).strip()

            if provider == "custom":
                custom_base = str(
                    settings.get("base_url") or settings.get("custom_base_url") or "http://127.0.0.1:11434/v1"
                ).strip()
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
                    if any(k in t_low for k in ["papua merdeka", "opm", "kkb", "pemberontak", "makzulkan", "hancurkan tni", "lumpuh", "diretas", "pencitraan"]):
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

            botnets = IntelligenceService.calculate_coordinated_bot_networks(
                df,
                min_accounts=2,
                min_length=25,
                custom_whitelist=custom_whitelist,
                custom_threats=custom_threats,
            )

            flagged = IntelligenceService.calculate_flagged_accounts(
                df,
                custom_whitelist=custom_whitelist,
                custom_threats=custom_threats,
            )

            cib_metrics = IntelligenceService.calculate_cib_metrics(
                df,
                custom_whitelist=custom_whitelist,
                custom_threats=custom_threats,
            )

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
