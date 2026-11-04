from cari_siber.engine.core.exceptions import PipelineError
"""
==============================================================================
LANGKAH 5: EXPLORATORY DATA ANALYSIS (EDA) KOMENTAR YOUTUBE
==============================================================================
Menghitung metrik statistik menyeluruh dari komentar video YouTube dan
menyimpannya ke dalam `output/youtube/json/youtube_eda_summary.json`.
==============================================================================
"""

import json
import os
import sys
import numpy as np
import pandas as pd

from cari_siber.engine.core.config import AppConfig, extract_youtube_video_id


def _compute_overview(df_bcs, df_all):
    total = int(df_bcs["comment_count_all"].sum())

    sentiment_dist = {}
    for sent_label in ["Positif", "Negatif", "Netral"]:
        sent_df = df_bcs[df_bcs["ai_sentiment"] == sent_label]
        count = int(sent_df["comment_count_all"].sum())
        pct = round(count / total * 100, 2) if total > 0 else 0.0

        total_likes_sent = int(sent_df["total_likes"].sum()) if "total_likes" in sent_df.columns else 0
        avg_likes = round(total_likes_sent / count, 2) if count > 0 else 0.0

        sentiment_dist[sent_label] = {
            "count": count,
            "pct": pct,
            "avg_like_count": avg_likes,
            "total_likes": total_likes_sent,
        }

    total_confident = int(df_bcs["comment_count_confident"].sum())
    overall_rate = round(total_confident / total, 4) if total > 0 else 0.0

    by_sentiment_conf = {}
    for sent_label in ["Positif", "Negatif", "Netral"]:
        sent_df = df_bcs[df_bcs["ai_sentiment"] == sent_label]
        s_total = int(sent_df["comment_count_all"].sum())
        s_conf = int(sent_df["comment_count_confident"].sum())
        by_sentiment_conf[sent_label] = round(s_conf / s_total, 4) if s_total > 0 else 0.0

    total_hearted = 0
    total_official = 0
    reply_comments = 0
    if not df_all.empty:
        if "is_hearted" in df_all.columns:
            total_hearted = int(df_all["is_hearted"].astype(str).str.lower().isin(["true", "1"]).sum())
        if "is_official" in df_all.columns:
            total_official = int(df_all["is_official"].astype(str).str.lower().isin(["true", "1"]).sum())
        if "is_reply" in df_all.columns:
            reply_comments = int(df_all["is_reply"].astype(str).str.lower().isin(["true", "1"]).sum())

    return {
        "total_comments": total,
        "top_level_comments": max(0, total - reply_comments),
        "reply_comments": reply_comments,
        "total_hearted": total_hearted,
        "total_official_replies": total_official,
        "sentiment_distribution": sentiment_dist,
        "confidence_stats": {
            "overall_confident_rate": overall_rate,
            "by_sentiment": by_sentiment_conf,
        },
    }


def _compute_topic_analysis(df_bcs, df_all):
    result = {}

    for sent_label in ["Positif", "Negatif", "Netral"]:
        df_valid = df_bcs[df_bcs["ai_sentiment"] == sent_label].copy()
        if df_valid.empty:
            continue

        df_valid = df_valid.sort_values("comment_count_all", ascending=False).reset_index(drop=True)
        total_topics = len(df_valid)
        total_comments_sent = int(df_valid["comment_count_all"].sum())

        topics = []
        for idx, row in df_valid.iterrows():
            cat_name = str(row.get("business_category", ""))
            sample_comments = []
            if not df_all.empty and "business_category" in df_all.columns:
                sub_df = df_all[
                    (df_all["ai_sentiment"] == sent_label)
                    & (df_all["business_category"] == cat_name)
                ]
                if not sub_df.empty:
                    sub_df_sorted = sub_df.copy()
                    sub_df_sorted["like_count"] = pd.to_numeric(sub_df_sorted.get("like_count", 0), errors="coerce").fillna(0)
                    sample_comments = (
                        sub_df_sorted.sort_values("like_count", ascending=False)["comment_text"]
                        .dropna()
                        .astype(str)
                        .head(3)
                        .tolist()
                    )

            topics.append(
                {
                    "rank": idx + 1,
                    "name": cat_name,
                    "business_category": cat_name,
                    "sub_issue": str(row.get("example_sub_issues", "")),
                    "example_sub_issues": str(row.get("example_sub_issues", "")),
                    "comment_count": int(row["comment_count_all"]),
                    "total_likes": int(row.get("total_likes", 0)),
                    "total_replies": int(row.get("total_replies", 0)),
                    "share_confident": float(row.get("share_confident", 0.0)),
                    "sample_comments": sample_comments,
                }
            )

        top_3_sum = sum(t["comment_count"] for t in topics[:3])
        top_3_pct = round(top_3_sum / total_comments_sent * 100, 2) if total_comments_sent > 0 else 0.0

        result[sent_label] = {
            "total_categories": total_topics,
            "total_comments": total_comments_sent,
            "categories": topics,
            "concentration": {"top_3_pct": top_3_pct},
        }

    return result


