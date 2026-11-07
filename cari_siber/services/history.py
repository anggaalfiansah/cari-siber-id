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
                    if not r.get("sha256_hash") and r.get("run_dir") and os.path.isdir(r["run_dir"]):
                        manifest_path = os.path.join(r["run_dir"], "json", "forensic_manifest.json")
                        if os.path.exists(manifest_path):
                            try:
                                with open(manifest_path, "r", encoding="utf-8") as mf:
                                    mdata = json.load(mf)
                                    r["sha256_hash"] = mdata.get("primary_sha256", "")
                            except Exception:
                                pass
                        else:
                            manifest = HistoryService.generate_forensic_manifest(r["run_dir"], r.get("id", ""))
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
