import os
import json
import base64
from typing import Dict, Any, Optional, List
import pandas as pd


class ResultsService:
    @staticmethod
    def load_run_results(run_dir: str) -> Optional[Dict[str, Any]]:
        """
        Loads and compiles all artifacts from a completed run into a structured dict for the UI.
        """
        if not os.path.exists(run_dir):
            return None

        # 1. Load EDA summary JSON
        eda_path = os.path.join(run_dir, "json", "youtube_eda_summary.json")
        eda_data = {}
        if os.path.exists(eda_path):
            try:
                with open(eda_path, "r", encoding="utf-8") as f:
                    eda_data = json.load(f)
            except Exception:
                pass

        meta = eda_data.get("meta", {})
        overview = eda_data.get("overview", {})
        video_title = meta.get("video_title", meta.get("app_name", "YouTube Video"))
        channel_name = meta.get("channel_name", "")

        # 2. Load Topics Table first so topics is always defined
        topics = []
        agregasi_csv = os.path.join(run_dir, "csv", "master_topic_youtube_agregasi.csv")
        if os.path.exists(agregasi_csv):
            try:
                df_top = pd.read_csv(agregasi_csv)
                for _, row in df_top.head(25).iterrows():
                    # Support comment_count, total_comments, Count, count, review_count
                    cnt = None
                    for col_name in ["comment_count", "total_comments", "Count", "count", "review_count"]:
                        if col_name in row and pd.notna(row[col_name]):
                            cnt = row[col_name]
                            break
                    cnt = int(cnt) if cnt is not None and pd.notna(cnt) else 0

                    sample = row.get("sample_comments")
                    if pd.isna(sample) or not sample:
                        sample = row.get("sample_comment", "")

                    raw_sentiment = str(row.get("dominant_sentiment", row.get("ai_sentiment", "Netral"))).strip()
                    if raw_sentiment.lower() in ("nan", "none", "", "null"):
                        raw_sentiment = "Netral"
                    raw_sentiment = raw_sentiment.capitalize()
                    if raw_sentiment not in ("Positif", "Negatif", "Netral"):
                        raw_sentiment = "Netral"

                    b_cat = str(row.get("business_category", "")).strip()
                    if b_cat.lower() in ("nan", "none", "", "null"):
                        b_cat = "Isu Publik"

                    sub_iss = str(row.get("sub_issue", "")).strip()
                    if sub_iss.lower() in ("nan", "none", "", "null"):
                        sub_iss = str(row.get("topic_name", ""))

                    raw_kw = str(row.get("top_keywords", row.get("topic_name", ""))).strip()

                    topics.append({
                        "topic_id": int(row.get("topic_id", 0)) if pd.notna(row.get("topic_id")) else 0,
                        "topic_name": str(row.get("topic_name", "")),
                        "category": b_cat,
                        "sub_issue": sub_iss,
                        "keywords": raw_kw,
                        "sentiment": raw_sentiment,
                        "total_comments": cnt,
                        "sample_comment": str(sample)[:140],
                    })
            except Exception:
                pass

        # 3. Load Final Classification CSV for exact counts
        final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_final.csv")
        if not os.path.exists(final_csv):
            final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_raw.csv")

        df_final = None
        if os.path.exists(final_csv):
            try:
                df_final = pd.read_csv(final_csv)
            except Exception:
                pass

        total_comments = overview.get("total_comments")
        if not total_comments:
            total_comments = len(df_final) if df_final is not None else 0
        if not total_comments and topics:
            total_comments = sum(t["total_comments"] for t in topics)

        # 4. Load narrative insights markdown
        narrative_path = os.path.join(run_dir, "reports", "narrative_insights.md")
        narrative_md = ""
        if os.path.exists(narrative_path):
            try:
                with open(narrative_path, "r", encoding="utf-8") as f:
                    narrative_md = f.read()
            except Exception:
                narrative_md = "Gagal memuat dokumen narasi insight."
        else:
            narrative_md = "Narasi insight belum dibuat atau analisis belum selesai."

        # 5. Load Charts as Base64 Data URIs
        charts_dir = os.path.join(run_dir, "charts")
        charts = []
        if os.path.isdir(charts_dir):
            for filename in sorted(os.listdir(charts_dir)):
                if filename.lower().endswith(".png"):
                    chart_path = os.path.join(charts_dir, filename)
                    try:
                        with open(chart_path, "rb") as img_f:
                            b64_str = base64.b64encode(img_f.read()).decode("utf-8")
                            title = filename.replace(".png", "").replace("_", " ").title()
                            charts.append({
                                "id": filename,
                                "title": title,
                                "data_uri": f"data:image/png;base64,{b64_str}",
                            })
                    except Exception:
                        pass

        # 6. Format Interactive Recharts Data
        raw_sent = overview.get("sentiment_distribution", {})
        pos_cnt = 0
        neg_cnt = 0
        net_cnt = 0

        if isinstance(raw_sent, dict) and raw_sent:
            def _extract_c(key):
                val = raw_sent.get(key, 0)
                if isinstance(val, dict):
                    return int(val.get("count", 0))
                return int(val) if val else 0
            pos_cnt = _extract_c("Positif")
            neg_cnt = _extract_c("Negatif")
            net_cnt = _extract_c("Netral")
        elif df_final is not None and not df_final.empty and "ai_sentiment" in df_final.columns:
            vc = df_final["ai_sentiment"].value_counts().to_dict()
            pos_cnt = int(vc.get("Positif", 0))
            neg_cnt = int(vc.get("Negatif", 0))
            net_cnt = int(vc.get("Netral", 0))

        # Fallback sentiment counts from topics if overview was zero
        if pos_cnt == 0 and neg_cnt == 0 and net_cnt == 0 and topics:
            for t in topics:
                sent = str(t.get("sentiment", "")).strip().capitalize()
                t_count = int(t.get("total_comments", 0))
                if "Pos" in sent:
                    pos_cnt += t_count
                elif "Neg" in sent:
                    neg_cnt += t_count
                else:
                    net_cnt += t_count

        sentiment_chart_data = [
            {"name": "Positif", "value": pos_cnt, "color": "#10B981"},
            {"name": "Netral", "value": net_cnt, "color": "#64748B"},
            {"name": "Negatif", "value": neg_cnt, "color": "#EF4444"},
        ]

        # Top Topics bar chart data: filter out outlier topic -1 and sort by count descending
        valid_topics = [t for t in topics if t.get("topic_id") != -1 and t.get("total_comments", 0) > 0]
        valid_topics.sort(key=lambda x: x["total_comments"], reverse=True)

        topic_chart_data = []
        for t in valid_topics[:8]:
            title = t.get("sub_issue") or t.get("category") or t.get("topic_name", "")
            short_title = title[:24] + ("..." if len(title) > 24 else "")
            topic_chart_data.append({
                "topic": short_title,
                "full_topic": title,
                "category": t.get("category", "Umum"),
                "keywords": t.get("keywords", t.get("topic_name", "")),
                "count": t["total_comments"],
                "sentiment": t["sentiment"],
            })

        # 5. Load Cross-Video Intelligence (if multi-video run)
        cross_intel = None
        cross_json_path = os.path.join(run_dir, "json", "cross_video_intelligence.json")
        if os.path.exists(cross_json_path):
            try:
                with open(cross_json_path, "r", encoding="utf-8") as cjf:
                    cross_intel = json.load(cjf)
            except Exception:
                pass

        # 6. Load Flagged Accounts (Buzzer, Spam Bot, & CIB Indicators)
        flagged_accounts = []
        flagged_json_path = os.path.join(run_dir, "json", "flagged_accounts.json")
        if os.path.exists(flagged_json_path):
            try:
                with open(flagged_json_path, "r", encoding="utf-8") as faf:
                    flagged_accounts = json.load(faf)
            except Exception:
                pass
        elif cross_intel and cross_intel.get("flagged_accounts"):
            flagged_accounts = cross_intel.get("flagged_accounts", [])
        elif df_final is not None and not df_final.empty:
            try:
                from cari_siber.services.intelligence import IntelligenceService
                flagged_accounts = IntelligenceService.calculate_flagged_accounts(df_final)
            except Exception:
                pass

        # 7. Sampel Komentar untuk Corpus Explorer (hingga 1.000 komentar)
        corpus_comments = []
        if df_final is not None and not df_final.empty:
            try:
                sample_df = df_final.head(1000)
                for _, crow in sample_df.iterrows():
                    corpus_comments.append({
                        "comment_id": str(crow.get("comment_id", "")),
                        "username": str(crow.get("username", "Anonim")),
                        "author_channel_id": str(crow.get("author_channel_id", "")),
                        "author_channel_url": str(crow.get("author_channel_url", "")),
                        "comment_text": str(crow.get("comment_text", "")),
                        "like_count": int(pd.to_numeric(crow.get("like_count", 0), errors="coerce") or 0),
                        "reply_count": int(pd.to_numeric(crow.get("reply_count", 0), errors="coerce") or 0),
                        "ai_sentiment": str(crow.get("ai_sentiment", "Netral")),
                        "topic_name": str(crow.get("topic_name", "")),
                        "business_category": str(crow.get("business_category", "")),
                        "sub_issue": str(crow.get("sub_issue", "")),
                        "video_id": str(crow.get("video_id", "")),
                        "video_title": str(crow.get("video_title", "")),
                        "created_at": str(crow.get("created_at", "")),
                        "is_reply": bool(str(crow.get("is_reply", "")).lower() in ["true", "1"]),
                        "is_hearted": bool(str(crow.get("is_hearted", "")).lower() in ["true", "1"]),
                        "is_pinned": bool(str(crow.get("is_pinned", "")).lower() in ["true", "1"]),
                    })
            except Exception:
                pass

        return {
            "meta": {
                "video_title": video_title,
                "channel_name": channel_name,
                "total_comments": total_comments,
                "run_dir": run_dir,
            },
            "topics": topics,
            "charts": charts,
            "narrative_md": narrative_md,
            "interactive_data": {
                "sentiment": sentiment_chart_data,
                "topics": topic_chart_data,
            },
            "flagged_accounts": flagged_accounts,
            "corpus_comments": corpus_comments,
            "cross_video": cross_intel,
        }

    @staticmethod
    def get_comments_by_author(run_dir: str, author_key: str) -> List[Dict[str, Any]]:
        """Mengambil seluruh riwayat komentar dari satu akun tertentu di suatu sesi run."""
        final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_final.csv")
        if not os.path.exists(final_csv):
            final_csv = os.path.join(run_dir, "csv", "mapping_review_topic_youtube_raw.csv")
        if not os.path.exists(final_csv):
            return []
        try:
            df = pd.read_csv(final_csv)
            author_id_col = "author_channel_id" if "author_channel_id" in df.columns else "username"
            user_col = "username" if "username" in df.columns else author_id_col

            mask = (df[author_id_col].astype(str) == str(author_key)) | (df[user_col].astype(str) == str(author_key))
            matched_df = df[mask]

            comments = []
            for _, crow in matched_df.iterrows():
                comments.append({
                    "comment_id": str(crow.get("comment_id", "")),
                    "comment_text": str(crow.get("comment_text", "")),
                    "like_count": int(pd.to_numeric(crow.get("like_count", 0), errors="coerce") or 0),
                    "reply_count": int(pd.to_numeric(crow.get("reply_count", 0), errors="coerce") or 0),
                    "ai_sentiment": str(crow.get("ai_sentiment", "Netral")),
                    "topic_name": str(crow.get("topic_name", "")),
                    "business_category": str(crow.get("business_category", "")),
                    "sub_issue": str(crow.get("sub_issue", "")),
                    "video_id": str(crow.get("video_id", "")),
                    "video_title": str(crow.get("video_title", "")),
                    "created_at": str(crow.get("created_at", "")),
                    "is_reply": bool(str(crow.get("is_reply", "")).lower() in ["true", "1"]),
                    "is_hearted": bool(str(crow.get("is_hearted", "")).lower() in ["true", "1"]),
                    "is_pinned": bool(str(crow.get("is_pinned", "")).lower() in ["true", "1"]),
                })
            comments.sort(key=lambda x: x["like_count"], reverse=True)
            return comments
        except Exception:
            return []