def _compute_video_analysis(meta_csv_path: str, df_all: pd.DataFrame, video_id: str):
    """Menganalisis metadata video YouTube (single maupun multi-video corpus) beserta top comments."""
    df_all_copy = df_all.copy() if not df_all.empty else pd.DataFrame()
    if not df_all_copy.empty:
        df_all_copy["like_count"] = pd.to_numeric(df_all_copy.get("like_count", 0), errors="coerce").fillna(0)
        df_all_copy["reply_count"] = pd.to_numeric(df_all_copy.get("reply_count", 0), errors="coerce").fillna(0)

    total_comment_count = len(df_all_copy)
    total_comment_likes = int(df_all_copy["like_count"].sum()) if not df_all_copy.empty else 0
    sent_counts = df_all_copy["ai_sentiment"].value_counts() if (not df_all_copy.empty and "ai_sentiment" in df_all_copy.columns) else pd.Series(dtype=int)
    overall_dominant_sentiment = sent_counts.index[0] if not sent_counts.empty else "Netral"

    # Periksa apakah ada metadata agregat multi-video (youtube_videos_meta_all.csv)
    scrap_dir = os.path.dirname(meta_csv_path) if meta_csv_path else ""
    all_meta_csv = os.path.join(scrap_dir, "youtube_videos_meta_all.csv") if scrap_dir else ""
    target_meta_csv = all_meta_csv if (all_meta_csv and os.path.exists(all_meta_csv)) else meta_csv_path

    video_list = []
    total_views = 0
    total_video_likes = 0
    primary_title = f"Video YouTube ({video_id})"
    primary_channel = "YouTube Channel"
    primary_url = f"https://www.youtube.com/watch?v={video_id}"
    primary_published = "-"

    if os.path.exists(target_meta_csv):
        try:
            df_meta = pd.read_csv(target_meta_csv)
            if not df_meta.empty:
                for idx, m_row in df_meta.iterrows():
                    v_id = str(m_row.get("video_id") or f"video_{idx}")
                    v_title = str(m_row.get("video_title") or f"Video {v_id}")
                    v_channel = str(m_row.get("channel_name") or "YouTube Channel")
                    v_url = str(m_row.get("video_url") or f"https://www.youtube.com/watch?v={v_id}")
                    v_published = str(m_row.get("published_at") or "-")
                    v_views_int = int(pd.to_numeric(m_row.get("views", 0), errors="coerce") or 0)
                    v_likes_int = int(pd.to_numeric(m_row.get("video_likes", 0), errors="coerce") or 0)

                    total_views += v_views_int
                    total_video_likes += v_likes_int

                    # Filter komentar khusus video ini jika kolom video_id tersedia
                    if not df_all_copy.empty and "video_id" in df_all_copy.columns:
                        v_df = df_all_copy[df_all_copy["video_id"].astype(str) == v_id]
                    else:
                        v_df = df_all_copy if idx == 0 else pd.DataFrame()

                    v_comment_count = len(v_df)
                    v_comment_likes = int(v_df["like_count"].sum()) if not v_df.empty else 0
                    v_sents = v_df["ai_sentiment"].value_counts() if (not v_df.empty and "ai_sentiment" in v_df.columns) else pd.Series(dtype=int)
                    v_dom_sent = v_sents.index[0] if not v_sents.empty else overall_dominant_sentiment

                    video_entry = {
                        "video_id": v_id,
                        "video_url": v_url,
                        "caption": v_title,
                        "video_title": v_title,
                        "channel_name": v_channel,
                        "published_at": v_published,
                        "views": f"{v_views_int:,}",
                        "views_int": v_views_int,
                        "video_likes": v_likes_int,
                        "comment_count": v_comment_count,
                        "total_likes": v_comment_likes,
                        "dominant_sentiment": v_dom_sent,
                    }
                    video_list.append(video_entry)

                    if idx == 0:
                        primary_title = v_title
                        primary_channel = v_channel
                        primary_url = v_url
                        primary_published = v_published
        except Exception as e:
            print(f"[WARNING] Gagal membaca metadata video CSV: {e}")

    # Fallback jika video_list kosong
    if not video_list:
        fallback_entry = {
            "video_id": video_id,
            "video_url": primary_url,
            "caption": primary_title,
            "video_title": primary_title,
            "channel_name": primary_channel,
            "published_at": primary_published,
            "views": "0",
            "views_int": 0,
            "video_likes": 0,
            "comment_count": total_comment_count,
            "total_likes": total_comment_likes,
            "dominant_sentiment": overall_dominant_sentiment,
        }
        video_list = [fallback_entry]

    total_videos = len(video_list)
    avg_views = int(total_views / total_videos) if total_videos > 0 else 0
    top_videos = sorted(video_list, key=lambda x: x.get("views_int", 0), reverse=True)[:10]

    if total_videos > 1:
        primary_title = f"Multi-Video Corpus ({total_videos} Video): {primary_title}"

    # Kumpulkan Top 10 komentar dengan likes tertinggi dari seluruh corpus
    top_comments = []
    if not df_all_copy.empty:
        top_df = df_all_copy.sort_values(by=["like_count", "reply_count"], ascending=[False, False]).head(10)
        for _, crow in top_df.iterrows():
            top_comments.append(
                {
                    "comment_id": str(crow.get("comment_id", "")),
                    "username": str(crow.get("username", "Anonim")),
                    "comment_text": str(crow.get("comment_text", ""))[:220],
                    "like_count": int(crow.get("like_count", 0)),
                    "reply_count": int(crow.get("reply_count", 0)),
                    "ai_sentiment": str(crow.get("ai_sentiment", "Netral")),
                    "business_category": str(crow.get("business_category", "")),
                    "is_hearted": bool(str(crow.get("is_hearted", "")).lower() in ["true", "1"]),
                    "video_title": str(crow.get("video_title", "")),
                }
            )

    return {
        "total_videos": total_videos,
        "total_views": total_views,
        "average_views": avg_views,
        "video_likes": total_video_likes,
        "video_title": primary_title,
        "channel_name": primary_channel,
        "video_url": primary_url,
        "published_at": primary_published,
        "video_list": video_list,
        "top_videos": top_videos,
        "top_comments": top_comments,
    }


