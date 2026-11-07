from cari_siber.engine.core.exceptions import PipelineError
"""
==============================================================================
LANGKAH 7 (OPSIONAL): LAPORAN PERKIRAAN INTELIJEN SIBER (KIRKA SIBER SOSIAL)
==============================================================================
Menghasilkan Laporan Perkiraan Intelijen Siber (Kirka Siber Sosial) (`narrative_insights.md`)
berdasarkan data telemetri dan statistik `youtube_eda_summary.json` serta
data forensik CIB, Jaringan Bot Massal, Polarisasi, dan DISARM Framework.
==============================================================================
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime
import pandas as pd

from cari_siber.engine.core.ai_client import generate_text
from cari_siber.engine.core.agentic_gates import run_report_gate
from cari_siber.engine.core.config import AppConfig


def _load_or_compute_forensic_cib_context(output_dir: str) -> dict:
    """
    Memuat (atau menghitung langsung dari mapping_review_topic_youtube_final.csv jika belum ada)
    metrik CIB, Indeks Polarisasi, Jaringan Bot Massal (copypasta), Akun Terindikasi (Flagged),
    serta rekap matriks taktik DISARM Framework agar Laporan KIRKA memiliki fakta forensik utuh.
    """
    if not output_dir or not os.path.exists(output_dir):
        return {}

    json_dir = os.path.join(output_dir, "json")
    os.makedirs(json_dir, exist_ok=True)

    cib_path = os.path.join(json_dir, "cib_detection_summary.json")
    pol_path = os.path.join(json_dir, "polarization_metrics.json")
    botnet_path = os.path.join(json_dir, "coordinated_bot_networks.json")
    flagged_path = os.path.join(json_dir, "flagged_accounts.json")

    cib_dict = {}
    pol_dict = {}
    botnets = []
    flagged = []

    if os.path.exists(cib_path):
        try:
            with open(cib_path, "r", encoding="utf-8") as f:
                cib_dict = json.load(f)
        except Exception:
            pass

    if os.path.exists(pol_path):
        try:
            with open(pol_path, "r", encoding="utf-8") as f:
                pol_dict = json.load(f)
        except Exception:
            pass

    if os.path.exists(botnet_path):
        try:
            with open(botnet_path, "r", encoding="utf-8") as f:
                botnets = json.load(f)
        except Exception:
            pass

    if os.path.exists(flagged_path):
        try:
            with open(flagged_path, "r", encoding="utf-8") as f:
                flagged = json.load(f)
        except Exception:
            pass

    # Jika salah satu belum terkomputasi, hitung dari CSV final dan simpan ke json_dir
    if not cib_dict or not pol_dict or not flagged:
        final_csv = os.path.join(output_dir, "csv", "mapping_review_topic_youtube_final.csv")
        if not os.path.exists(final_csv):
            final_csv = os.path.join(output_dir, "csv", "mapping_review_topic_youtube_raw.csv")
        if os.path.exists(final_csv):
            try:
                from cari_siber.services.intelligence import IntelligenceService
                df_final = pd.read_csv(final_csv)
                if not df_final.empty:
                    if not cib_dict:
                        c_calc = IntelligenceService.calculate_cib_metrics(df_final)
                        cib_dict = {
                            "cib_threat_score": float(c_calc.cib_threat_score),
                            "cib_threat_level": c_calc.cib_threat_level.value,
                            "total_comments_analyzed": c_calc.total_comments_analyzed,
                            "unique_authors": c_calc.unique_authors,
                            "author_duplication_rate": c_calc.author_duplication_rate,
                            "rapid_burst_ratio": c_calc.rapid_burst_ratio,
                            "high_risk_bot_count": c_calc.high_risk_bot_count,
                        }
                        with open(cib_path, "w", encoding="utf-8") as f:
                            json.dump(cib_dict, f, indent=2, ensure_ascii=False)
                    if not pol_dict:
                        p_calc = IntelligenceService.calculate_polarization_metrics(df_final)
                        pol_dict = {
                            "polarization_index": float(p_calc.polarization_index),
                            "sentiment_distribution": p_calc.sentiment_distribution,
                            "dominant_conflict_topics": p_calc.dominant_conflict_topics,
                            "silent_majority_consensus": p_calc.silent_majority_consensus,
                        }
                        with open(pol_path, "w", encoding="utf-8") as f:
                            json.dump(pol_dict, f, indent=2, ensure_ascii=False)
                    if not botnets:
                        botnets = IntelligenceService.calculate_coordinated_bot_networks(df_final)
                        with open(botnet_path, "w", encoding="utf-8") as f:
                            json.dump(botnets, f, indent=2, ensure_ascii=False)
                    if not flagged:
                        flagged = IntelligenceService.calculate_flagged_accounts(df_final)
                        with open(flagged_path, "w", encoding="utf-8") as f:
                            json.dump(flagged, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[INFO] Peringatan saat memuat telemetri CIB untuk narasi: {e}")

    # Ringkas DISARM Framework Matrix (identik dengan header UI)
    disarm_counter = Counter()
    for acc in flagged or []:
        codes = acc.get("disarm_codes") or acc.get("disarm_framework") or []
        for c in codes:
            disarm_counter[str(c)] += 1

    slim_botnets = []
    for bn in (botnets or [])[:6]:
        slim_botnets.append({
            "template_text": str(bn.get("template_text", ""))[:140],
            "unique_accounts_count": bn.get("unique_accounts_count", 0),
            "total_occurrences": bn.get("total_occurrences", 0),
            "coordination_level": bn.get("coordination_level", ""),
            "sample_accounts": (bn.get("accounts") or [])[:5],
        })

    slim_flagged = []
    for fa in (flagged or [])[:10]:
        slim_flagged.append({
            "username": fa.get("username", ""),
            "actor_label": fa.get("actor_label", ""),
            "cib_risk_level": fa.get("cib_risk_level", ""),
            "bot_score": fa.get("bot_score", 0),
            "provocation_score": fa.get("provocation_score", 0),
            "total_comments": fa.get("total_comments", 0),
            "videos_count": fa.get("videos_count", 1),
            "disarm_codes": fa.get("disarm_codes", []),
            "sample_comment": (fa.get("sample_comments") or [""])[0][:120] if fa.get("sample_comments") else "",
        })

    return {
        "cib_intelligence": cib_dict,
        "polarization_intelligence": pol_dict,
        "disarm_framework_detected": dict(disarm_counter.most_common(10)),
        "total_flagged_accounts": len(flagged or []),
        "coordinated_bot_networks_count": len(botnets or []),
        "top_coordinated_bot_clusters": slim_botnets,
        "top_flagged_threat_accounts": slim_flagged,
    }


def _slim_json(data: dict, output_dir: str = None) -> dict:
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

    if output_dir:
        forensic_ctx = _load_or_compute_forensic_cib_context(output_dir)
        if forensic_ctx:
            slimmed.update(forensic_ctx)

    return slimmed


def build_prompt(json_data: str, target_name: str) -> str:
    return f"""Anda adalah Analis Utama Intelijen Kognitif & Pertahanan Ruang Siber.
