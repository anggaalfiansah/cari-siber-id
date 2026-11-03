"""
==============================================================================
CORE NLP & BERTOPIC MODELING (UNIVERSAL + AGENTIC HARDENED)
==============================================================================
File ini berisi fungsi inti NLP dan pemodelan topik menggunakan BERTopic.
Fungsi-fungsi di sini didesain universal dan menerima input data mentah
berupa tipe data Python dasar (seperti list of strings), terlepas dari
format file CSV atau schema kolom DataFrame tertentu.

Terintegrasi dengan Agentic Gates:
  - Quality Gate: Statistik + LLM Sample Audit pada tahap Cleaning / Preprocessing
  - Topic Gate  : Evaluasi Kohesi & Duplikasi Topik + Auto-Tune & Re-cluster
==============================================================================
"""

import os
import re
import copy
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import CountVectorizer
try:
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
except ImportError:
    BERTopic = None
    HDBSCAN = None

from cari_siber.paths import get_resources_dir, get_user_data_dir

def _resolve_resource_file(filename: str) -> str:
    p = os.path.join(get_resources_dir(), filename)
    if os.path.exists(p):
        return p
    for sub in ['resources', 'data', 'config']:
        p2 = os.path.join(sub, filename)
        if os.path.exists(p2):
            return p2
    return p

from cari_siber.engine.core.agentic_gates import (
    run_quality_gate,
    audit_and_heal_topic_clustering,
    normalisasi_teks_hardened,
)

# ==============================================================================
# KAMUS NORMALISASI SLANG INDONESIA (DEFAULT IMMUTABLE)
# ==============================================================================
DEFAULT_KAMUS_SLANG = {
    "bgt": "banget", "bgtt": "banget", "bngt": "banget", "bangettttt": "banget",
    "jg": "juga", "jga": "juga", 
    "jgn": "jangan",
    "dpt": "dapat", "dapet": "dapat",
    "dr": "dari", "dri": "dari",
    "apk": "aplikasi", "aplkasi": "aplikasi", "app": "aplikasi", "apknya": "aplikasinya",
    "lemot": "lambat", "lola": "lambat",
    "pas": "saat", 
    "klo": "kalau", "kalo": "kalau", "kl": "kalau",
    "yg": "yang", 
    "tp": "tapi", "tpi": "tapi",
    "ga": "tidak", "gak": "tidak", "gk": "tidak", "ngga": "tidak", "nggak": "tidak", "engga": "tidak", "gx": "tidak", "g": "tidak",
    "sdh": "sudah", "udah": "sudah", "udh": "sudah",
    "bca": "baca", "mbaca": "membaca",
    "byr": "bayar",
    "blm": "belum", "belom": "belum",
    "pdhal": "padahal", "pdhl": "padahal",
    "gmn": "bagaimana", "gimana": "bagaimana", "gmana": "bagaimana",
    "knp": "kenapa", "knpa": "kenapa",
    "krn": "karena", "karna": "karena", "krna": "karena",
    "trus": "terus", "trs": "terus",
    "bkin": "buat", "bikin": "buat",
    "sm": "sama",
    "pake": "pakai", "pke": "pakai",
    "sy": "saya", "sya": "saya", "gw": "saya", "gue": "saya",
    "kyk": "seperti", "kya": "seperti", "kaya": "seperti",
    "skrg": "sekarang", "skrng": "sekarang",
    "bnyk": "banyak", "bnyak": "banyak",
    "bgus": "bagus", "bgs": "bagus", "bagusss": "bagus", "bagussss": "bagus", "bgusss": "bagus",
    "jelek": "buruk", "jlk": "buruk",
    "ny": "nya", "nyaa": "nya",
    "cb": "coba", "cba": "coba",
    "dl": "dulu", "dlu": "dulu",
    "gt": "begitu", "gitu": "begitu", "gtu": "begitu",
    "tau": "tahu", "tw": "tahu",
    "bs": "bisa", "bisaa": "bisa"
}

# Alias untuk kompatibilitas mundur
kamus_slang = dict(DEFAULT_KAMUS_SLANG)

DEFAULT_BERTOPIC_CONFIG = {
    "embedding_model": "indobenchmark/indobert-base-p1",
    "hdbscan": {
        "min_cluster_size": 10,
        "metric": "euclidean",
        "cluster_selection_method": "leaf",
        "prediction_data": True
    },
    "bertopic": {
        "language": "multilingual",
        "calculate_probabilities": False,
        "reduce_outliers_strategy": "c-tf-idf",
        "similarity_threshold": 0.80,
        "min_topic_size": 10,
        "nr_topics": {
            "negatif": 30,
            "netral": 30,
            "positif": 30
        }
    }
}