def _compute_official_response(df_engagement):
    total_official = int(df_engagement["official_comments"].sum()) if "official_comments" in df_engagement.columns else 0
    total_user = int(df_engagement["user_comments"].sum()) if "user_comments" in df_engagement.columns else 0
    total_hearted = int(df_engagement["hearted_comments"].sum()) if "hearted_comments" in df_engagement.columns else 0
    total_all = total_official + total_user

    df_gap = df_engagement[df_engagement["official_comments"] == 0].copy()
    df_gap = df_gap.sort_values("total_comments", ascending=False).head(5)

    reply_gap_topics = []
    for _, row in df_gap.iterrows():
        reply_gap_topics.append(
            {
                "topic_id": int(row["topic_id"]),
                "business_category": str(row["business_category"]),
                "sub_issue": str(row.get("sub_issue", "")),
                "ai_sentiment": str(row["ai_sentiment"]),
                "total_comments": int(row["total_comments"]),
                "total_likes": int(row.get("total_likes", 0)),
                "engagement_score": float(row["engagement_score"]),
            }
        )

    return {
        "global_distribution": {
            "official_comments": total_official,
            "user_comments": total_user,
            "hearted_comments": total_hearted,
            "official_ratio": round(total_official / total_all * 100, 2) if total_all > 0 else 0.0,
        },
        "reply_gap_top_5": reply_gap_topics,
    }


