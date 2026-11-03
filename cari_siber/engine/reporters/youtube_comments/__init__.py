import os
import json
import re

from .xlsx import export_xlsx
from cari_siber.engine.core.exceptions import PipelineError


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def run_exporter(output_dir: str = None) -> str:
    """
    Mengekspor laporan analisis YouTube ke dalam format Excel (.xlsx).
    Mengembalikan path file xlsx yang dihasilkan.
    """
    from cari_siber.engine.core.config import AppConfig

    run_output_dir = output_dir or AppConfig.OUTPUT_YOUTUBE_DIR
    csv_dir = os.path.join(run_output_dir, "csv")
    reports_dir = os.path.join(run_output_dir, "reports")

    os.makedirs(reports_dir, exist_ok=True)

    json_path = os.path.join(run_output_dir, "json", "youtube_eda_summary.json")
    if not os.path.exists(json_path):
        raise PipelineError(f"File data {json_path} tidak ditemukan untuk ekspor.")

    with open(json_path, "r", encoding="utf-8") as f:
        eda_data = json.load(f)

    app_name = eda_data.get("meta", {}).get("app_name", "YouTube Video")
    app_slug = slugify(app_name)[:60].strip("-")

    xlsx_path = os.path.join(reports_dir, f"report_{app_slug}.xlsx")
    export_xlsx(eda_data, xlsx_path, csv_dir)
    return xlsx_path


__all__ = ["export_xlsx", "run_exporter", "slugify"]
