"""
==============================================================================
CORE AI LABELER (UNIVERSAL)
==============================================================================
Berisi skema Pydantic untuk output AI dan fungsi inti pelabelan topik.
Fungsi label_csv_file() menerima path CSV apapun yang berisi kolom
topic_id, topic_name, top_keywords, sample_reviews — tidak terikat pada
skema khusus Play Store atau platform tertentu.
==============================================================================
"""

import os
import time
import pandas as pd
try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        pass
    def Field(*args, **kwargs):
        return None
from cari_siber.engine.core.ai_client import generate_structured_json


# ==============================================================================
# Pydantic Output Schemas (For Gemini/AI Structured Output)
# ==============================================================================
class TopicClassification(BaseModel):
    topic_id: int = Field(description="ID topik yang sedang diklasifikasikan.")
    business_category: str = Field(
        description="Kategori luas dari feedback/masalah. Hasilkan nama kategori yang bersih, profesional, dan WAJIB dalam Bahasa Indonesia (maksimal 4-5 kata) yang konsisten antar topik dan sangat relevan dengan domain aplikasi."
    )
    sub_issue: str = Field(
        description="Deskripsi masalah secara spesifik dan detail WAJIB dalam Bahasa Indonesia (maksimal 10 kata)."
    )
    merge_group: str = Field(
        description="Kode UPPERCASE (snake_case) untuk mengelompokkan masalah sejenis (contoh: 'PERFORMANCE_BUG', 'LOGIN_ERROR')."
    )

class BatchTopicLabels(BaseModel):
    classifications: list[TopicClassification] = Field(
        description="Daftar klasifikasi untuk batch topik yang diberikan."
    )