def _compute_engagement_analysis(df_engagement):
    df_sorted = df_engagement.sort_values("engagement_score", ascending=False)
    df_top = df_sorted[df_sorted["total_comments"] >= 3].head(5)
    if df_top.empty:
        df_top = df_sorted.head(5)

    top_engaging_topics = []
    for _, row in df_top.iterrows():
        top_engaging_topics.append(
            {
                "business_category": str(row["business_category"]),
                "sub_issue": str(row.get("sub_issue", "")),
                "ai_sentiment": str(row["ai_sentiment"]),
                "engagement_score": float(row["engagement_score"]),
                "total_comments": int(row["total_comments"]),
                "total_replies": int(row["sum_reply_count"]),
                "total_likes": int(row.get("total_likes", 0)),
            }
        )

    return {"top_engaging_topics": top_engaging_topics}


def _compute_monthly_trend(df_all):
    if df_all.empty:
        return []

    df_temp = df_all.copy()
    df_temp["created_dt"] = pd.to_datetime(df_temp["created_at"], errors="coerce")
    valid = df_temp[df_temp["created_dt"].notna()].copy()

    if valid.empty:
        return []

    valid["year_month"] = valid["created_dt"].dt.to_period("M").astype(str)
    pivot = valid.groupby(["year_month", "ai_sentiment"]).size().unstack(fill_value=0)

    trend = []
    for month in sorted(pivot.index):
        row = pivot.loc[month]
        pos = int(row.get("Positif", 0))
        neg = int(row.get("Negatif", 0))
        net = int(row.get("Netral", 0))
        total = pos + neg + net
        nsr = round((pos - neg) / total, 4) if total > 0 else 0.0

        trend.append(
            {
                "month": month,
                "positif": pos,
                "negatif": neg,
                "netral": net,
                "total": total,
                "net_sentiment_ratio": nsr,
            }
        )

    return trend


def _compute_spike_detection(df_all):
    spike_info = {"threshold": 0.0, "spikes": []}

    df_temp = df_all.copy()
    df_temp["created_dt"] = pd.to_datetime(df_temp["created_at"], errors="coerce")
    valid_dates = df_temp["created_dt"].dropna()

    if len(valid_dates) > 0:
        df_temp["date_only"] = df_temp["created_dt"].dt.date
        comments_by_date = df_temp.groupby("date_only").size()

        date_idx = pd.date_range(start=valid_dates.min().date(), end=valid_dates.max().date())
        ts_comments = pd.Series(0, index=date_idx.date)
        for d, val in comments_by_date.items():
            if d in ts_comments.index:
                ts_comments[d] = val

        if len(ts_comments) > 0:
            median_comments = float(ts_comments.median())
            std_comments = float(ts_comments.std()) if len(ts_comments) > 1 else 0.0
            threshold = round(median_comments + 2.5 * std_comments, 2)
            if std_comments == 0 or np.isnan(threshold):
                threshold = median_comments + 5

            spike_info["threshold"] = threshold

            spike_dates = ts_comments[ts_comments > threshold].sort_values(ascending=False).head(5)
            if spike_dates.empty:
                spike_dates = comments_by_date.sort_values(ascending=False).head(5)

            spikes = []
            for date_val, count in spike_dates.items():
                date_str = date_val.strftime("%Y-%m-%d")
                day_df = df_temp[df_temp["date_only"] == date_val]

                day_df_valid = day_df[day_df["sub_issue"].fillna("").astype(str).str.strip() != ""]
                if len(day_df_valid) > 0:
                    topic_series = day_df_valid["sub_issue"].fillna("").astype(str).str.strip()
                    top_topics = topic_series.value_counts().head(3).index.tolist()
                else:
                    top_topics = []

                spikes.append(
                    {
                        "date": date_str,
                        "comment_count": int(count),
                        "top_topics": top_topics,
                    }
                )

            spike_info["spikes"] = spikes

    return spike_info


def _compute_keyword_analysis(df_topic_agg):
    result = {}
    if "top_keywords" not in df_topic_agg.columns:
        return result

    for sent_label in ["Positif", "Negatif", "Netral"]:
        df_valid = df_topic_agg[
            (df_topic_agg["ai_sentiment"] == sent_label) & (df_topic_agg["topic_id"] != -1)
        ].copy()

        keyword_stats = {}
        for _, row in df_valid.iterrows():
            keywords_raw = str(row.get("top_keywords", ""))
            if not keywords_raw or keywords_raw == "nan":
                continue

            keywords = [kw.strip().lower() for kw in keywords_raw.split(",") if kw.strip()]
            comment_count = int(row["comment_count"])

            for kw in keywords:
                if kw not in keyword_stats:
                    keyword_stats[kw] = {"topic_count": 0, "weighted_comment_count": 0}
                keyword_stats[kw]["topic_count"] += 1
                keyword_stats[kw]["weighted_comment_count"] += comment_count

        kw_list = [
            {
                "keyword": kw,
                "topic_count": stats["topic_count"],
                "weighted_comment_count": stats["weighted_comment_count"],
            }
            for kw, stats in keyword_stats.items()
        ]
        kw_list.sort(key=lambda x: x["weighted_comment_count"], reverse=True)
        result[sent_label] = kw_list

    return result


