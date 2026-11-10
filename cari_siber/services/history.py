import sqlite3
import os
import json
import hashlib
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from cari_siber.paths import get_history_db_path


class HistoryService:
    @staticmethod
    def compute_sha256(file_path: str) -> str:
        """Menghitung hash kriptografi SHA-256 untuk integritas barang bukti digital (Chain of Custody)."""
        if not file_path or not os.path.exists(file_path):
            return ""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""

    @staticmethod
    def generate_forensic_manifest(run_dir: str, run_id: str = "") -> Dict[str, Any]:
        """Menghasilkan forensic_manifest.json berisi segel SHA-256 korpus mentah & final."""
        if not run_id:
            run_id = os.path.basename(run_dir)
        scrap_dir = os.path.join(run_dir, "scrap")
        csv_dir = os.path.join(run_dir, "csv")
        json_dir = os.path.join(run_dir, "json")
        os.makedirs(json_dir, exist_ok=True)

        raw_csv = os.path.join(scrap_dir, "youtube_comments_all_videos.csv")
        if not os.path.exists(raw_csv) and os.path.isdir(scrap_dir):
            cand = [
                os.path.join(scrap_dir, f)
                for f in os.listdir(scrap_dir)
                if f.startswith("youtube_comments_") and f.endswith(".csv") and "meta" not in f
            ]
            if cand:
                raw_csv = cand[0]

        final_csv = os.path.join(csv_dir, "mapping_review_topic_youtube_final.csv")
        if not os.path.exists(final_csv):
            final_csv = os.path.join(csv_dir, "mapping_review_topic_youtube_raw.csv")

        raw_hash = HistoryService.compute_sha256(raw_csv)
        final_hash = HistoryService.compute_sha256(final_csv)
        primary_hash = raw_hash or final_hash

        manifest = {
            "run_id": run_id,
            "sealed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "algorithm": "SHA-256",
            "primary_sha256": primary_hash,
            "raw_corpus_sha256": raw_hash,
            "raw_corpus_file": os.path.basename(raw_csv) if os.path.exists(raw_csv) else "",
            "final_corpus_sha256": final_hash,
            "final_corpus_file": os.path.basename(final_csv) if os.path.exists(final_csv) else "",
            "chain_of_custody_status": "VERIFIED_IMMUTABLE" if primary_hash else "UNSEALED",
        }
        try:
            with open(os.path.join(json_dir, "forensic_manifest.json"), "w", encoding="utf-8") as mf:
                json.dump(manifest, mf, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return manifest

    @staticmethod
    def _get_connection():
        db_path = get_history_db_path()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init_db():
        with HistoryService._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    target_url TEXT NOT NULL,
                    video_title TEXT DEFAULT '',
                    channel_name TEXT DEFAULT '',
                    total_comments INTEGER DEFAULT 0,
                    cib_score REAL DEFAULT 0.0,
                    cib_level TEXT DEFAULT 'LOW',
                    polarization_index REAL DEFAULT 0.0,
                    status TEXT NOT NULL,
                    error_message TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    completed_at TEXT DEFAULT '',
                    run_dir TEXT NOT NULL,
                    sha256_hash TEXT DEFAULT ''
                )
            """)
            try:
                conn.execute("ALTER TABLE runs ADD COLUMN sha256_hash TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass
            # Bersihkan status 'RUNNING' zombie yang tertinggal jika aplikasi ditutup paksa
            conn.execute("""
                UPDATE runs
                SET status = 'FAILED', error_message = 'Aplikasi ditutup atau terhenti sebelum analisis selesai.'
                WHERE status = 'RUNNING'
            """)
            conn.commit()

            # Daftarkan run prebuilt bawaan sebagai contoh siap pakai
            HistoryService.seed_prebuilt_runs(conn)

    @staticmethod
    def seed_prebuilt_runs(conn=None):
        """
        Otomatis mendaftarkan korpus/analisis prebuilt bawaan (contoh multi-video yang sudah siap)
        ke dalam basis data riwayat operasi (history.db) sehingga pengguna dapat langsung melihat
        contoh hasil SITREP tanpa perlu melakukan scraping terlebih dahulu.
        """
        from cari_siber.paths import get_prebuilt_runs_dir, get_runs_dir

        prebuilt_dir = get_prebuilt_runs_dir()
        if not os.path.exists(prebuilt_dir):
            return

        KNOWN_PREBUILTS = {
            "20261108_232226_5bbf0f": {
                "target_url": 'Kata Kunci: "Penyadapan Presiden" (98 Video)',
                "video_title": 'Kata Kunci Pencarian: "Penyadapan Presiden" (98 Video)',
                "channel_name": "98 Video Lintas 35 Kanal (KOMPASTV, SINDOnews, METRO TV, +32 kanal lainnya)",
                "total_comments": 46183,
                "cib_score": 0.08,
                "cib_level": "LOW",
                "polarization_index": 0.72,
                "created_at": "2026-11-08 23:22:26",
                "completed_at": "2026-11-09 00:31:20",
                "sha256_hash": "429f3cd79c07262dda720053a76624638feae363834fe16e7ecd5423635de98d",
            },
            "20261108_013609_1a64cc": {
                "target_url": 'Kata Kunci: "PAPUA Propaganda Separatis Separatisme KKB" (34 Video)',
                "video_title": 'Kata Kunci Pencarian: "PAPUA Propaganda Separatis Separatisme KKB" (34 Video)',
                "channel_name": "34 Video Lintas 26 Kanal (CNN Indonesia, The Papua Darkside, BBC News Indonesia, +23 kanal lainnya)",
                "total_comments": 5729,
                "cib_score": 0.14,
                "cib_level": "LOW",
                "polarization_index": 0.26,
                "created_at": "2026-11-08 01:36:09",
                "completed_at": "2026-11-08 01:49:44",
                "sha256_hash": "6aae164d1a63e300b2253f99bd32a8b94d8f0a91f46667b1ff30612583e25a38",
            },
        }

        should_close = False
        if conn is None:
            conn = HistoryService._get_connection()
            should_close = True

        try:
            for rid in os.listdir(prebuilt_dir):
                pb_path = os.path.join(prebuilt_dir, rid)
                if not os.path.isdir(pb_path):
                    continue

                user_run_dir = os.path.join(get_runs_dir(), rid)
                if not os.path.exists(user_run_dir):
                    try:
                        shutil.copytree(pb_path, user_run_dir, dirs_exist_ok=True)
                    except Exception:
                        user_run_dir = pb_path

                meta = KNOWN_PREBUILTS.get(rid, {})
                v_title = meta.get("video_title")
                c_name = meta.get("channel_name")
                tot_c = meta.get("total_comments")
                cib_s = meta.get("cib_score", 0.0)
                cib_l = meta.get("cib_level", "LOW")
                pol_i = meta.get("polarization_index", 0.0)
                c_at = meta.get("created_at", "2026-11-08 00:00:00")
                done_at = meta.get("completed_at", "2026-11-08 01:00:00")
                sha_hash = meta.get("sha256_hash", "")
                t_url = meta.get("target_url", v_title)

                if not v_title:
                    eda_f = os.path.join(pb_path, "json", "youtube_eda_summary.json")
                    if os.path.exists(eda_f):
                        try:
                            with open(eda_f, "r", encoding="utf-8") as ef:
                                eda_d = json.load(ef)
                                m = eda_d.get("meta", {})
                                v_title = m.get("video_title", "Prebuilt Corpus")
                                c_name = m.get("channel_name", "")
                                tot_c = int(m.get("total_comments", 0))
                        except Exception:
                            pass
                    manifest_f = os.path.join(pb_path, "json", "forensic_manifest.json")
                    if os.path.exists(manifest_f):
                        try:
                            with open(manifest_f, "r", encoding="utf-8") as mf:
                                sha_hash = json.load(mf).get("primary_sha256", "")
                        except Exception:
                            pass

                cur = conn.execute("SELECT id FROM runs WHERE id = ?", (rid,))
                existing = cur.fetchone()
                if not existing:
                    conn.execute("""
                        INSERT INTO runs (
                            id, target_url, video_title, channel_name, total_comments,
                            cib_score, cib_level, polarization_index, status,
                            created_at, completed_at, run_dir, sha256_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', ?, ?, ?, ?)
                    """, (rid, t_url, v_title, c_name, tot_c, cib_s, cib_l, pol_i, c_at, done_at, user_run_dir, sha_hash))
                else:
                    conn.execute("""
                        UPDATE runs
                        SET video_title = ?, channel_name = ?, sha256_hash = ?, status = 'COMPLETED', run_dir = ?
                        WHERE id = ?
                    """, (v_title, c_name, sha_hash, user_run_dir, rid))
            conn.commit()
        except Exception as e:
            print(f"[HISTORY WARNING] Gagal seeding prebuilt runs: {e}")
        finally:
            if should_close:
                conn.close()

    @staticmethod
    def create_run(run_id: str, target_url: str, run_dir: str) -> Dict[str, Any]:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with HistoryService._get_connection() as conn:
            conn.execute("""
                INSERT INTO runs (id, target_url, status, created_at, run_dir)
                VALUES (?, ?, 'RUNNING', ?, ?)
            """, (run_id, target_url, now_str, run_dir))
            conn.commit()
        return HistoryService.get_run(run_id)

    @staticmethod
    def update_run_status(run_id: str, status: str, error: str = ""):
        with HistoryService._get_connection() as conn:
            conn.execute("""
                UPDATE runs
                SET status = ?, error_message = ?
                WHERE id = ?
            """, (status, error, run_id))
            conn.commit()

    @staticmethod
    def complete_run(
        run_id: str,
        video_title: str,
        channel_name: str,
        total_comments: int,
        cib_score: float,
        cib_level: str,
        polarization_index: float,
        sha256_hash: str = "",
    ):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with HistoryService._get_connection() as conn:
            try:
                conn.execute("ALTER TABLE runs ADD COLUMN sha256_hash TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass
            conn.execute("""
                UPDATE runs
                SET status = 'COMPLETED',
                    video_title = ?,
                    channel_name = ?,
                    total_comments = ?,
                    cib_score = ?,
                    cib_level = ?,
                    polarization_index = ?,
                    completed_at = ?,
                    sha256_hash = ?
                WHERE id = ?
            """, (video_title, channel_name, total_comments, cib_score, cib_level, polarization_index, now_str, sha256_hash, run_id))
            conn.commit()

    @staticmethod
    def update_cib_metrics(run_id: str, cib_score: float, cib_level: str):
        with HistoryService._get_connection() as conn:
            conn.execute("""
                UPDATE runs
                SET cib_score = ?,
                    cib_level = ?
                WHERE id = ?
            """, (cib_score, cib_level, run_id))
            conn.commit()

    @staticmethod
    def list_runs() -> List[Dict[str, Any]]:
        try:
            with HistoryService._get_connection() as conn:
                try:
                    conn.execute("ALTER TABLE runs ADD COLUMN sha256_hash TEXT DEFAULT ''")
                except sqlite3.OperationalError:
                    pass
                cursor = conn.execute("SELECT * FROM runs ORDER BY created_at DESC")
                rows = [dict(row) for row in cursor.fetchall()]
                for r in rows:
                    r_dir = r.get("run_dir", "")
                    if r_dir and os.path.isdir(r_dir):
                        # Normalisasi retroaktif judul multi-video lama ("Multi-Video Corpus (...): <judul 1 video>")
                        if str(r.get("video_title", "")).startswith("Multi-Video Corpus ("):
                            all_meta_csv = os.path.join(r_dir, "scrap", "youtube_videos_meta_all.csv")
                            if os.path.exists(all_meta_csv):
                                try:
                                    import pandas as pd
                                    from cari_siber.engine.pipelines.youtube_comments.pipeline_eda import infer_corpus_keyword_and_channels
                                    m_df = pd.read_csv(all_meta_csv)
                                    if len(m_df) > 1:
                                        saved_kw = ""
                                        r_ctx = os.path.join(r_dir, "json", "run_context.json")
                                        if os.path.exists(r_ctx):
                                            with open(r_ctx, "r", encoding="utf-8") as rcf:
                                                saved_kw = str(json.load(rcf).get("search_keyword", "")).strip()
                                        ident = infer_corpus_keyword_and_channels(m_df.to_dict(orient="records"), search_keyword=saved_kw)
                                        r["video_title"] = ident.get("video_title", r["video_title"])
                                        r["channel_name"] = ident.get("channel_name", r.get("channel_name", ""))
                                        conn.execute(
                                            "UPDATE runs SET video_title = ?, channel_name = ? WHERE id = ?",
                                            (r["video_title"], r["channel_name"], r["id"]),
                                        )
                                        conn.commit()
                                except Exception:
                                    pass

                        if not r.get("sha256_hash"):
                            manifest_path = os.path.join(r_dir, "json", "forensic_manifest.json")
                            if os.path.exists(manifest_path):
                                try:
                                    with open(manifest_path, "r", encoding="utf-8") as mf:
                                        mdata = json.load(mf)
                                        r["sha256_hash"] = mdata.get("primary_sha256", "")
                                except Exception:
                                    pass
                            else:
                                manifest = HistoryService.generate_forensic_manifest(r_dir, r.get("id", ""))
                                r["sha256_hash"] = manifest.get("primary_sha256", "")
                            if r.get("sha256_hash"):
                                try:
                                    conn.execute("UPDATE runs SET sha256_hash = ? WHERE id = ?", (r["sha256_hash"], r["id"]))
                                    conn.commit()
                                except Exception:
                                    pass
                return rows
        except Exception as e:
            print(f"[HISTORY ERROR] Gagal membaca riwayat: {e}")
            return []

    @staticmethod
    def get_run(run_id: str) -> Optional[Dict[str, Any]]:
        try:
            with HistoryService._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"[HISTORY ERROR] Gagal membaca run ({run_id}): {e}")
            return None

    @staticmethod
    def delete_run(run_id: str, delete_files: bool = True) -> bool:
        run = HistoryService.get_run(run_id)
        if not run:
            return False
        with HistoryService._get_connection() as conn:
            conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
            conn.commit()
        if delete_files and run.get("run_dir") and os.path.exists(run["run_dir"]):
            try:
                shutil.rmtree(run["run_dir"], ignore_errors=True)
            except Exception:
                pass
        return True
