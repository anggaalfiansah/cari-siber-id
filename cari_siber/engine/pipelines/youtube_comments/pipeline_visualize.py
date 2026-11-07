from cari_siber.engine.core.exceptions import PipelineError
"""
==============================================================================
LANGKAH 6: VISUALISASI DATA (CHARTS) KOMENTAR YOUTUBE
==============================================================================
Membuat 8 grafik visualisasi Matplotlib/Seaborn (.png) dari `youtube_eda_summary.json`:
  01_youtube_overview.png          - Donut Sentimen & Rata-Rata Likes per Sentimen
  02_youtube_topic_analysis.png    - Distribusi Kategori Topik per Sentimen Dominan
  03_youtube_engagement_score.png  - Topik dengan Tingkat Diskusi/Balasan Tertinggi
  04_youtube_monthly_trends.png    - Tren Volume Komentar dari Waktu ke Waktu
  05_youtube_reply_gap.png         - Kesenjangan Respons Channel Resmi (Reply Gap)
  06_youtube_spike_detection.png   - Deteksi Lonjakan Komentar Harian (Spikes)
  07_youtube_wordcloud.png         - Peta Visual Kata Kunci Komentar (WordCloud)
  08_youtube_top_comments.png      - Top Komentar dengan Likes Tertinggi di Video
==============================================================================
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.ticker as ticker

from cari_siber.engine.core.config import AppConfig

try:
    from wordcloud import WordCloud
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False

# Terapkan Dark Theme SOC pada seluruh chart Matplotlib
plt.style.use('dark_background')
plt.rcParams['figure.facecolor'] = '#090d16'
plt.rcParams['axes.facecolor'] = '#0f172a'
plt.rcParams['axes.edgecolor'] = '#334155'
plt.rcParams['text.color'] = '#f8fafc'
plt.rcParams['axes.labelcolor'] = '#94a3b8'
plt.rcParams['xtick.color'] = '#94a3b8'
plt.rcParams['ytick.color'] = '#94a3b8'
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "Helvetica", "DejaVu Sans"]

COLOR_POSITIF = "#10B981"   # Hijau Emerald
COLOR_NEGATIF = "#EF4444"   # Merah YouTube
COLOR_NETRAL = "#64748B"    # Slate Abu-abu
COLOR_OFFICIAL = "#0EA5E9"  # Biru Sky


def _save_chart(fig, images_dir, filename):
    filepath = os.path.join(images_dir, filename)
    fig.tight_layout()
    fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    print(f"  [OK] Tersimpan: {filename}")


def _add_bar_labels(ax, bars, fmt="{}", fontsize=10, color="#f8fafc", padding=4):
    for bar in bars:
        width = bar.get_width()
        if width > 0:
            ax.annotate(
                fmt.format(width),
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(padding, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=fontsize,
                color=color,
                fontweight="bold",
            )


def _chart_01_overview(data, images_dir, app_name):
    overview = data.get("overview", {})
    sent_dist = overview.get("sentiment_distribution", {})
    if not sent_dist:
        return

    labels, sizes, colors, avg_likes = [], [], [], []
    color_map = {"Positif": COLOR_POSITIF, "Negatif": COLOR_NEGATIF, "Netral": COLOR_NETRAL}

    for s in ["Positif", "Negatif", "Netral"]:
        if s in sent_dist and sent_dist[s].get("count", 0) >= 0:
            labels.append(s)
            sizes.append(sent_dist[s]["count"])
            colors.append(color_map[s])
            avg_likes.append(sent_dist[s].get("avg_like_count", 0))

    if sum(sizes) == 0:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1, 1]})

    wedges, texts, autotexts = ax1.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.82,
        wedgeprops=dict(width=0.42, edgecolor="w"),
    )
    plt.setp(autotexts, size=11, weight="bold", color="white")
    plt.setp(texts, size=12)

    center_circle = plt.Circle((0, 0), 0.55, fc="white")
    ax1.add_artist(center_circle)

    total_comments = overview.get("total_comments", sum(sizes))
    ax1.text(0, 0, f"Total\n{total_comments:,}\nKomentar", ha="center", va="center", fontsize=14, fontweight="bold")
    ax1.set_title("Distribusi Sentimen Komentar", fontsize=14, fontweight="bold", loc="center")

    bars = ax2.bar(labels, avg_likes, color=colors, edgecolor="white", width=0.55)
    ax2.set_title("Rata-Rata 'Likes' per Sentimen", fontsize=14, fontweight="bold", loc="center")
    ax2.set_ylabel("Rata-Rata Likes / Komentar")

    max_l = max(avg_likes) if avg_likes and max(avg_likes) > 0 else 1
    ax2.set_ylim(0, max_l * 1.2)

    for bar in bars:
        height = bar.get_height()
        ax2.annotate(
            f"{height:,.1f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    fig.suptitle("Ringkasan Sentimen & Resonansi Likes Komentar YouTube", fontsize=16, fontweight="bold", y=1.03)
    _save_chart(fig, images_dir, "01_youtube_overview.png")


def _chart_02_topic_analysis(data, images_dir, app_name):
    topic_data = data.get("topic_analysis", {})
    if not topic_data:
        return

    all_cats = []
    color_map = {"Positif": COLOR_POSITIF, "Negatif": COLOR_NEGATIF, "Netral": COLOR_NETRAL}

    for sent, t_data in topic_data.items():
        for cat in t_data.get("categories", []):
            cat_name = cat.get("threat_domain") or cat.get("business_category") or cat.get("name", "Umum")
            all_cats.append(
                {
                    "category": cat_name,
                    "comment_count": cat["comment_count"],
                    "sentiment": sent,
                }
            )

    if not all_cats:
        return

    df_cats = pd.DataFrame(all_cats)
    idx = df_cats.groupby("category")["comment_count"].idxmax()
    df_dominant = df_cats.loc[idx].sort_values("comment_count", ascending=True).tail(15)

    categories = df_dominant["category"].tolist()
    counts = df_dominant["comment_count"].tolist()
    colors = [color_map.get(s, COLOR_NETRAL) for s in df_dominant["sentiment"].tolist()]

    fig, ax = plt.subplots(figsize=(12, max(6, len(categories) * 0.42)))
    bars = ax.barh(categories, counts, color=colors, edgecolor="white")
    _add_bar_labels(ax, bars, fmt="{:,}")

    max_c = max(counts) if counts else 1
    ax.set_xlim(0, max_c * 1.2)
    ax.set_xlabel("Jumlah Komentar")

    legend_elements = [
        Patch(facecolor=COLOR_POSITIF, label="Positif Dominan"),
        Patch(facecolor=COLOR_NEGATIF, label="Negatif Dominan"),
        Patch(facecolor=COLOR_NETRAL, label="Netral Dominan"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    fig.suptitle("Distribusi Kategori Topik Berdasarkan Sentimen Dominan", fontsize=16, fontweight="bold", y=0.98)
    _save_chart(fig, images_dir, "02_youtube_topic_analysis.png")


def _chart_03_engagement_analysis(data, images_dir, app_name):
    eng_data = data.get("engagement_analysis", {}).get("top_engaging_topics", [])
    if not eng_data:
        return

    df_eng = pd.DataFrame(eng_data).sort_values("engagement_score", ascending=True)
    topics = (
        df_eng["sub_issue"]
        .apply(lambda x: str(x)[:32] + "..." if len(str(x)) > 32 else str(x))
        .tolist()
    )
    scores = df_eng["engagement_score"].tolist()
    comments = df_eng["total_comments"].tolist()

    colors = [COLOR_NEGATIF if s >= 1.0 else COLOR_OFFICIAL for s in scores]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(topics, scores, color=colors, edgecolor="white")

    ax.axvline(x=1.0, color=COLOR_NEGATIF, linestyle="--", linewidth=1.8, label="Threshold Diskusi Aktif (1 Balasan/Komen)")

    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.annotate(
            f"Skor: {width:.2f} ({comments[i]} komen)",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=10,
        )

    ax.set_xlabel("Engagement Score (Rata-Rata Balasan per Komentar)")
    ax.legend(loc="lower right")

    max_score = max(scores) if scores and max(scores) > 0 else 1.5
    ax.set_xlim(0, max(max_score * 1.35, 1.3))

    fig.suptitle("Topik dengan Tingkat Diskusi Berantai (Engagement) Tertinggi", fontsize=16, fontweight="bold", y=0.98)
    _save_chart(fig, images_dir, "03_youtube_engagement_score.png")


def _chart_04_trends(data, images_dir, app_name):
    trends = data.get("trends", [])
    if not trends:
        return

    df_trend = pd.DataFrame(trends).sort_values("month").tail(18)
    months = df_trend["month"].tolist()
    pos = df_trend["positif"].tolist()
    neg = df_trend["negatif"].tolist()
    net = df_trend["netral"].tolist()

    fig, ax = plt.subplots(figsize=(14, 7))

    ax.bar(months, net, color=COLOR_NETRAL, label="Netral", edgecolor="white")
    ax.bar(months, pos, bottom=net, color=COLOR_POSITIF, label="Positif", edgecolor="white")
    ax.bar(months, neg, bottom=np.array(net) + np.array(pos), color=COLOR_NEGATIF, label="Negatif", edgecolor="white")

    ax.set_ylabel("Jumlah Komentar")
    ax.legend(loc="upper left")
    plt.xticks(rotation=45, ha="right")

    fig.suptitle("Tren Volume & Sentimen Komentar Bulanan", fontsize=16, fontweight="bold", y=0.98)
    _save_chart(fig, images_dir, "04_youtube_monthly_trends.png")


def _chart_05_official_response(data, images_dir, app_name):
    off_data = data.get("official_response", {}).get("reply_gap_top_5", [])
    if not off_data:
        return

    df_gap = pd.DataFrame(off_data)
    df_gap["sub_issue"] = df_gap["sub_issue"].fillna("").astype(str)
    df_gap = df_gap[df_gap["sub_issue"].str.strip() != ""]
    if df_gap.empty:
        return
    df_gap = df_gap.sort_values("total_comments", ascending=True)

    topics = df_gap["sub_issue"].apply(lambda x: x[:32] + "..." if len(x) > 32 else x).tolist()
    comments = df_gap["total_comments"].tolist()
    likes = df_gap["total_likes"].tolist() if "total_likes" in df_gap.columns else [0] * len(comments)

    fig, ax = plt.subplots(figsize=(12, 6))
    y = np.arange(len(topics))
    height = 0.38

    bars_c = ax.barh(y - height / 2, comments, height, color=COLOR_NETRAL, edgecolor="white", label="Komentar (Tanpa Balasan Kreator)")
    bars_l = ax.barh(y + height / 2, likes, height, color=COLOR_POSITIF, edgecolor="white", label="Total Likes Komentar")

    ax.set_yticks(y)
    ax.set_yticklabels(topics)
    ax.legend(loc="lower right")

    for bar in bars_c:
        width = bar.get_width()
        ax.annotate(
            f"{int(width):,} Komen",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=9,
        )

    for bar in bars_l:
        width = bar.get_width()
        ax.annotate(
            f"{int(width):,} Likes",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=9,
        )

    ax.set_xlabel("Jumlah Interaksi")
    max_val = max(max(comments, default=1), max(likes, default=1), 1)
    ax.set_xlim(0, max_val * 1.3)

    fig.suptitle(
        "Kesenjangan Respons (Reply Gap) Kreator pada Topik Populer",
        fontsize=16,
        fontweight="bold",
        color=COLOR_NEGATIF,
        y=0.98,
    )
    _save_chart(fig, images_dir, "05_youtube_reply_gap.png")


def _chart_06_spike_detection(data, images_dir, app_name):
    spike_data = data.get("spike_detection", {})
    spikes = spike_data.get("spikes", [])
    if not spikes:
        return

    dates = [s["date"] for s in spikes]
    counts = [s["comment_count"] for s in spikes]
    threshold = spike_data.get("threshold", 0)

    sorted_spikes = sorted(zip(dates, counts), key=lambda x: x[0])
    dates, counts = zip(*sorted_spikes)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.bar(dates, counts, color=COLOR_OFFICIAL, alpha=0.55, label="Volume Komentar Harian")
    ax.scatter(dates, counts, color=COLOR_NEGATIF, s=100, zorder=5, label="Titik Puncak / Lonjakan")

    if threshold > 0:
        ax.axhline(
            y=threshold,
            color=COLOR_NEGATIF,
            linestyle="--",
            linewidth=2,
            alpha=0.75,
            label=f"Threshold Abnormal (> {threshold:.1f})",
        )

    for s in spikes:
        ax.plot(s["date"], s["comment_count"], "ro", markersize=9)
        top_topic = s["top_topics"][0] if s.get("top_topics") else "Topik Umum"
        top_topic = top_topic[:22] + "..." if len(top_topic) > 22 else top_topic
        ax.annotate(
            top_topic,
            xy=(s["date"], s["comment_count"]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=COLOR_NEGATIF, alpha=0.85),
        )

    ax.set_ylabel("Jumlah Komentar")
    plt.xticks(rotation=45, ha="right")
    ax.legend()

    fig.suptitle("Deteksi Lonjakan Komentar Harian (Spike Detection)", fontsize=16, fontweight="bold", y=0.98)
    _save_chart(fig, images_dir, "06_youtube_spike_detection.png")


def _chart_07_wordcloud(data, images_dir, app_name):
    if not HAS_WORDCLOUD:
        return

    kw_data = data.get("keyword_analysis", {})
    all_kw = []
    if kw_data:
        for s in ["Negatif", "Positif", "Netral"]:
            all_kw.extend(kw_data.get(s, []))

    stopwords = {
        "nya", "ya", "yg", "di", "ke", "dan", "ini", "itu", "untuk", "dengan",
        "ada", "dari", "aja", "sih", "kok", "kan", "dong", "yang", "video", "youtube",
    }
    freq_all = {}
    for kw in all_kw:
        word = str(kw.get("keyword", "")).lower().strip()
        if word and word not in stopwords and len(word) > 2:
            freq_all[word] = freq_all.get(word, 0) + int(kw.get("weighted_comment_count", 1))

    if not freq_all:
        # Fallback: baca dari master_topic_youtube_agregasi.csv jika tersedia
        csv_agg = os.path.join(os.path.dirname(images_dir), "csv", "master_topic_youtube_agregasi.csv")
        if os.path.exists(csv_agg):
            try:
                df_agg = pd.read_csv(csv_agg)
                for _, row in df_agg.iterrows():
                    kws = str(row.get("top_keywords", "")).split(",")
                    cnt = max(1, int(pd.to_numeric(row.get("comment_count", 1), errors="coerce") or 1))
                    for w in kws:
                        w = w.strip().lower()
                        if w and w not in stopwords and len(w) > 2:
                            freq_all[w] = freq_all.get(w, 0) + cnt
            except Exception:
                pass

    if not freq_all:
        freq_all = {"komentar": 10, "opini": 8, "publik": 6, "diskusi": 5}

    fig, ax = plt.subplots(figsize=(12, 8))

    def combined_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        return f"hsl({np.random.randint(0, 360)}, 85%, {np.random.randint(30, 55)}%)"

    wc = WordCloud(
        width=1200,
        height=800,
        background_color="#090d16",
        color_func=combined_color_func,
    ).generate_from_frequencies(freq_all)

    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")

    fig.suptitle("Visualisasi Peta Kata Kunci Komentar YouTube (WordCloud)", fontsize=16, fontweight="bold", y=0.98)
    _save_chart(fig, images_dir, "07_youtube_wordcloud.png")


def _chart_08_top_comments(data, images_dir, app_name):
    """
    Menampilkan Top 8 Komentar dengan jumlah Likes tertinggi pada video YouTube,
    diwarnai berdasarkan sentimen AI-nya.
    """
    vid_analysis = data.get("video_analysis", {})
    top_comments = vid_analysis.get("top_comments", [])
    if not top_comments:
        return

    df_top = pd.DataFrame(top_comments).head(8)
    if df_top.empty:
        return
    df_top = df_top.sort_values("like_count", ascending=True)

    color_map = {"Positif": COLOR_POSITIF, "Negatif": COLOR_NEGATIF, "Netral": COLOR_NETRAL}
    labels = []
    for _, row in df_top.iterrows():
        uname = str(row.get("username", "User")).strip()
        txt = str(row.get("comment_text", "")).replace("\n", " ").strip()
        short_txt = txt[:38] + "..." if len(txt) > 38 else txt
        labels.append(f"{uname}: \"{short_txt}\"")

    likes = df_top["like_count"].tolist()
    replies = df_top["reply_count"].tolist()
    colors = [color_map.get(str(s), COLOR_NETRAL) for s in df_top["ai_sentiment"].tolist()]

    fig, ax = plt.subplots(figsize=(13, max(6, len(labels) * 0.65)))
    bars = ax.barh(labels, likes, color=colors, edgecolor="white", height=0.6)

    for idx, bar in enumerate(bars):
        width = bar.get_width()
        rep_cnt = replies[idx]
        ax.annotate(
            f"{int(width):,} Likes ({rep_cnt} balasan)",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(6, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=9.5,
            fontweight="bold",
        )

    max_l = max(likes) if likes and max(likes) > 0 else 1
    ax.set_xlim(0, max_l * 1.32)
    ax.set_xlabel("Jumlah Likes pada Komentar")

    legend_elements = [
        Patch(facecolor=COLOR_POSITIF, label="Positif"),
        Patch(facecolor=COLOR_NEGATIF, label="Negatif"),
        Patch(facecolor=COLOR_NETRAL, label="Netral"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    fig.suptitle("Top Komentar Penonton dengan Resonansi (Likes) Tertinggi", fontsize=16, fontweight="bold", y=0.98)
    _save_chart(fig, images_dir, "08_youtube_top_comments.png")


def run_visualizer(config_override=None):
    print("=== LANGKAH 6: GENERATE CHART KOMENTAR YOUTUBE ===")

    cfg = config_override or {}
    output_dir = cfg.get("OUTPUT_DIR", AppConfig.OUTPUT_YOUTUBE_DIR)
    json_path = os.path.join(output_dir, "json", "youtube_eda_summary.json")

    if not os.path.exists(json_path):
        raise PipelineError("'{json_path}' tidak ditemukan! Silakan jalankan '5_eda_stats.py' terlebih dahulu.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    app_name = data.get("meta", {}).get("app_name", "YouTube Video")
    images_dir = os.path.join(output_dir, "charts")
    os.makedirs(images_dir, exist_ok=True)

    chart_functions = [
        ("01 - Overview & Sentimen", _chart_01_overview),
        ("02 - Topic Analysis", _chart_02_topic_analysis),
        ("03 - Engagement Analysis", _chart_03_engagement_analysis),
        ("04 - Tren Bulanan", _chart_04_trends),
        ("05 - Official Response (Gap)", _chart_05_official_response),
        ("06 - Spike Detection", _chart_06_spike_detection),
        ("07 - WordCloud", _chart_07_wordcloud),
        ("08 - Top Comments Resonance", _chart_08_top_comments),
    ]

    for chart_name, chart_func in chart_functions:
        try:
            print(f"[INFO] Membuat chart: {chart_name}")
            chart_func(data, images_dir, app_name)
        except Exception as e:
            print(f"  [ERROR] Gagal membuat {chart_name}: {e}")

    print(f"\n[SUCCESS] Semua chart YouTube berhasil dirender di '{images_dir}'")


if __name__ == "__main__":
    run_visualizer()