def load_kamus_slang():
    """
    Memuat kamus alay dari:
    1. DEFAULT_KAMUS_SLANG (bawaan sistem)
    2. 'data/kamus-alay-nasalsabila.csv' (Kredit dasar: Nasalsabila - Colloquial Indonesian Lexicon)
    3. 'data/kamus-alay-learned.csv' (Hasil incremental learning CaRI Sentimen ID)
    """
    fresh_kamus = dict(DEFAULT_KAMUS_SLANG)

    # 1. Base dictionary (Kredit: Nasalsabila)
    csv_kamus_path = _resolve_resource_file('kamus-alay-nasalsabila.csv')
    if os.path.exists(csv_kamus_path):
        print(f"[INFO] Memuat kamus alay dasar dari '{csv_kamus_path}' (Kredit: Nasalsabila)...")
        try:
            df_kamus = pd.read_csv(csv_kamus_path, usecols=['slang', 'formal'])
            df_kamus = df_kamus.dropna(subset=['slang', 'formal'])
            kamus_csv = dict(zip(df_kamus['slang'].astype(str).str.strip().str.lower(), 
                                 df_kamus['formal'].astype(str).str.strip().str.lower()))
            fresh_kamus = {**kamus_csv, **fresh_kamus}
            print(f"[INFO] Berhasil memuat {len(kamus_csv):,} entri kamus dasar Nasalsabila.")
        except Exception as e:
            print(f"[WARNING] Gagal memuat kamus dasar CSV: {e}")

    # 2. Learned dictionary (Incremental Learning)
    learned_kamus_path = _resolve_resource_file('kamus-alay-learned.csv')
    if os.path.exists(learned_kamus_path):
        try:
            df_learned = pd.read_csv(learned_kamus_path, usecols=['slang', 'formal'])
            df_learned = df_learned.dropna(subset=['slang', 'formal'])
            kamus_learned = dict(zip(df_learned['slang'].astype(str).str.strip().str.lower(),
                                     df_learned['formal'].astype(str).str.strip().str.lower()))
            fresh_kamus = {**fresh_kamus, **kamus_learned}
            print(f"[INFO] 🧠 Berhasil memuat {len(kamus_learned):,} entri kamus baru hasil pembelajaran (learned).")
        except Exception as e:
            print(f"[WARNING] Gagal memuat kamus learned CSV: {e}")

    print(f"[INFO] Total entri kata slang aktif: {len(fresh_kamus):,} kata.")
    return fresh_kamus


