import os
import pandas as pd
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


def export_xlsx(eda_data: dict, output_path: str, csv_dir: str):
    """Mengekspor data analisis YouTube ke dalam file Excel dengan multi-sheet & styling premium."""
    if not HAS_OPENPYXL:
        print("[WARNING] openpyxl tidak tersedia. Ekspor Excel dilewati.")
        return False

    print(f"[PROCESS] Mengekspor laporan Excel ke: {output_path}")

    wb = openpyxl.Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)

    font_family = "Segoe UI"

    color_primary = "7F1D1D"    # Deep YouTube crimson/indigo
    color_accent = "B91C1C"
    color_light_gray = "FEF2F2"
    color_border = "FECACA"

    font_title = Font(name=font_family, size=16, bold=True, color=color_primary)
    font_section = Font(name=font_family, size=11, bold=True, color=color_accent)
    font_header = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    font_body = Font(name=font_family, size=10, color="000000")
    font_bold = Font(name=font_family, size=10, bold=True, color="000000")

    fill_header = PatternFill(start_color=color_primary, end_color=color_primary, fill_type="solid")
    fill_zebra = PatternFill(start_color=color_light_gray, end_color=color_light_gray, fill_type="solid")
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    thin_border_side = Side(style="thin", color=color_border)
    border_all = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center", wrap_text=True)

    # ----------------------------------------------------
    # Sheet 1: Ringkasan Eksekutif
    # ----------------------------------------------------
    ws_dash = wb.create_sheet(title="Ringkasan Eksekutif")
    ws_dash.views.sheetView[0].showGridLines = True

    ws_dash["A1"] = "LAPORAN EXECUTIVE SUMMARY ANALISIS SENTIMEN YOUTUBE"
    ws_dash["A1"].font = font_title

    overview = eda_data.get("overview", {})
    meta = eda_data.get("meta", {})
    if "app_name" not in meta:
        meta["app_name"] = "YouTube Video"
    if "date_range" not in meta:
        meta["date_range"] = {"start": "-", "end": "-"}

    ws_dash["A3"] = "Metadata Laporan"
    ws_dash["A3"].font = font_section

    metadata_rows = [
        ("Judul Video", meta.get("app_name", "YouTube")),
        ("Channel", meta.get("channel_name", "YouTube Channel")),
        ("ID Video", meta.get("video_id", "-")),
        ("Periode Komentar", f"{meta.get('date_range', {}).get('start', '')} s/d {meta.get('date_range', {}).get('end', '')}"),
        ("Tanggal Ekspor", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Total Komentar Diolah", overview.get("total_comments", 0)),
    ]

    for idx, (label, val) in enumerate(metadata_rows, start=4):
        ws_dash[f"A{idx}"] = label
        ws_dash[f"B{idx}"] = val
        ws_dash[f"A{idx}"].font = font_bold
        ws_dash[f"B{idx}"].font = font_body
        ws_dash[f"A{idx}"].border = border_all
        ws_dash[f"B{idx}"].border = border_all
        if label == "Total Komentar Diolah":
            ws_dash[f"B{idx}"].number_format = "#,##0"
            ws_dash[f"B{idx}"].font = font_bold

    ws_dash["D3"] = "Statistik & Ringkasan Sentimen"
    ws_dash["D3"].font = font_section

    sent_dist = overview.get("sentiment_distribution", {})

    metrics = [
        ("Komentar Positif", sent_dist.get("Positif", {}).get("count", 0), "Jumlah interaksi bernada dukungan/apresiasi"),
        ("Komentar Netral", sent_dist.get("Netral", {}).get("count", 0), "Jumlah interaksi netral/pertanyaan"),
        ("Komentar Negatif", sent_dist.get("Negatif", {}).get("count", 0), "Jumlah interaksi bernada kritik/keluhan"),
        ("Total Komentar", overview.get("total_comments", 0), "Total komentar terklasifikasi"),
        ("Rasio Sentimen Positif", sent_dist.get("Positif", {}).get("pct", 0) / 100 if sent_dist.get("Positif") else 0, "Persentase sentimen positif"),
        ("Rasio Sentimen Negatif", sent_dist.get("Negatif", {}).get("pct", 0) / 100 if sent_dist.get("Negatif") else 0, "Persentase kritik/keluhan penonton"),
        ("Rata-rata Likes (Positif)", sent_dist.get("Positif", {}).get("avg_like_count", 0), "Rata-rata likes per komentar positif"),
        ("Rata-rata Likes (Negatif)", sent_dist.get("Negatif", {}).get("avg_like_count", 0), "Rata-rata likes per komentar negatif"),
    ]

    ws_dash["D4"] = "Metrik/KPI"
    ws_dash["E4"] = "Nilai Aktual"
    ws_dash["F4"] = "Keterangan/Penjelasan"

    for col_name in ["D", "E", "F"]:
        cell = ws_dash[f"{col_name}4"]
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_all

    for idx, (metric_name, val, desc) in enumerate(metrics, start=5):
        ws_dash[f"D{idx}"] = metric_name
        ws_dash[f"E{idx}"] = val
        ws_dash[f"F{idx}"] = desc

        ws_dash[f"D{idx}"].font = font_body
        ws_dash[f"E{idx}"].font = font_bold
        ws_dash[f"F{idx}"].font = font_body

        ws_dash[f"D{idx}"].border = border_all
        ws_dash[f"E{idx}"].border = border_all
        ws_dash[f"F{idx}"].border = border_all

        if "Komentar" in metric_name and "Rasio" not in metric_name:
            ws_dash[f"E{idx}"].number_format = "#,##0"
            ws_dash[f"E{idx}"].alignment = align_right
        elif "Rasio" in metric_name:
            ws_dash[f"E{idx}"].number_format = "0.00%"
            ws_dash[f"E{idx}"].alignment = align_right
        elif "Likes" in metric_name:
            ws_dash[f"E{idx}"].number_format = "#,##0.00"
            ws_dash[f"E{idx}"].alignment = align_right

        if idx % 2 == 0:
            ws_dash[f"D{idx}"].fill = fill_zebra
            ws_dash[f"E{idx}"].fill = fill_zebra
            ws_dash[f"F{idx}"].fill = fill_zebra

    for col_letter in ["A", "B", "C", "D", "E", "F"]:
        max_len = 0
        max_row = 10 if col_letter in ["A", "B", "C"] else 15
        for row in range(1, max_row + 1):
            val_str = str(ws_dash[f"{col_letter}{row}"].value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws_dash.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 55)

    def write_csv_sheet(sheet_title, csv_filename, title_text, fill_color="991B1B"):
        csv_path = os.path.join(csv_dir, csv_filename)
        if not os.path.exists(csv_path):
            return
        df = pd.read_csv(csv_path).fillna("")
        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = title_text
        ws["A1"].font = Font(name=font_family, size=14, bold=True, color=color_primary)

        header_fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

        headers = list(df.columns)
        for col_num, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col_num)
            cell.value = header.replace("_", " ").title()
            cell.font = font_header
            cell.fill = header_fill
            cell.alignment = align_center
            cell.border = border_all

        ws.row_dimensions[3].height = 28

        for row_num, row_data in enumerate(df.values, start=4):
            ws.row_dimensions[row_num].height = 20
            is_zebra = row_num % 2 == 0
            row_fill = fill_zebra if is_zebra else fill_white

            for col_num, cell_value in enumerate(row_data, start=1):
                cell = ws.cell(row=row_num, column=col_num)
                col_name = str(df.columns[col_num - 1]).lower()

                # Sanitasi Formula Injection untuk mencegah eksekusi macro/formula Excel dari input teks pengguna
                if isinstance(cell_value, str) and cell_value.startswith(("=", "+", "-", "@")):
                    cell.value = f"'{cell_value}"
                else:
                    cell.value = cell_value

                cell.font = font_body
                cell.border = border_all
                cell.fill = row_fill

                if isinstance(cell_value, (int, float)):
                    cell.alignment = align_right
                    if isinstance(cell_value, float):
                        # Format persentase hanya untuk kolom rasio/proporsi/share
                        if any(term in col_name for term in ["ratio", "share", "pct", "percent", "persen"]) and 0.0 <= cell_value <= 1.0:
                            cell.number_format = "0.00%"
                        else:
                            cell.number_format = "#,##0.00"
                    else:
                        cell.number_format = "#,##0"
                else:
                    cell.alignment = align_left

        for col_idx, col in enumerate(ws.columns, start=1):
            col_name = str(df.columns[col_idx - 1]) if col_idx <= len(df.columns) else ""
            max_len = len(col_name)
            # Sample baris secukupnya (maks 50) agar penentuan lebar kolom tidak lambat pada data besar
            for cell in list(col)[2:52]:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 60)

    write_csv_sheet("Komparasi Video", "cross_video_comparison_matrix.csv", "Matriks Komparasi Lintas Video & Kanal", fill_color="0284C7")
    write_csv_sheet("Buzzer & CIB Lintas Video", "cross_video_cib_buzzers.csv", "Daftar Akun Buzzer Terdeteksi Aktif di Multi-Video (+Link Profil)", fill_color="B91C1C")
    write_csv_sheet("Detail Kategori Topik", "business_category_youtube_summary.csv", "Detail Distribusi Topik & Sentimen", fill_color="991B1B")
    write_csv_sheet("Engagement Metrics", "youtube_engagement_metrics.csv", "Analisis Interaksi & Metrik Engagement", fill_color="1E3A8A")
    write_csv_sheet("Ulasan Low Confidence", "review_youtube_low_confidence.csv", "Daftar Komentar dengan Tingkat Keyakinan Rendah (< 0.5 atau Ambigu)", fill_color="B91C1C")
    write_csv_sheet("Semua Komentar Final", "mapping_review_topic_youtube_final.csv", "Semua Komentar Final Terklasifikasi", fill_color="312E81")

    wb.save(output_path)
    print(f"[SUCCESS] Berhasil menyimpan file Excel: {output_path}")
    return True