Tugas Anda adalah menyusun "Laporan Perkiraan Intelijen Siber (Kirka Siber Sosial)" mengenai dinamika opini dan potensi ancaman operasi informasi pada target: "{target_name}".

Berikut adalah data telemetri statistik dan forensik CIB hasil ekstraksi intelijen:
{json_data}

Susun Laporan Eksekutif dalam BAHASA INDONESIA yang RINGKAS, PADAT, dan TAKTIS (sekitar 800–1.400 kata) dengan struktur heading Markdown berikut:
## 1. SITUASI RUANG SIBER & INDEKS POLARISASI
(Overview ancaman, distribusi sentimen publik, Indeks Polarisasi dari `polarization_intelligence`, dan analisis Silent Majority vs Loud Minority)

## 2. IDENTIFIKASI OPERASI INFORMASI TERKOORDINASI / CIB
(Analisis skor ancaman CIB dari `cib_intelligence`, rasio duplikasi penulis, rasio burst, temuan klaster copypasta dari `top_coordinated_bot_clusters`, serta daftar akun terindikasi Bot/Buzzer & Provokator dari `top_flagged_threat_accounts`)

## 3. PEMETAAN NARASI ANCAMAN KOGNITIF & KORELASI ANCAMAN INFRASTRUKTUR IT/OT
(Pemetaan isu berdasar domain Disinformasi, SARA, Delegitimasi Institusi, serta korelasi potensi eskalasi narasi siber sosial terhadap gangguan operasional, doxing personel, atau ancaman siber pada infrastruktur IT/OT)

