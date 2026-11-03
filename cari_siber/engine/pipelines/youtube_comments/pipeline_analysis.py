from cari_siber.engine.core.exceptions import PipelineError
"""
==============================================================================
LANGKAH 4: ENGAGEMENT ANALYSIS KOMENTAR YOUTUBE
==============================================================================
Menghitung tingkat keterlibatan (engagement) tiap topik berdasarkan:
  - reply_count (diskusi berantai)
  - like_count (resonansi persetujuan penonton)
  - is_hearted (apresiasi langsung dari kreator)
  - is_official (partisipasi balasan akun pemilik channel vs penonton umum)
==============================================================================
"""

import os
import sys
import pandas as pd

from cari_siber.engine.core.config import AppConfig


def run_engagement_analysis(config_override=None):
    print("=== LANGKAH 4: ANALISIS ENGAGEMENT TOPIK YOUTUBE ===")

    cfg = config_override or {}
    output_dir = cfg.get("OUTPUT_DIR", AppConfig.OUTPUT_YOUTUBE_DIR)
    csv_output_dir = os.path.join(output_dir, "csv")

    final_mapping_path = os.path.join(csv_output_dir, "mapping_review_topic_youtube_final.csv")

    if not os.path.exists(final_mapping_path):
        raise PipelineError("Berkas '{final_mapping_path}' tidak ditemukan. Harap jalankan Langkah 3.")

    print(f"[INFO] Membaca Golden Dataset: {final_mapping_path}")
    df = pd.read_csv(final_mapping_path)

    df["reply_count"] = pd.to_numeric(df.get("reply_count", 0), errors="coerce").fillna(0)
    df["like_count"] = pd.to_numeric(df.get("like_count", 0), errors="coerce").fillna(0)

    analysis_data = []

    df["business_category"] = df.get("business_category", pd.Series(dtype=object)).fillna("Lainnya")
    df["sub_issue"] = df.get("sub_issue", pd.Series(dtype=object)).fillna("Umum")
    df["ai_sentiment"] = df.get("ai_sentiment", pd.Series(dtype=object)).fillna("Netral")
    grouped = df.groupby(["topic_id", "business_category", "sub_issue", "ai_sentiment"], dropna=False)

    for (t_id, category, sub_issue, sentiment), group in grouped:
        total_comments = len(group)
        sum_reply_count = int(group["reply_count"].sum())
        total_likes = int(group["like_count"].sum())

        # Hitung komentar dari pemilik channel resmi (is_official == True)
        if "is_official" in group.columns:
            official_mask = group["is_official"].astype(str).str.lower().isin(["true", "1"])
            official_count = int(official_mask.sum())
        else:
            official_count = 0

        # Hitung komentar yang diberi Heart oleh kreator
        if "is_hearted" in group.columns:
            hearted_mask = group["is_hearted"].astype(str).str.lower().isin(["true", "1"])
            hearted_count = int(hearted_mask.sum())
        else:
            hearted_count = 0

        user_count = total_comments - official_count
        engagement_score = round(sum_reply_count / total_comments, 2) if total_comments > 0 else 0.0

        analysis_data.append(
            {
                "topic_id": t_id,
                "business_category": category,
                "sub_issue": sub_issue,
                "ai_sentiment": sentiment,
                "total_comments": total_comments,
                "sum_reply_count": sum_reply_count,
                "total_likes": total_likes,
                "hearted_comments": hearted_count,
                "official_comments": official_count,
                "user_comments": user_count,
                "engagement_score": engagement_score,
            }
        )

    df_analysis = pd.DataFrame(analysis_data)

    if not df_analysis.empty:
        df_analysis = df_analysis.sort_values(by="engagement_score", ascending=False)

    output_path = os.path.join(csv_output_dir, "youtube_engagement_metrics.csv")
    df_analysis.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[SUCCESS] Analisis engagement YouTube selesai! Tersimpan di: {output_path}")
    if not df_analysis.empty:
        print("\n[Preview Top 3 Topik dengan Engagement Tertinggi]:")
        print(
            df_analysis[["business_category", "sum_reply_count", "total_likes", "engagement_score"]]
            .head(3)
            .to_string(index=False)
        )


if __name__ == "__main__":
    run_engagement_analysis()