# ==============================================================================
# FUNGSI INTI LABELING (UNIVERSAL)
# ==============================================================================
def label_csv_file(file_path: str, provider: str, model: str, overwrite: bool,
                   title_name: str, title_desc: str, api_key: str):
    """
    Memproses satu file CSV berisi topik (kolom: topic_id, topic_name,
    top_keywords, sample_reviews) menggunakan AI, lalu menyimpan hasilnya
    kembali ke CSV yang sama.

    Tidak bergantung pada path pipeline, nama sentimen, atau platform data.

    Args:
        file_path:  Path lengkap ke file CSV yang akan dilabeli.
        provider:   Provider AI ('gemini', 'openrouter', 'ollama').
        model:      Nama model AI yang digunakan.
        overwrite:  Jika True, timpa label yang sudah ada.
        title_name: Nama subjek analisis (misal: nama aplikasi atau akun TikTok).
        title_desc: Deskripsi singkat subjek analisis.
        api_key:    API key untuk provider (opsional, fallback ke AppConfig).
    """
    if not os.path.exists(file_path):
        print(f"[WARNING] Berkas '{file_path}' tidak ditemukan. Melewati.")
        return

    print(f"\n[PROCESS] Memproses berkas: {file_path}")
    df = pd.read_csv(file_path)

    for col in ['business_category', 'sub_issue', 'merge_group']:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].astype(str).replace("nan", "").fillna("")

    topics_to_label = []

    for idx, row in df.iterrows():
        try:
            topic_id_val = int(row['topic_id'])
        except (ValueError, TypeError):
            topic_id_val = row['topic_id']
            
        if topic_id_val == -1:
            df.at[idx, 'business_category'] = 'Lain-lain / Noise'
            df.at[idx, 'sub_issue'] = 'Ulasan umum/noise'
            df.at[idx, 'merge_group'] = 'OVERALL_SATISFACTION'
            continue

        is_empty = (
            pd.isna(row['business_category']) or str(row['business_category']).strip() == "" or
            pd.isna(row['sub_issue']) or str(row['sub_issue']).strip() == "" or
            pd.isna(row['merge_group']) or str(row['merge_group']).strip() == ""
        )

        if is_empty or overwrite:
            topics_to_label.append({
                "df_index": idx,
                "topic_id": topic_id_val,
                "topic_name": row['topic_name'],
                "keywords": row['top_keywords'],
                "sample_reviews": row['sample_reviews']
            })

    if not topics_to_label:
        print(f" -> Semua topik di berkas ini sudah memiliki label. Melewati.")
        df.to_csv(file_path, index=False)
        return

    # Pemrosesan Batch (15 topik per batch)
    batch_size = 15
    updated_count = 0
    
    for i in range(0, len(topics_to_label), batch_size):
        batch = topics_to_label[i:i+batch_size]
        print(f" -> Mengirim batch {i//batch_size + 1} ({len(batch)} topik) ke {provider}...")
        
        batch_text = ""
        for t in batch:
            batch_text += (
                f"--- Topic ID: {t['topic_id']} ---\n"
                f"Nama Topik Sementara: {t['topic_name']}\n"
                f"Kata Kunci Dominan: {t['keywords']}\n"
                f"Contoh Ulasan Nyata: {t['sample_reviews']}\n\n"
            )
            
        if provider == "gemini":
            prompt = (
                f"Anda adalah analis intelijen bisnis senior untuk {title_name} ({title_desc}).\n"
                "Tugas Anda adalah mengklasifikasikan beberapa topik ulasan pengguna secara sekaligus (batch) di bawah ini.\n\n"
                f"{batch_text}\n"
                "PENTING: Anda HARUS menghasilkan `business_category` dan `sub_issue` dalam Bahasa Indonesia yang baku, profesional, dan ringkas.\n"
                "Aturan ketat:\n"
                "1. `business_category` HARUS dalam Bahasa Indonesia (maksimal 4-5 kata). Contoh: 'Konektivitas Streaming', 'Pembayaran Berlangganan', 'Masalah Pemutaran Video', bukan 'Streaming Connectivity' atau 'Subscription Payment'.\n"
                "2. `sub_issue` HARUS menjelaskan masalah secara spesifik dalam Bahasa Indonesia (maksimal 10 kata).\n"
                "3. `merge_group` HARUS berupa kode UPPERCASE pendek untuk pengelompokan (contoh: 'STREAM_QUALITY', 'PAYMENT_FAIL').\n\n"
                "Pastikan hasil kembalian menyertakan topic_id yang sesuai untuk masing-masing klasifikasi."
            )
        else:  # ollama / provider lain
            prompt = (
                f"Anda adalah analis ulasan {title_name} ({title_desc}). Klasifikasikan batch topik ulasan berikut:\n\n"
                f"{batch_text}\n"
                "Harap berikan hasil klasifikasi untuk setiap topic_id dalam format JSON valid berikut:\n"
                "{\n"
                '  "classifications": [\n'
                '    {\n'
                '      "topic_id": 123,\n'
                '      "business_category": "kategori bisnis ulasan dalam Bahasa Indonesia secara bebas, ringkas (maksimal 4 kata), konsisten, dan sangat relevan dengan domain (Contoh: \'Pembayaran Langganan\', bukan \'Subscription Payment\')",\n'
                '      "sub_issue": "penjelasan masalah spesifik dalam Bahasa Indonesia (maksimal 10 kata)",\n'
                '      "merge_group": "KODE_UPPERCASE secara bebas untuk pengelompokan yang relevan (contoh: \'LOGIN_ERROR\')"\n'
                '    }\n'
                '  ]\n'
                "}\n\n"
                "PENTING: Seluruh nilai 'business_category' dan 'sub_issue' WAJIB dalam Bahasa Indonesia.\n"
                "Pastikan keluaran HANYA berupa JSON valid, tanpa markdown backticks atau teks penjelasan lainnya."
            )
            
        result = generate_structured_json(prompt, BatchTopicLabels, provider, model, api_key)
            
        if result and "classifications" in result:
            classifications = result["classifications"]
            batch_mapping = {t["topic_id"]: t["df_index"] for t in batch}
            
            for classification in classifications:
                t_id = classification.get("topic_id")
                try:
                    t_id_clean = int(t_id) if t_id is not None else None
                except (ValueError, TypeError):
                    t_id_clean = t_id
                    
                df_idx = batch_mapping.get(t_id_clean)
                
                if df_idx is not None:
                    df.at[df_idx, 'business_category'] = classification.get('business_category', '')
                    df.at[df_idx, 'sub_issue'] = classification.get('sub_issue', '')
                    df.at[df_idx, 'merge_group'] = classification.get('merge_group', '')
                    updated_count += 1
                    print(f"    [OK] Topik {t_id_clean} -> Category: '{classification.get('business_category')}', Group: '{classification.get('merge_group')}'")
                else:
                    print(f"    [WARNING] Menerima label untuk topic_id {t_id} yang tidak ada di batch ini.")
        else:
            print(f"    [FAILED] Gagal mendapatkan klasifikasi untuk batch {i//batch_size + 1}.")
            
        if provider == "gemini":
            time.sleep(4.0)
        else:
            time.sleep(0.5)

    df.to_csv(file_path, index=False)
    print(f"[SUCCESS] Berkas '{file_path}' selesai diproses. Total {updated_count} baris diperbarui.")