## 4. DISARM FRAMEWORK MAPPING
(Pemetaan taktik dan teknik ancaman berdasarkan data `disarm_framework_detected` seperti DISARM-T0083, DISARM-T0088, DISARM-T0089, DISARM-T0092 beserta jumlah akun yang terdeteksi)

## 5. REKOMENDASI TINDAKAN PENANGKALAN & KONTRA-NARASI
(Langkah taktis terukur untuk Tim Komunikasi Strategis / Humas, Tim Analis Intelijen Kognitif, dan Tim Pertahanan Siber / CSIRT-SOC — JANGAN mencatut nama instansi spesifik)

ATURAN PENULISAN WAJIB:
- Tulis LANGSUNG isi laporan dalam Bahasa Indonesia formal dan profesional tanpa mencatut nama instansi spesifik.
- DILARANG KERAS menulis proses berpikir/monolog bahasa Inggris (seperti "We need...", "Let's outline...") atau tag `<think>`.
- Gunakan hanya angka faktual yang tercantum di dalam JSON di atas.
- Hindari membuat tabel yang berulang-ulang agar laporan tetap padat dan siap dibacakan dalam briefing eksekutif.
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
            raise PipelineError(f"File youtube_eda_summary.json bukan JSON yang valid: {e}")

    app_name = data.get("meta", {}).get("app_name", AppConfig.YOUTUBE_APP_NAME)
    slimmed_data = _slim_json(data, output_dir=output_dir)
    json_payload = json.dumps(slimmed_data, ensure_ascii=False, indent=2)

    print(f"[INFO] Ukuran data EDA asli: {os.path.getsize(input_path):,} bytes")
    print(f"[INFO] Ukuran data EDA + Forensik CIB disederhanakan: {len(json_payload):,} karakter")

    active_api_key = None
    if ai_provider == "gemini":
        active_api_key = gemini_api_key
        if not active_api_key:
            print("[WARNING] GEMINI_API_KEY tidak diset di konfigurasi. Melewati pembuatan narasi AI.")
            return
    elif ai_provider == "openrouter":
        active_api_key = openrouter_api_key
        if not active_api_key:
            print("[WARNING] OPENROUTER_API_KEY tidak diset di konfigurasi. Melewati pembuatan narasi AI.")
            return
    elif ai_provider == "edgeone":
        active_api_key = edgeone_api_key
        if not active_api_key:
            print("[WARNING] EDGEONE_API_KEY tidak diset di konfigurasi. Melewati pembuatan narasi AI.")
            return
    elif ai_provider == "custom":
        active_api_key = custom_api_key
        if not active_api_key:
            custom_base_url = str(cfg.get("CUSTOM_BASE_URL", AppConfig.CUSTOM_BASE_URL) or "").lower()
            is_local = any(h in custom_base_url for h in ["127.0.0.1", "localhost", "0.0.0.0", "192.168.", "10.", "172."])
            if not is_local:
                print("[WARNING] CUSTOM_API_KEY tidak diset di konfigurasi. Melewati pembuatan narasi AI.")
                return
            active_api_key = "local-airgap"

    prompt = build_prompt(json_payload, app_name)

    print(f"\n[INFO] Menghasilkan Laporan Perkiraan Intelijen Siber (Kirka) menggunakan model: {model_name}...")
    try:
        report_md = generate_text(
            prompt=prompt,
            provider=ai_provider,
            model=model_name,
            api_key=active_api_key,
            min_length=250,
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
