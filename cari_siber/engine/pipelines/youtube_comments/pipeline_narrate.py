from cari_siber.engine.core.exceptions import PipelineError
"""
==============================================================================
LANGKAH 7 (OPSIONAL): LAPORAN PERKIRAAN INTELIJEN SIBER (KIRKA SIBER SOSIAL)
==============================================================================
Menghasilkan Laporan Perkiraan Intelijen Siber (Kirka Siber Sosial) (`narrative_insights.md`)
berdasarkan data telemetri dan statistik `youtube_eda_summary.json`.
==============================================================================
"""

import json
import os
import sys
from datetime import datetime

from cari_siber.engine.core.ai_client import generate_text
from cari_siber.engine.core.agentic_gates import run_report_gate
from cari_siber.engine.core.config import AppConfig


def _slim_json(data: dict) -> dict:
    slimmed = {
        "meta": data.get("meta", {}),
        "overview": data.get("overview", {}),
        "video_summary": {
            "video_title": data.get("video_analysis", {}).get("video_title", ""),
            "channel_name": data.get("video_analysis", {}).get("channel_name", ""),
            "views": data.get("video_analysis", {}).get("total_views", 0),
            "video_likes": data.get("video_analysis", {}).get("video_likes", 0),
            "top_comments": data.get("video_analysis", {}).get("top_comments", [])[:5],
        },
        "topic_analysis": {},
        "official_response": data.get("official_response", {}),
        "engagement_analysis": {
            "top_engaging_topics": data.get("engagement_analysis", {}).get("top_engaging_topics", [])[:10]
        },
        "trends": data.get("trends", [])[-12:],
        "spike_detection": data.get("spike_detection", {}),
        "keyword_analysis": {
            "Negatif": data.get("keyword_analysis", {}).get("Negatif", [])[:10],
            "Positif": data.get("keyword_analysis", {}).get("Positif", [])[:10],
        },
    }

    # Truncate top comments in video_summary
    if "video_summary" in slimmed and "top_comments" in slimmed["video_summary"]:
        truncated_top = []
        for tc in slimmed["video_summary"]["top_comments"][:3]:
            if isinstance(tc, dict):
                c_text = str(tc.get("comment_text") or tc.get("text") or tc.get("comment", "")).strip()
                truncated_top.append({
                    "comment": c_text[:140],
                    "like_count": tc.get("like_count", 0),
                })
        slimmed["video_summary"]["top_comments"] = truncated_top

    topic_analysis = data.get("topic_analysis", {})
    for sent, v in topic_analysis.items():
        if isinstance(v, dict):
            categories = v.get("categories", [])
            slim_cats = []
            for cat in categories[:5]:
                raw_samples = cat.get("sample_comments", [])
                clean_sample = [str(raw_samples[0])[:100]] if raw_samples else []
                cat_name = cat.get("threat_domain") or cat.get("business_category") or cat.get("name")
                slim_cats.append(
                    {
                        "name": cat_name,
                        "threat_domain": cat_name,
                        "comment_count": cat.get("comment_count"),
                        "total_likes": cat.get("total_likes"),
                        "sub_issue": cat.get("sub_issue"),
                        "sample_comment": clean_sample[0] if clean_sample else "",
                    }
                )
            slimmed["topic_analysis"][sent] = {
                "total_categories": v.get("total_categories", 0),
                "total_comments": v.get("total_comments", 0),
                "categories": slim_cats,
            }
    return slimmed


def build_prompt(json_data: str, target_name: str) -> str:
    return f"""Anda adalah Perwira Analis Intelijen Kognitif & Pertahanan Ruang Siber PUSSIBERAD TNI AD.
Tugas Anda adalah menyusun "Laporan Perkiraan Intelijen Siber (Kirka Siber Sosial)" mengenai dinamika opini dan potensi ancaman operasi informasi pada target: "{target_name}".

Berikut adalah data telemetri dan statistik hasil ekstraksi intelijen:
{json_data}

Susun Laporan Eksekutif dengan struktur doktrin pertahanan berikut:
1. SITUASI RUANG SIBER & INDEKS POLARISASI (Overview ancaman, sentimen publik, dan deteksi Silent Majority vs Loud Minority)
2. IDENTIFIKASI OPERASI INFORMASI TERKOORDINASI / CIB (Analisis jaringan bot, copypasta, dan pola waktu burst akun inotentik)
3. PEMETAAN NARASI ANCAMAN KOGNITIF & KORELASI ANCAMAN INFRASTRUKTUR IT/OT (Pemetaan isu berdasar domain Disinformasi, SARA, Delegitimasi Komando/Negara, serta korelasi potensi eskalasi narasi siber sosial terhadap gangguan operasi komando, doxing personel, atau ancaman siber pada infrastruktur IT/OT pertahanan TNI AD)
4. DISARM FRAMEWORK MAPPING (Pemetaan taktik dan teknik ancaman berdasarkan standar DISARM/AMITT)
5. REKOMENDASI TINDAKAN PENANGKALAN & KONTRA-NARASI (Langkah taktis terukur untuk Satuan Penerangan, Puskodal, dan Tim Siber TNI AD)

Gunakan terminologi intelijen pertahanan yang formal, tegas, analitis, dan berbasis angka faktual.
"""


