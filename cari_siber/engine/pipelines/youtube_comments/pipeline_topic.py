from cari_siber.engine.core.exceptions import PipelineError
"""
==============================================================================
LANGKAH 1: TOPIC MODELING PIPELINE YOUTUBE (BERTopic + IndoBERT)
==============================================================================
Memodelkan klaster topik dari dataset komentar video YouTube secara kolektif.
Menghasilkan file CSV raw, reduced, dan master_topic_youtube_agregasi.csv.
==============================================================================
"""

import ast
import os
import sys
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from cari_siber.engine.core.config import AppConfig, extract_youtube_video_id
from cari_siber.engine.core.topic_modeling import (
    load_kamus_slang,
    get_bertopic_config,
    get_stopwords,
    train_bertopic,
)


def process_youtube_bertopic(df, kamus, embedding_model, config, stopwords, csv_output_dir, output_dir=None, config_override=None):
    print(f"\n{'='*65}")
    print("Mulai memproses Topic Modeling Komentar YouTube (Keseluruhan Data)")
    print(f"{'='*65}")

    df = df.dropna(subset=["comment_text"]).copy()
    df = df[df["comment_text"].astype(str).str.strip() != ""].copy()
    docs_raw = df["comment_text"].astype(str).tolist()

    if len(docs_raw) < 15:
        print(f"[YOUTUBE] Data terlalu sedikit ({len(docs_raw)} komentar). Minimal membutuhkan 15 komentar untuk klasterisasi.")
        return

    min_cluster = 5 if len(docs_raw) < 150 else 10
    topic_model, topics, probs, embeddings, docs_clean = train_bertopic(
        docs_raw=docs_raw,
        kamus=kamus,
        embedding_model=embedding_model,
        config=config,
        stopwords=stopwords,
        min_cluster_size=min_cluster,
        domain_name=AppConfig.YOUTUBE_APP_NAME,
        segment_label="youtube_all",
        output_dir=output_dir or AppConfig.OUTPUT_YOUTUBE_DIR,
        config_override=config_override,
    )

    def generate_manual_label(name_str):
        parts = str(name_str).split("_")
        if len(parts) > 1:
            words = parts[1:4]
            return " ".join(words).title()
        return name_str

    def save_results(model, current_probs, suffix):
        df_topics = model.get_topic_info().copy()
        df_topics["label_manual"] = df_topics["Name"].apply(generate_manual_label)

        new_topics = model.topics_
        df_sub = df.copy()
        if len(df_sub) != len(new_topics):
            df_sub = df_sub.iloc[: len(new_topics)].copy()

        df_sub["topic_id"] = new_topics
        topic_mapping = dict(zip(df_topics["Topic"], df_topics["label_manual"]))
        df_sub["topic_name"] = df_sub["topic_id"].map(topic_mapping)

        print(f"\n=== EVALUASI TOPIK YOUTUBE ({suffix.upper()}) ===")
        top_topics = df_topics[df_topics["Topic"] != -1].head(3)
        for _, row in top_topics.iterrows():
            t_id = row["Topic"]
            t_name = row["label_manual"]
            t_count = row["Count"]
            print(f"> Topik ID: {t_id} | Label: '{t_name}' | Jumlah Komentar: {t_count}")
            try:
                sample_docs = model.get_representative_docs(int(t_id))
                if isinstance(sample_docs, (list, tuple, np.ndarray)):
                    for i, doc in enumerate(list(sample_docs)[:3]):
                        print(f"    {i+1}. {doc[:100]}...")
            except Exception:
                pass

        centroids = {}
        unique_topics = set(new_topics)
        for t in unique_topics:
            if t == -1:
                continue
            idx_in_sub = np.where(np.array(new_topics) == t)[0]
            if len(idx_in_sub) > 0:
                mean_emb = embeddings[idx_in_sub].mean(axis=0)
                norm = np.linalg.norm(mean_emb)
                centroids[t] = mean_emb / norm if norm > 0 else mean_emb

        # Hitung probabilitas & topik alternatif secara vektorisasi (NumPy BLAS)
        if centroids:
            centroid_ids = np.array(list(centroids.keys()))
            centroid_matrix = np.array(list(centroids.values()))
            sim_matrix = np.dot(embeddings[:len(df_sub)], centroid_matrix.T)
            topic_to_col = {tid: idx for idx, tid in enumerate(centroid_ids)}

            main_probs, alt1_id, alt1_prob, alt2_id, alt2_prob = [], [], [], [], []
            for i in range(len(df_sub)):
                local_main = new_topics[i]
                sims = sim_matrix[i]

                if local_main != -1 and local_main in topic_to_col:
                    main_probs.append(float(sims[topic_to_col[local_main]]))
                    top_indices = np.argsort(-sims)
                    alts = [centroid_ids[idx] for idx in top_indices if centroid_ids[idx] != local_main]
                    alt_probs = [float(sims[idx]) for idx in top_indices if centroid_ids[idx] != local_main]
                else:
                    main_probs.append(0.0)
                    top_indices = np.argsort(-sims)
                    alts = [centroid_ids[idx] for idx in top_indices]
                    alt_probs = [float(sims[idx]) for idx in top_indices]

                alt1_id.append(int(alts[0]) if len(alts) >= 1 else None)
                alt1_prob.append(alt_probs[0] if len(alt_probs) >= 1 else None)
                alt2_id.append(int(alts[1]) if len(alts) >= 2 else None)
                alt2_prob.append(alt_probs[1] if len(alt_probs) >= 2 else None)
        else:
            n_rows = len(df_sub)
            main_probs = [0.0] * n_rows
            alt1_id = [None] * n_rows
            alt1_prob = [None] * n_rows
            alt2_id = [None] * n_rows
            alt2_prob = [None] * n_rows

        df_sub["main_topic_prob"] = main_probs
        df_sub["alt_topic_1"] = alt1_id
        df_sub["alt_topic_1_name"] = df_sub["alt_topic_1"].map(topic_mapping)
        df_sub["alt_topic_1_prob"] = alt1_prob
        df_sub["alt_topic_2"] = alt2_id
        df_sub["alt_topic_2_name"] = df_sub["alt_topic_2"].map(topic_mapping)
        df_sub["alt_topic_2_prob"] = alt2_prob

        df_topics["Representation"] = df_topics["Representation"].astype(str)
        df_topics["Representative_Docs"] = df_topics["Representative_Docs"].astype(str)

        # Pertahankan seluruh kolom metadata video dan penulis untuk analisis downstream
        df_mapping = df_sub.copy()

        master_csv_path = os.path.join(csv_output_dir, f"master_topic_youtube_{suffix}.csv")
        mapping_csv_path = os.path.join(csv_output_dir, f"mapping_review_topic_youtube_{suffix}.csv")

        df_topics.to_csv(master_csv_path, index=False)
        df_mapping.to_csv(mapping_csv_path, index=False, encoding="utf-8-sig")
        print(f"[YOUTUBE] CSV ({suffix}) berhasil disimpan ke '{master_csv_path}' dan '{mapping_csv_path}'\n")

        if suffix == "reduced":
            agg_data = []
            total_sub_reviews = len(df_sub)
            grouped = df_sub.groupby("topic_id")
            for t_id, group in grouped:
                topic_info = df_topics[df_topics["Topic"] == t_id]
                if not topic_info.empty:
                    topic_name = topic_info.iloc[0]["label_manual"]
                    representation = topic_info.iloc[0]["Representation"]
                    if isinstance(representation, str):
                        try:
                            words = ast.literal_eval(representation)
                            keywords = ", ".join(words)
                        except Exception:
                            keywords = representation
                    else:
                        keywords = str(representation)
                else:
                    topic_name = "Outliers" if t_id == -1 else f"Topic {t_id}"
                    keywords = ""

                review_count = len(group)
                pct = (review_count / total_sub_reviews) * 100 if total_sub_reviews > 0 else 0.0

                total_likes = pd.to_numeric(group["like_count"], errors="coerce").fillna(0).sum()
                total_replies = pd.to_numeric(group["reply_count"], errors="coerce").fillna(0).sum()

                if "main_topic_prob" in group.columns:
                    samples = group.sort_values(by="main_topic_prob", ascending=False)["comment_text"].head(10).tolist()
                else:
                    samples = group["comment_text"].head(10).tolist()
                samples_str = " | ".join([str(s).replace("\n", " ").strip() for s in samples])

                agg_data.append(
                    {
                        "topic_id": t_id,
                        "topic_name": topic_name,
                        "ai_sentiment": "",
                        "business_category": "",
                        "sub_issue": "",
                        "comment_count": review_count,
                        "percentage": round(pct, 2),
                        "total_likes": int(total_likes),
                        "total_replies": int(total_replies),
                        "top_keywords": keywords,
                        "sample_comments": samples_str,
                    }
                )

            df_agg = pd.DataFrame(agg_data)
            if not df_agg.empty:
                df_agg = df_agg.sort_values(by="comment_count", ascending=False)

            agg_csv_path = os.path.join(csv_output_dir, "master_topic_youtube_agregasi.csv")
            df_agg.to_csv(agg_csv_path, index=False, encoding="utf-8-sig")
            print(f"[YOUTUBE] CSV Agregasi berhasil disimpan ke '{agg_csv_path}'\n")

    save_results(topic_model, probs, "raw")

    nr_topics = config["bertopic"].get("nr_topics", {}).get("netral", 25)
    target_nr_topics = max(10, min(30, nr_topics))

    unique_topics = set(topic_model.topics_)
    if -1 in unique_topics:
        unique_topics.remove(-1)

    if len(unique_topics) > target_nr_topics:
        print(f"[YOUTUBE] Mengurangi jumlah topik dari {len(unique_topics)} menjadi {target_nr_topics}...")
        try:
            topic_model.reduce_topics(docs_clean, nr_topics=target_nr_topics)
            probs = topic_model.probabilities_
        except Exception as e:
            print(f"[YOUTUBE] Gagal mengurangi jumlah topik: {e}")

    save_results(topic_model, probs, "reduced")


