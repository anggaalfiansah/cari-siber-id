import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from cari_siber.paths import get_history_db_path


class HistoryService:
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
                    run_dir TEXT NOT NULL
                )
            """)
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
    ):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with HistoryService._get_connection() as conn:
            conn.execute("""
                UPDATE runs
                SET status = 'COMPLETED',
                    video_title = ?,
                    channel_name = ?,
                    total_comments = ?,
                    cib_score = ?,
                    cib_level = ?,
                    polarization_index = ?,
                    completed_at = ?
                WHERE id = ?
            """, (video_title, channel_name, total_comments, cib_score, cib_level, polarization_index, now_str, run_id))
            conn.commit()

    @staticmethod
    def list_runs() -> List[Dict[str, Any]]:
        try:
            with HistoryService._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM runs ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
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