def run_narrator(config_override=None):
    print("=" * 70)
    print("LANGKAH 7 (OPSIONAL): LAPORAN PERKIRAAN INTELIJEN SIBER (KIRKA SIBER SOSIAL)")
    print("=" * 70)

    cfg = config_override or {}
    output_dir = cfg.get("OUTPUT_DIR", AppConfig.OUTPUT_YOUTUBE_DIR)
    ai_provider = cfg.get("AI_PROVIDER", AppConfig.AI_PROVIDER)
    ai_model = cfg.get("AI_MODEL", AppConfig.AI_MODEL)
    narration_model = cfg.get("AI_NARRATION_MODEL", AppConfig.AI_NARRATION_MODEL)
    gemini_api_key = cfg.get("GEMINI_API_KEY", AppConfig.GEMINI_API_KEY)
    openrouter_api_key = cfg.get("OPENROUTER_API_KEY", AppConfig.OPENROUTER_API_KEY)
    edgeone_api_key = cfg.get("EDGEONE_API_KEY", AppConfig.EDGEONE_API_KEY)
    custom_api_key = cfg.get("CUSTOM_API_KEY", AppConfig.CUSTOM_API_KEY)

    model_name = narration_model if narration_model else ai_model

    json_dir = os.path.join(output_dir, "json")
    input_path = os.path.join(json_dir, "youtube_eda_summary.json")
    if not os.path.exists(input_path):
        print(f"[ERROR] File tidak ditemukan: {input_path}")
        print("[INFO] Pastikan langkah 5 (EDA) sudah dijalankan terlebih dahulu.")
        raise PipelineError("Tahap pipeline dihentikan karena kesalahan.")

    print(f"[INFO] Membaca data EDA dari: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise PipelineError("File youtube_eda_summary.json bukan JSON yang valid: {e}")

    app_name = data.get("meta", {}).get("app_name", AppConfig.YOUTUBE_APP_NAME)
    slimmed_data = _slim_json(data)
    json_payload = json.dumps(slimmed_data, ensure_ascii=False, indent=2)

    print(f"[INFO] Ukuran data EDA asli: {os.path.getsize(input_path):,} bytes")
    print(f"[INFO] Ukuran data EDA disederhanakan: {len(json_payload):,} karakter")

    if ai_provider == "gemini" and not gemini_api_key:
        print("[WARNING] GEMINI_API_KEY tidak diset di konfigurasi. Melewati pembuatan narasi AI.")
        return
    elif ai_provider == "openrouter" and not openrouter_api_key:
        print("[WARNING] OPENROUTER_API_KEY tidak diset di konfigurasi. Melewati pembuatan narasi AI.")
        return
    elif ai_provider == "edgeone" and not edgeone_api_key:
        print("[WARNING] EDGEONE_API_KEY tidak diset di konfigurasi. Melewati pembuatan narasi AI.")
        return
    elif ai_provider == "custom" and not custom_api_key:
        custom_base_url = str(cfg.get("CUSTOM_BASE_URL", AppConfig.CUSTOM_BASE_URL) or "").lower()
        is_local = any(h in custom_base_url for h in ["127.0.0.1", "localhost", "0.0.0.0", "192.168.", "10.", "172."])
        if not is_local:
            print("[WARNING] CUSTOM_API_KEY tidak diset di konfigurasi. Melewati pembuatan narasi AI.")
            return

    prompt = build_prompt(json_payload, app_name)

    print(f"\n[INFO] Menghasilkan Laporan Perkiraan Intelijen Siber (Kirka) menggunakan model: {model_name}...")
    try:
        report_md = generate_text(
            prompt=prompt,
            provider=ai_provider,
            model=model_name,
            timeout=180.0,
            max_retries=2,
        )
    except Exception as e:
        print(f"[ERROR] Gagal memanggil API LLM: {e}")
        return

    if not report_md:
        print("[WARNING] Hasil narasi kosong. Melewati penyimpanan narasi dan melanjutkan ke tahap berikutnya.")
        return

    reports_dir = os.path.join(output_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"narrative_insights_{timestamp}.md"
    output_path = os.path.join(reports_dir, output_filename)
    latest_path = os.path.join(reports_dir, "narrative_insights.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\n[SUCCESS] Laporan Kirka Siber Sosial berhasil dibuat dan disimpan di:\n  - {output_path}\n  - {latest_path}")
    run_report_gate(
        narrative_md_path=latest_path,
        eda_json_path=input_path,
        slimmed_eda_data=slimmed_data,
        app_name=app_name,
        output_dir=output_dir,
        config_override=config_override,
    )
    if os.path.exists(latest_path):
        with open(latest_path, "r", encoding="utf-8") as f_rev:
            revised_content = f_rev.read()
        with open(output_path, "w", encoding="utf-8") as f_out:
            f_out.write(revised_content)


if __name__ == "__main__":
    run_narrator()