def run_eda(config_override=None):
    print("=== LANGKAH 5: EDA STATS KOMENTAR YOUTUBE ===")

    cfg = config_override or {}
    raw_url = cfg.get("YOUTUBE_VIDEO_URL", AppConfig.YOUTUBE_VIDEO_URL)
    video_id = extract_youtube_video_id(raw_url) or AppConfig.YOUTUBE_VIDEO_ID
    output_dir = cfg.get("OUTPUT_DIR", AppConfig.OUTPUT_YOUTUBE_DIR)

    csv_output_dir = os.path.join(output_dir, "csv")
    json_output_dir = os.path.join(output_dir, "json")
    os.makedirs(json_output_dir, exist_ok=True)

    bcs_path = os.path.join(csv_output_dir, "business_category_youtube_summary.csv")
    mapping_path = os.path.join(csv_output_dir, "mapping_review_topic_youtube_final.csv")
    engagement_path = os.path.join(csv_output_dir, "youtube_engagement_metrics.csv")
    topic_agg_path = os.path.join(csv_output_dir, "master_topic_youtube_agregasi.csv")

    if not all(os.path.exists(p) for p in [bcs_path, mapping_path, engagement_path, topic_agg_path]):
        raise PipelineError("File agregasi / metrics YouTube tidak lengkap. Harap selesaikan Langkah 3 dan 4.")

    df_bcs = pd.read_csv(bcs_path)
    df_all = pd.read_csv(mapping_path)
    df_engagement = pd.read_csv(engagement_path)
    df_topic_agg = pd.read_csv(topic_agg_path)

    meta_csv_path = os.path.join(output_dir, "scrap", f"youtube_video_meta_{video_id}.csv")
    video_analysis = _compute_video_analysis(meta_csv_path, df_all, video_id)

    eda_results = {
        "overview": _compute_overview(df_bcs, df_all),
        "topic_analysis": _compute_topic_analysis(df_bcs, df_all),
        "official_response": _compute_official_response(df_engagement),
        "engagement_analysis": _compute_engagement_analysis(df_engagement),
        "trends": _compute_monthly_trend(df_all),
        "spike_detection": _compute_spike_detection(df_all),
        "keyword_analysis": _compute_keyword_analysis(df_topic_agg),
        "video_analysis": video_analysis,
    }

    try:
        dt_series = pd.to_datetime(df_all["created_at"], errors="coerce").dropna()
        start_date = dt_series.min().strftime("%Y-%m-%d") if not dt_series.empty else "-"
        end_date = dt_series.max().strftime("%Y-%m-%d") if not dt_series.empty else "-"
    except Exception:
        start_date = "-"
        end_date = "-"

    app_name_cfg = cfg.get("YOUTUBE_APP_NAME", AppConfig.YOUTUBE_APP_NAME)
    if app_name_cfg in ("YouTube Video", f"YouTube - {video_id}") and video_analysis.get("video_title"):
        display_name = f"YouTube - {video_analysis['video_title'][:50]}"
    else:
        display_name = app_name_cfg

    eda_results["meta"] = {
        "app_name": display_name,
        "video_id": video_id,
        "video_url": video_analysis.get("video_url", f"https://www.youtube.com/watch?v={video_id}"),
        "video_title": video_analysis.get("video_title", ""),
        "channel_name": video_analysis.get("channel_name", ""),
        "date_range": {"start": start_date, "end": end_date},
    }

    out_json = os.path.join(json_output_dir, "youtube_eda_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(eda_results, f, ensure_ascii=False, indent=2)

    print(f"[SUCCESS] EDA Stats YouTube berhasil digenerate: {out_json}")


if __name__ == "__main__":
    run_eda()