# ==============================================================================
# BERTopic Configuration
# ==============================================================================
def get_bertopic_config():
    """
    Memuat konfigurasi BERTopic dari 'config/bertopic_config.json' sebagai
    salinan baru (deep copy) agar setiap pengujian selalu mulai dari default.
    """
    config_path = _resolve_resource_file('bertopic_config.json')
    if os.path.exists(config_path):
        print(f"[INFO] Memuat konfigurasi default dari '{config_path}'...")
        with open(config_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        return copy.deepcopy(loaded)
    else:
        print(f"[WARNING] File konfigurasi '{config_path}' tidak ditemukan. Menggunakan default...")
        return copy.deepcopy(DEFAULT_BERTOPIC_CONFIG)


# ==============================================================================
# Stopwords Initialization
# ==============================================================================
def get_stopwords(title_name):
    indo_stopwords = [
        "yang", "di", "dan", "untuk", "dengan", "saya", "ini", "itu", "ke", "dari", 
        "pada", "atau", "juga", "sudah", "telah", "oleh", "aplikasi", "aplikasinya", 
        "apk", "apknya", "app", "adalah", "ya", "saja", "aja", "lah", "deh",
        "sih", "kok", "dong", "karena", "sebab", "sehingga",
        "maka", "jika", "kalau", "bila", "apabila", "pun", "aku", "kamu", "dia", 
        "mereka", "kita", "kami", "kalian", "anda", "nya", "ku", "mu", "ada",
        "bagaimana", "banyak", "bintang", "rate", "rating"
    ]

    default_stopwords_path = _resolve_resource_file('id.stopwords.02.01.2016.txt')
    if os.path.exists(default_stopwords_path):
        print(f"[INFO] Memuat default stopwords dari '{default_stopwords_path}'...")
        try:
            with open(default_stopwords_path, 'r', encoding='utf-8') as f:
                default_stopwords = [line.strip().lower() for line in f if line.strip()]
            indo_stopwords.extend(default_stopwords)
            print(f"[INFO] Berhasil memuat {len(default_stopwords)} default stopwords.")
        except Exception as e:
            print(f"[WARNING] Gagal memuat default stopwords: {e}")

    # Memuat & mengakumulasikan custom stopwords tanpa menghapus kata yang sudah ada
    custom_stopwords_path = _resolve_resource_file('stopwords.txt')
    existing_custom = set()
    if os.path.exists(custom_stopwords_path):
        try:
            with open(custom_stopwords_path, 'r', encoding='utf-8') as f:
                for line in f:
                    w = line.strip().lower()
                    if w and len(w) > 1:
                        existing_custom.add(w)
        except Exception:
            pass

    words_in_app = re.findall(r'\b\w+\b', title_name.lower())
    new_app_words = set([w for w in words_in_app if len(w) > 1])
    combined_custom = sorted(list(existing_custom | new_app_words))

    if combined_custom:
        try:
            os.makedirs(os.path.dirname(custom_stopwords_path), exist_ok=True)
            with open(custom_stopwords_path, 'w', encoding='utf-8') as f:
                for sw in combined_custom:
                    f.write(f"{sw}\n")
        except Exception as e:
            print(f"[WARNING] Gagal memperbarui custom stopwords: {e}")
        indo_stopwords.extend(combined_custom)

    indo_stopwords = sorted(list(set(indo_stopwords)))
    print(f"[INFO] Total stopwords aktif: {len(indo_stopwords):,} kata (Custom/Akumulatif: {len(combined_custom):,} kata).")
    return indo_stopwords


# ==============================================================================
# FUNGSI NORMALISASI TEKS
# ==============================================================================
def normalisasi_teks(text, kamus):
    return normalisasi_teks_hardened(text, kamus, collapse_repeats=False)


# ==============================================================================
# FUNGSI MODELING BERTopic (UNIVERSAL + QUALITY GATE + TOPIC GATE)
# ==============================================================================
def train_bertopic(
    docs_raw,
    kamus,
    embedding_model,
    config,
    stopwords,
    min_cluster_size=None,
    domain_name="Aplikasi",
    segment_label="all",
    output_dir=None,
    config_override=None,
):
    """
    Melatih BERTopic secara universal dengan input list of text murni,
    dilengkapi dengan Quality Gate (Cleaning + LLM Sample Audit) dan
    Topic Gate (Evaluasi Kohesi & Duplikasi + Auto-Tune HDBSCAN).
    Selalu bekerja di atas salinan (copy) parameter agar konfigurasi default
    tetap murni untuk setiap run/segmen.

    Returns:
        tuple: (topic_model, topics, probs, embeddings, docs_clean)
    """
    working_kamus = dict(kamus)
    working_stopwords = list(stopwords)
    working_config = copy.deepcopy(config)

    # 1. Jalankan Cleaning / Preprocessing + Quality Gate (pass / retry dengan parameter baru)
    print("Normalisasi kata slang & evaluasi Quality Gate...")
    docs_clean, working_kamus, updated_stopwords, _ = run_quality_gate(
        docs_raw=docs_raw,
        kamus=working_kamus,
        stopwords=working_stopwords,
        domain_name=domain_name,
        output_dir=output_dir,
        segment_label=segment_label,
        config_override=config_override,
    )

    # 2. Ubah teks menjadi angka (IndoBERT Embeddings) — disimpan di memori untuk efisiensi re-cluster
    print("Mengubah teks menjadi angka (Embeddings IndoBERT)...")
    embeddings = embedding_model.encode(docs_clean, show_progress_bar=True, batch_size=32)
    embeddings = normalize(embeddings)

    vectorizer_model = CountVectorizer(ngram_range=(1, 2), stop_words=updated_stopwords)

    initial_min_size = (
        min_cluster_size
        if min_cluster_size is not None
        else working_config["hdbscan"].get("min_cluster_size", 10)
    )

    # 3. Jalankan BERTopic + Topic Gate (pass / tune parameter HDBSCAN & cluster ulang / merge duplikat)
    topic_model, topics, probs, _ = audit_and_heal_topic_clustering(
        docs_clean=docs_clean,
        embeddings=embeddings,
        vectorizer_model=vectorizer_model,
        config=working_config,
        initial_min_size=initial_min_size,
        domain_name=domain_name,
        segment_label=segment_label,
        output_dir=output_dir,
        config_override=config_override,
        docs_raw=docs_raw,
    )

    return topic_model, topic_model.topics_, probs, embeddings, docs_clean