_CACHED_EMBEDDING_MODEL = None
_CACHED_MODEL_PATH = None


def get_cached_embedding_model(model_name_or_path: str):
    """Mengambil atau memuat model SentenceTransformer di memori agar run berikutnya instan."""
    global _CACHED_EMBEDDING_MODEL, _CACHED_MODEL_PATH
    if _CACHED_EMBEDDING_MODEL is not None and _CACHED_MODEL_PATH == model_name_or_path:
        return _CACHED_EMBEDDING_MODEL
    print(f"[INFO] Memuat Model Embedding: {model_name_or_path}...")
    _CACHED_EMBEDDING_MODEL = SentenceTransformer(model_name_or_path)
    _CACHED_MODEL_PATH = model_name_or_path
    return _CACHED_EMBEDDING_MODEL


def run_topic_modeling(config_override=None):
    """Orkestrator utama Langkah 1 untuk Topic Modeling komentar YouTube."""
    print("=== LANGKAH 1: NLP TOPIC MODELING YOUTUBE DENGAN BERTOPIC ===")

    cfg = config_override or {}
    raw_url = cfg.get("YOUTUBE_VIDEO_URL", AppConfig.YOUTUBE_VIDEO_URL)
    video_id = extract_youtube_video_id(raw_url) or AppConfig.YOUTUBE_VIDEO_ID
    output_dir = cfg.get("OUTPUT_DIR", AppConfig.OUTPUT_YOUTUBE_DIR)

    youtube_csv_path = os.path.join(output_dir, "scrap", f"youtube_comments_video_{video_id}.csv")
    csv_output_dir = os.path.join(output_dir, "csv")
    os.makedirs(csv_output_dir, exist_ok=True)

    if not os.path.exists(youtube_csv_path):
        raise PipelineError("Berkas komentar YouTube '{youtube_csv_path}' tidak ditemukan. Harap jalankan Langkah 0 terlebih dahulu.")

    print(f"[INFO] Membaca file CSV dari {youtube_csv_path}...")
    df = pd.read_csv(youtube_csv_path)

    kamus = load_kamus_slang()
    config = get_bertopic_config()
    stopwords = get_stopwords(f"youtube video channel {AppConfig.YOUTUBE_APP_NAME}")

    print("[INFO] Menyiapkan Model Embedding...")
    from cari_siber.paths import get_models_dir
    model_name_or_path = config["embedding_model"]
    local_model = os.path.join(get_models_dir(), "indobert-base-p1")
    if os.path.isdir(local_model):
        print(f"[INFO] Menggunakan model IndoBERT lokal offline dari: {local_model}")
        model_name_or_path = local_model
    embedding_model = get_cached_embedding_model(model_name_or_path)

    process_youtube_bertopic(df, kamus, embedding_model, config, stopwords, csv_output_dir, output_dir=output_dir, config_override=config_override)

    print(f"\n[SUCCESS] Semua proses BERTopic YouTube selesai! Hasil tersimpan di: {csv_output_dir}/")


if __name__ == "__main__":
    run_topic_modeling()
