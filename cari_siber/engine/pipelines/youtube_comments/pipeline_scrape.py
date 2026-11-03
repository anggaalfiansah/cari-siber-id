from cari_siber.engine.core.exceptions import PipelineError
"""
==============================================================================
LANGKAH 0: SCRAPING KOMENTAR VIDEO YOUTUBE (DUAL-ENGINE: API v3 + FALLBACK)
==============================================================================
Modul ini mengunduh metadata video beserta komentar utama (top-level) dan
balasan komentar (replies) dari sebuah video YouTube.

STRATEGI SCRAPING BERLAPIS (OTOMATIS):
  1. YouTube Data API v3 Resmi — digunakan secara otomatis apabila variabel
     `YOUTUBE_API_KEY` diset di file `.env`.
  2. youtube-comment-downloader — digunakan sebagai fallback otomatis apabila
     `YOUTUBE_API_KEY` kosong atau gagal, menggunakan pustaka Python tanpa API key.
  3. Built-in YouTube InnerTube Web API — fallback murni berbasis `requests`
     apabila paket `youtube-comment-downloader` belum terinstal.

OUTPUT:
  - {OUTPUT_YOUTUBE_DIR}/scrap/youtube_comments_video_{video_id}.csv
  - {OUTPUT_YOUTUBE_DIR}/scrap/youtube_video_meta_{video_id}.csv
==============================================================================
"""

import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
import requests

from cari_siber.engine.core.config import AppConfig, extract_youtube_video_id

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


# ==============================================================================
# UTILITAS PARSING ANGKA & TANGGAL RELATIF
# ==============================================================================

def parse_compact_number(val) -> int:
    """
    Mengubah representasi angka ringkas YouTube ('1.2K', '3,5 rb', '2 jt', '1.5M')
    menjadi integer murni.
    """
    if val is None or val == "":
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    text = str(val).strip().lower()
    text = text.replace("\u00a0", " ").strip()
    if not text:
        return 0

    multiplier = 1
    if any(k in text for k in ["rb", "ribu", "k"]):
        multiplier = 1_000
        text = re.sub(r"(rb|ribu|k)", "", text).strip()
    elif any(k in text for k in ["jt", "juta", "m"]):
        multiplier = 1_000_000
        text = re.sub(r"(jt|juta|m)", "", text).strip()
    elif any(k in text for k in ["miliar", "b"]):
        multiplier = 1_000_000_000
        text = re.sub(r"(miliar|b)", "", text).strip()

    if multiplier > 1:
        text = text.replace(",", ".")
        text = re.sub(r"[^0-9.]", "", text)
        try:
            return int(float(text) * multiplier)
        except ValueError:
            return 0
    else:
        digits = re.sub(r"[^0-9]", "", text)
        return int(digits) if digits else 0


def parse_relative_time_to_iso(time_str: str, reference_dt: datetime = None) -> str:
    """
    Mengubah waktu relatif YouTube (misal: '2 days ago', '3 bulan yang lalu',
    '1 year ago (edited)', atau ISO-8601 '2025-05-12T08:30:00Z') menjadi
    format standar 'YYYY-MM-DD HH:MM:SS'.
    """
    if not time_str:
        return ""
    raw = str(time_str).strip()

    try:
        if "T" in raw and ("Z" in raw or "+" in raw):
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    try:
        dt = datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    now = reference_dt or datetime.now()
    clean = re.sub(r"\(.*?\)", "", raw).strip().lower()

    if any(w in clean for w in ["baru saja", "just now", "moment"]):
        return now.strftime("%Y-%m-%d %H:%M:%S")

    match = re.search(r"(\d+)\s*([a-zA-Z]+)", clean)
    if not match:
        return now.strftime("%Y-%m-%d %H:%M:%S")

    amount = int(match.group(1))
    unit = match.group(2)

    if unit.startswith(("detik", "sec", "second")):
        delta = timedelta(seconds=amount)
    elif unit.startswith(("menit", "min", "minute")):
        delta = timedelta(minutes=amount)
    elif unit.startswith(("jam", "hour", "hr")):
        delta = timedelta(hours=amount)
    elif unit.startswith(("hari", "day")):
        delta = timedelta(days=amount)
    elif unit.startswith(("minggu", "week", "wk")):
        delta = timedelta(weeks=amount)
    elif unit.startswith(("bulan", "month", "mo")):
        delta = timedelta(days=amount * 30)
    elif unit.startswith(("tahun", "year", "yr")):
        delta = timedelta(days=amount * 365)
    else:
        delta = timedelta(days=0)

    estimated = now - delta
    return estimated.strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# EKSTRAKSI METADATA VIDEO DARI HALAMAN WEB YOUTUBE (TANPA API KEY)
# ==============================================================================

def fetch_video_metadata_from_web(video_id: str, session: requests.Session = None) -> dict:
    """
    Mengambil metadata video YouTube langsung dari halaman watch?v={video_id}
    menggunakan objek JSON ytInitialPlayerResponse & ytInitialData.
    """
    sess = session or requests.Session()
    url = f"https://www.youtube.com/watch?v={video_id}&hl=id"
    meta = {
        "video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "video_title": f"Video YouTube ({video_id})",
        "channel_name": "YouTube Channel",
        "channel_id": "",
        "published_at": "",
        "views": 0,
        "video_likes": 0,
        "total_comments_reported": 0,
        "description": "",
    }

    try:
        resp = sess.get(url, headers=DEFAULT_HEADERS, timeout=20)
        if resp.status_code != 200:
            return meta
        html = resp.text

        m_player = re.search(r"var ytInitialPlayerResponse\s*=\s*(\{.+?\});\s*(?:var|</script>)", html, re.DOTALL)
        if not m_player:
            m_player = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\});", html, re.DOTALL)
        if m_player:
            try:
                player_data = json.loads(m_player.group(1))
                vd = player_data.get("videoDetails", {})
                micro = (
                    player_data.get("microformat", {})
                    .get("playerMicroformatRenderer", {})
                )
                meta["video_title"] = vd.get("title") or meta["video_title"]
                meta["channel_name"] = vd.get("author") or meta["channel_name"]
                meta["channel_id"] = vd.get("channelId") or ""
                meta["views"] = parse_compact_number(vd.get("viewCount", 0))
                meta["description"] = (vd.get("shortDescription") or "")[:500]
                pub_date = micro.get("publishDate") or micro.get("uploadDate") or ""
                if pub_date:
                    meta["published_at"] = pub_date[:10]
            except Exception:
                pass

        m_likes = re.search(r'"label"\s*:\s*"([\d.,]+)\s+suka"', html, re.IGNORECASE)
        if not m_likes:
            m_likes = re.search(r'"label"\s*:\s*"([\d.,]+)\s+likes"', html, re.IGNORECASE)
        if m_likes:
            meta["video_likes"] = parse_compact_number(m_likes.group(1))

    except Exception as e:
        print(f"[WARNING] Gagal mengekstrak metadata halaman web video: {e}")

    return meta


# ==============================================================================
# METODE 1: YOUTUBE DATA API V3 RESMI (JIKA YOUTUBE_API_KEY TERSEDIA)
# ==============================================================================

def scrape_via_youtube_api_v3(
    video_id: str,
    api_key: str,
    max_comments: int = None,
    sort_by: str = "top",
    include_replies: bool = True,
):
    """
    Mengambil metadata video dan seluruh komentar menggunakan YouTube Data API v3 resmi.
    Mengembalikan tuple: (video_meta_dict, list_of_comment_dicts)
    """
    print("\n[API v3] Menggunakan YouTube Data API v3 resmi...")
    session = requests.Session()

    vid_url = "https://www.googleapis.com/youtube/v3/videos"
    vid_params = {
        "part": "snippet,statistics",
        "id": video_id,
        "key": api_key,
    }
    resp_vid = session.get(vid_url, params=vid_params, timeout=20)
    if resp_vid.status_code != 200:
        err_msg = resp_vid.text[:300]
        raise RuntimeError(f"YouTube API v3 (videos) gagal (HTTP {resp_vid.status_code}): {err_msg}")

    vid_json = resp_vid.json()
    items = vid_json.get("items", [])
    if not items:
        raise RuntimeError(f"Video ID '{video_id}' tidak ditemukan melalui YouTube Data API v3.")

    v_item = items[0]
    snippet = v_item.get("snippet", {})
    stats = v_item.get("statistics", {})

    channel_id = snippet.get("channelId", "")
    channel_title = snippet.get("channelTitle", "YouTube Channel")
    video_title = snippet.get("title", f"Video {video_id}")
    published_at = parse_relative_time_to_iso(snippet.get("publishedAt", ""))[:10]

    video_meta = {
        "video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "video_title": video_title,
        "channel_name": channel_title,
        "channel_id": channel_id,
        "published_at": published_at,
        "views": int(stats.get("viewCount", 0)),
        "video_likes": int(stats.get("likeCount", 0)),
        "total_comments_reported": int(stats.get("commentCount", 0)),
        "description": (snippet.get("description") or "")[:500],
    }

    print(f" -> Judul Video : {video_title}")
    print(f" -> Channel     : {channel_title} ({channel_id})")
    print(f" -> Views       : {video_meta['views']:,} | Likes: {video_meta['video_likes']:,} | Komentar Terlapor: {video_meta['total_comments_reported']:,}")

    threads_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    order_param = "relevance" if sort_by == "top" else "time"
    next_page_token = None
    comments_collected = []
    page = 1

    while True:
        if max_comments and len(comments_collected) >= max_comments:
            print(f" -> [INFO] Batas maksimal komentar ({max_comments}) telah tercapai.")
            break

        params = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": 100,
            "order": order_param,
            "textFormat": "plainText",
            "key": api_key,
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        print(f" -> [API v3] Mengambil halaman {page} (terkumpul: {len(comments_collected)} komentar)...", end="\r", flush=True)
        resp = session.get(threads_url, params=params, timeout=20)
        if resp.status_code != 200:
            print(f"\n[WARNING] Gagal mengambil halaman {page} (HTTP {resp.status_code}): {resp.text[:200]}")
            break

        data = resp.json()
        thread_items = data.get("items", [])
        if not thread_items:
            break

        for thread in thread_items:
            if max_comments and len(comments_collected) >= max_comments:
                break

            top_Snippet_wrap = thread.get("snippet", {})
            top_comment = top_Snippet_wrap.get("topLevelComment", {})
            top_id = top_comment.get("id", "")
            c_snip = top_comment.get("snippet", {})

            author_chan_id = (c_snip.get("authorChannelId") or {}).get("value", "")
            author_name = c_snip.get("authorDisplayName", "Anonim")
            is_official = bool(channel_id and author_chan_id == channel_id)
            reply_total = int(top_Snippet_wrap.get("totalReplyCount", 0))

            comments_collected.append({
                "video_id": video_id,
                "video_title": video_title,
                "channel_name": channel_title,
                "channel_id": channel_id,
                "comment_id": top_id,
                "username": author_name,
                "author_channel_id": author_chan_id,
                "avatar": c_snip.get("authorProfileImageUrl", ""),
                "comment_text": (c_snip.get("textDisplay") or c_snip.get("textOriginal") or "").strip(),
                "like_count": int(c_snip.get("likeCount", 0)),
                "reply_count": reply_total,
                "is_hearted": False,
                "is_pinned": False,
                "is_official": is_official,
                "created_at": parse_relative_time_to_iso(c_snip.get("publishedAt", "")),
                "is_reply": False,
                "parent_comment_id": "",
            })

            if include_replies and reply_total > 0:
                inline_replies = (thread.get("replies") or {}).get("comments", [])
                fetched_reply_ids = set()

                for rep in inline_replies:
                    if max_comments and len(comments_collected) >= max_comments:
                        break
                    rep_id = rep.get("id", "")
                    fetched_reply_ids.add(rep_id)
                    r_snip = rep.get("snippet", {})
                    r_author_chan = (r_snip.get("authorChannelId") or {}).get("value", "")
                    r_author_name = r_snip.get("authorDisplayName", "Anonim")

                    comments_collected.append({
                        "video_id": video_id,
                        "video_title": video_title,
                        "channel_name": channel_title,
                        "channel_id": channel_id,
                        "comment_id": rep_id,
                        "username": r_author_name,
                        "author_channel_id": r_author_chan,
                        "avatar": r_snip.get("authorProfileImageUrl", ""),
                        "comment_text": (r_snip.get("textDisplay") or r_snip.get("textOriginal") or "").strip(),
                        "like_count": int(r_snip.get("likeCount", 0)),
                        "reply_count": 0,
                        "is_hearted": False,
                        "is_pinned": False,
                        "is_official": bool(channel_id and r_author_chan == channel_id),
                        "created_at": parse_relative_time_to_iso(r_snip.get("publishedAt", "")),
                        "is_reply": True,
                        "parent_comment_id": top_id,
                    })

                if reply_total > len(fetched_reply_ids) and (not max_comments or len(comments_collected) < max_comments):
                    extra_replies = _fetch_extra_replies_api_v3(
                        session, top_id, api_key, fetched_reply_ids, video_meta, max_comments - len(comments_collected) if max_comments else None
                    )
                    comments_collected.extend(extra_replies)

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
        page += 1
        time.sleep(0.2)

    print(f"\n[SUCCESS] YouTube Data API v3 berhasil mengumpulkan {len(comments_collected)} komentar.")
    return video_meta, comments_collected


def _fetch_extra_replies_api_v3(session, parent_id, api_key, existing_ids, video_meta, remaining_limit=None):
    """Mengambil seluruh balasan tambahan untuk sebuah parent comment via endpoint comments.list."""
    url = "https://www.googleapis.com/youtube/v3/comments"
    next_token = None
    extra = []
    channel_id = video_meta.get("channel_id", "")

    while True:
        if remaining_limit is not None and len(extra) >= remaining_limit:
            break
        params = {
            "part": "snippet",
            "parentId": parent_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "key": api_key,
        }
        if next_token:
            params["pageToken"] = next_token

        try:
            resp = session.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                break
            data = resp.json()
            for rep in data.get("items", []):
                if remaining_limit is not None and len(extra) >= remaining_limit:
                    break
                rep_id = rep.get("id", "")
                if rep_id in existing_ids:
                    continue
                existing_ids.add(rep_id)
                r_snip = rep.get("snippet", {})
                r_author_chan = (r_snip.get("authorChannelId") or {}).get("value", "")
                extra.append({
                    "video_id": video_meta["video_id"],
                    "video_title": video_meta["video_title"],
                    "channel_name": video_meta["channel_name"],
                    "channel_id": channel_id,
                    "comment_id": rep_id,
                    "username": r_snip.get("authorDisplayName", "Anonim"),
                    "author_channel_id": r_author_chan,
                    "avatar": r_snip.get("authorProfileImageUrl", ""),
                    "comment_text": (r_snip.get("textDisplay") or r_snip.get("textOriginal") or "").strip(),
                    "like_count": int(r_snip.get("likeCount", 0)),
                    "reply_count": 0,
                    "is_hearted": False,
                    "is_pinned": False,
                    "is_official": bool(channel_id and r_author_chan == channel_id),
                    "created_at": parse_relative_time_to_iso(r_snip.get("publishedAt", "")),
                    "is_reply": True,
                    "parent_comment_id": parent_id,
                })
            next_token = data.get("nextPageToken")
            if not next_token:
                break
        except Exception:
            break
    return extra


# ==============================================================================
# METODE 2: FALLBACK YOUTUBE-COMMENT-DOWNLOADER (TANPA API KEY)
# ==============================================================================

def scrape_via_comment_downloader(
    video_id: str,
    max_comments: int = None,
    sort_by: str = "top",
    include_replies: bool = True,
):
    """
    Mengambil komentar menggunakan pustaka `youtube-comment-downloader` tanpa API key,
    atau beralih ke built-in InnerTube client apabila pustaka belum terinstal.
    """
    session = requests.Session()
    video_meta = fetch_video_metadata_from_web(video_id, session)

    print(f" -> Judul Video : {video_meta['video_title']}")
    print(f" -> Channel     : {video_meta['channel_name']} ({video_meta['channel_id']})")
    print(f" -> Views       : {video_meta['views']:,} | Likes Video: {video_meta['video_likes']:,}")

    try:
        from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT
        has_ycd = True
    except ImportError:
        has_ycd = False

    if has_ycd:
        print("\n[DOWNLOADER] Menggunakan pustaka 'youtube-comment-downloader' (tanpa API key)...")
        downloader = YoutubeCommentDownloader()
        sort_flag = SORT_BY_POPULAR if sort_by == "top" else SORT_BY_RECENT
        generator = downloader.get_comments_from_url(
            f"https://www.youtube.com/watch?v={video_id}",
            sort_by=sort_flag,
        )

        comments_collected = []
        reply_counts_by_parent = {}
        ref_now = datetime.now()
        channel_id = video_meta.get("channel_id", "")
        channel_name_clean = (video_meta.get("channel_name") or "").strip().lower()

        for item in generator:
            cid = str(item.get("cid", ""))
            is_reply = bool(item.get("reply", False) or ("." in cid))
            if is_reply and not include_replies:
                continue

            parent_id = cid.split(".")[0] if is_reply and "." in cid else ""
            if is_reply and parent_id:
                reply_counts_by_parent[parent_id] = reply_counts_by_parent.get(parent_id, 0) + 1

            author_name = str(item.get("author", "Anonim")).strip()
            author_chan = str(item.get("channel", "")).strip()
            is_official = bool(
                (channel_id and author_chan == channel_id)
                or (channel_name_clean and author_name.lstrip("@").lower() == channel_name_clean.lstrip("@"))
            )

            time_parsed = item.get("time_parsed")
            if time_parsed:
                try:
                    created_str = datetime.fromtimestamp(float(time_parsed)).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    created_str = parse_relative_time_to_iso(item.get("time", ""), ref_now)
            else:
                created_str = parse_relative_time_to_iso(item.get("time", ""), ref_now)

            comments_collected.append({
                "video_id": video_id,
                "video_title": video_meta["video_title"],
                "channel_name": video_meta["channel_name"],
                "channel_id": channel_id,
                "comment_id": cid,
                "username": author_name,
                "author_channel_id": author_chan,
                "avatar": item.get("photo", ""),
                "comment_text": str(item.get("text", "")).strip(),
                "like_count": parse_compact_number(item.get("votes", 0)),
                "reply_count": 0,
                "is_hearted": bool(item.get("heart", False)),
                "is_pinned": False,
                "is_official": is_official,
                "created_at": created_str,
                "is_reply": is_reply,
                "parent_comment_id": parent_id,
            })

            if len(comments_collected) % 25 == 0:
                print(f" -> Terkumpul {len(comments_collected)} komentar...", end="\r", flush=True)

            if max_comments and len(comments_collected) >= max_comments:
                print(f"\n -> [INFO] Batas maksimal komentar ({max_comments}) tercapai.")
                break

        for c in comments_collected:
            if not c["is_reply"] and c["comment_id"] in reply_counts_by_parent:
                c["reply_count"] = max(c["reply_count"], reply_counts_by_parent[c["comment_id"]])

        print(f"\n[SUCCESS] Berhasil mengunduh {len(comments_collected)} komentar via youtube-comment-downloader.")
        return video_meta, comments_collected

    print("\n[INNERTUBE] Pustaka 'youtube-comment-downloader' tidak ditemukan. Menggunakan built-in YouTube InnerTube Web Client...")
    return scrape_via_innertube_web(video_id, video_meta, session, max_comments, sort_by, include_replies)


# ==============================================================================
# METODE 3: BUILT-IN YOUTUBE INNERTUBE WEB CLIENT (ZERO EXTRA DEPENDENCY)
# ==============================================================================

def _find_json_values(obj, target_key):
    """Mencari semua nilai dari key tertentu secara rekursif di dalam struktur dict/list JSON."""
    results = []
    stack = [obj]
    while stack:
        curr = stack.pop()
        if isinstance(curr, dict):
            for k, v in curr.items():
                if k == target_key:
                    results.append(v)
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(curr, list):
            for item in curr:
                if isinstance(item, (dict, list)):
                    stack.append(item)
    return results


def scrape_via_innertube_web(
    video_id: str,
    video_meta: dict,
    session: requests.Session,
    max_comments: int = None,
    sort_by: str = "top",
    include_replies: bool = True,
):
    """
    Mengambil komentar menggunakan endpoint internal YouTube InnerTube (/youtubei/v1/next)
    hanya dengan modul `requests` standar.
    Dilengkapi deduplikasi token (`visited_tokens`) dan pemisahan antrean halaman utama
    vs balasan agar tidak terjadi infinite loop maupun request kosong.
    """
    watch_url = f"https://www.youtube.com/watch?v={video_id}&hl=id"
    resp = session.get(watch_url, headers=DEFAULT_HEADERS, timeout=20)
    html = resp.text

    m_key = re.search(r'"INNERTUBE_API_KEY"\s*:\s*"([^"]+)"', html)
    m_ctx = re.search(r'"INNERTUBE_CONTEXT"\s*:\s*(\{.+?\})\s*,\s*"INNERTUBE_', html)
    if not m_key:
        raise RuntimeError("Gagal menemukan INNERTUBE_API_KEY dari halaman YouTube.")

    api_key = m_key.group(1)
    context = {
        "client": {
            "hl": "id",
            "gl": "ID",
            "clientName": "WEB",
            "clientVersion": "2.20250101.00.00",
        }
    }
    if m_ctx:
        try:
            context = json.loads(m_ctx.group(1))
        except Exception:
            pass

    m_init = re.search(r"var ytInitialData\s*=\s*(\{.+?\});\s*</script>", html, re.DOTALL)
    if not m_init:
        m_init = re.search(r"ytInitialData\s*=\s*(\{.+?\});", html, re.DOTALL)
    if not m_init:
        raise RuntimeError("Gagal menemukan ytInitialData di halaman YouTube.")

    init_data = json.loads(m_init.group(1))

    visited_tokens = set()
    page_continuations = []
    reply_continuations = []

    def _enqueue_page_token(tok):
        if isinstance(tok, str) and len(tok) > 15 and tok not in visited_tokens:
            visited_tokens.add(tok)
            page_continuations.append(tok)

    def _enqueue_reply_token(tok):
        if isinstance(tok, str) and len(tok) > 15 and tok not in visited_tokens:
            visited_tokens.add(tok)
            reply_continuations.append(tok)

    # Cari continuation token awal untuk bagian komentar
    for item_sec in _find_json_values(init_data, "itemSectionRenderer"):
        if item_sec.get("sectionIdentifier") == "comment-item-section" or "comments" in str(item_sec.get("targetId", "")):
            for cir in _find_json_values(item_sec, "continuationItemRenderer"):
                for tok in _find_json_values(cir, "token"):
                    _enqueue_page_token(tok)

    if not page_continuations:
        for cir in _find_json_values(init_data, "continuationItemRenderer"):
            for tok in _find_json_values(cir, "token"):
                _enqueue_page_token(tok)
                if page_continuations:
                    break
            if page_continuations:
                break

    endpoint = f"https://www.youtube.com/youtubei/v1/next?key={api_key}"
    comments_collected = []
    seen_ids = set()
    ref_now = datetime.now()
    channel_id = video_meta.get("channel_id", "")
    sort_selected = False
    empty_batches = 0

    while page_continuations or reply_continuations:
        if max_comments and len(comments_collected) >= max_comments:
            print(f"\n -> [INFO] Batas maksimal komentar ({max_comments}) telah tercapai.")
            break

        # Prioritaskan halaman komentar utama (20 komentar/request) sebelum mengambil sub-thread balasan
        if page_continuations:
            token = page_continuations.pop(0)
            is_page_req = True
        else:
            token = reply_continuations.pop(0)
            is_page_req = False

        payload = {"context": context, "continuation": token}
        try:
            r = session.post(endpoint, json=payload, headers=DEFAULT_HEADERS, timeout=20)
            if r.status_code != 200:
                continue
            data = r.json()
        except Exception:
            continue

        # Pilih urutan sort_by pada request pertama jika tersedia subMenuItems
        if not sort_selected:
            menu_items = _find_json_values(data, "sortFilterSubMenuRenderer")
            if menu_items:
                sub_items = menu_items[0].get("subMenuItems", [])
                # Tandai SEMUA token di menu sort sebagai visited agar tidak pernah tereksekusi ulang
                sort_tokens = []
                for si in sub_items:
                    st = (
                        si.get("serviceEndpoint", {})
                        .get("continuationCommand", {})
                        .get("token")
                    )
                    if st:
                        visited_tokens.add(st)
                        sort_tokens.append(st)

                target_idx = 0 if sort_by == "top" else (1 if len(sort_tokens) > 1 else 0)
                if len(sort_tokens) > target_idx:
                    sort_selected = True
                    page_continuations.insert(0, sort_tokens[target_idx])
                    continue
            sort_selected = True

        prev_count = len(comments_collected)

        # Ekstrak commentEntityPayload (format baru YouTube) & commentRenderer (format lama)
        for ep in _find_json_values(data, "commentEntityPayload"):
            if max_comments and len(comments_collected) >= max_comments:
                break
            props = ep.get("properties", {})
            cid = str(props.get("commentId", ""))
            if not cid or cid in seen_ids:
                continue
            seen_ids.add(cid)

            author = ep.get("author", {})
            toolbar = ep.get("toolbar", {})
            text_content = (props.get("content") or {}).get("content", "")
            is_reply = "." in cid or int(props.get("replyLevel", 0)) > 0
            if is_reply and not include_replies:
                continue

            author_chan = str(author.get("channelId", ""))
            is_official = bool(author.get("isCreator", False) or (channel_id and author_chan == channel_id))

            comments_collected.append({
                "video_id": video_id,
                "video_title": video_meta["video_title"],
                "channel_name": video_meta["channel_name"],
                "channel_id": channel_id,
                "comment_id": cid,
                "username": str(author.get("displayName", "Anonim")),
                "author_channel_id": author_chan,
                "avatar": str(author.get("avatarThumbnailUrl", "")),
                "comment_text": str(text_content).strip(),
                "like_count": parse_compact_number(toolbar.get("likeCountNotliked") or toolbar.get("likeCountLiked") or 0),
                "reply_count": parse_compact_number(toolbar.get("replyCount", 0)),
                "is_hearted": bool(toolbar.get("heartActiveTooltip") or ep.get("hearted")),
                "is_pinned": False,
                "is_official": is_official,
                "created_at": parse_relative_time_to_iso(props.get("publishedTime", ""), ref_now),
                "is_reply": is_reply,
                "parent_comment_id": cid.split(".")[0] if is_reply and "." in cid else "",
            })

        for cr in _find_json_values(data, "commentRenderer"):
            if max_comments and len(comments_collected) >= max_comments:
                break
            cid = str(cr.get("commentId", ""))
            if not cid or cid in seen_ids:
                continue
            seen_ids.add(cid)

            is_reply = "." in cid
            if is_reply and not include_replies:
                continue

            runs = (cr.get("contentText") or {}).get("runs", [])
            text_content = "".join(r.get("text", "") for r in runs)
            author_name = ((cr.get("authorText") or {}).get("simpleText") or "Anonim").strip()
            author_chan = (
                ((cr.get("authorEndpoint") or {}).get("browseEndpoint") or {}).get("browseId", "")
            )
            pub_runs = (cr.get("publishedTimeText") or {}).get("runs", [])
            pub_str = pub_runs[0].get("text", "") if pub_runs else ""
            votes_str = (cr.get("voteCount") or {}).get("simpleText", "0")
            thumbs = ((cr.get("authorThumbnail") or {}).get("thumbnails") or [{}])
            avatar_url = thumbs[-1].get("url", "") if thumbs else ""

            comments_collected.append({
                "video_id": video_id,
                "video_title": video_meta["video_title"],
                "channel_name": video_meta["channel_name"],
                "channel_id": channel_id,
                "comment_id": cid,
                "username": author_name,
                "author_channel_id": author_chan,
                "avatar": avatar_url,
                "comment_text": text_content.strip(),
                "like_count": parse_compact_number(votes_str),
                "reply_count": int(cr.get("replyCount", 0)),
                "is_hearted": bool(cr.get("actionButtons", {}).get("commentActionButtonsRenderer", {}).get("creatorHeart")),
                "is_pinned": bool(cr.get("pinnedCommentBadge")),
                "is_official": bool(cr.get("authorIsChannelOwner", False) or (channel_id and author_chan == channel_id)),
                "created_at": parse_relative_time_to_iso(pub_str, ref_now),
                "is_reply": is_reply,
                "parent_comment_id": cid.split(".")[0] if is_reply and "." in cid else "",
            })

        added_now = len(comments_collected) - prev_count
        if added_now == 0:
            empty_batches += 1
            if empty_batches >= 5 and not page_continuations:
                break
        else:
            empty_batches = 0

        # 1. Kumpulkan token khusus balasan (replies) dari commentRepliesRenderer
        reply_token_set = set()
        if include_replies:
            for rep_rend in _find_json_values(data, "commentRepliesRenderer"):
                for cir in _find_json_values(rep_rend, "continuationItemRenderer"):
                    for tok in _find_json_values(cir, "token"):
                        reply_token_set.add(tok)
                        _enqueue_reply_token(tok)
        else:
            for rep_rend in _find_json_values(data, "commentRepliesRenderer"):
                for tok in _find_json_values(rep_rend, "token"):
                    if isinstance(tok, str):
                        visited_tokens.add(tok)

        # 2. Kumpulkan token halaman utama berikutnya dari continuationItemRenderer
        for cir in _find_json_values(data, "continuationItemRenderer"):
            for tok in _find_json_values(cir, "token"):
                if tok not in reply_token_set:
                    if is_page_req:
                        _enqueue_page_token(tok)
                    elif include_replies:
                        _enqueue_reply_token(tok)

        print(f" -> [INNERTUBE] Terkumpul {len(comments_collected)} komentar...", end="\r", flush=True)
        time.sleep(0.15)

    if max_comments and len(comments_collected) < max_comments:
        print(
            f"\n -> [INFO] Seluruh komentar yang tersedia pada video ini telah habis terambil "
            f"({len(comments_collected)} komentar dari batas {max_comments})."
        )
    print(f"[SUCCESS] Berhasil mengumpulkan {len(comments_collected)} komentar via InnerTube Web Client.")
    return video_meta, comments_collected


# ==============================================================================
# PENYIMPANAN CSV & ORKESTRATOR UTAMA
# ==============================================================================

def save_youtube_outputs(video_meta: dict, comments: list, output_dir: str):
    """Menyimpan metadata video dan daftar komentar ke dalam direktori scrap/."""
    scrap_dir = os.path.join(output_dir, "scrap")
    os.makedirs(scrap_dir, exist_ok=True)
    video_id = video_meta.get("video_id", "unknown")

    meta_csv_path = os.path.join(scrap_dir, f"youtube_video_meta_{video_id}.csv")
    meta_fields = [
        "video_id", "video_url", "video_title", "channel_name", "channel_id",
        "published_at", "views", "video_likes", "total_comments_reported", "description"
    ]
    with open(meta_csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=meta_fields)
        writer.writeheader()
        writer.writerow({k: video_meta.get(k, "") for k in meta_fields})

    comments_csv_path = os.path.join(scrap_dir, f"youtube_comments_video_{video_id}.csv")
    comment_fields = [
        "video_id", "video_title", "channel_name", "channel_id",
        "comment_id", "username", "author_channel_id", "avatar",
        "comment_text", "like_count", "reply_count",
        "is_hearted", "is_pinned", "is_official",
        "created_at", "is_reply", "parent_comment_id"
    ]
    with open(comments_csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=comment_fields)
        writer.writeheader()
        for c in comments:
            writer.writerow({k: c.get(k, "") for k in comment_fields})

    print("\n" + "=" * 65)
    print("[SUCCESS] SCRAPING KOMENTAR YOUTUBE SELESAI!")
    print(f" -> File Komentar : {comments_csv_path}")
    print(f" -> File Metadata : {meta_csv_path}")
    print(f" -> Total Komentar: {len(comments):,} baris")
    print("=" * 65)
    return comments_csv_path, meta_csv_path


def run_scraper(config_override=None):
    """Orkestrator utama Langkah 0 untuk scraping komentar dari satu video YouTube."""
    print("=" * 65)
    print("   LANGKAH 0: YOUTUBE VIDEO COMMENTS SCRAPER (API v3 + FALLBACK)")
    print("=" * 65)

    cfg = config_override or {}
    raw_url = cfg.get("YOUTUBE_VIDEO_URL", AppConfig.YOUTUBE_VIDEO_URL)
    video_id = extract_youtube_video_id(raw_url)

    if not video_id and config_override is None:
        user_input = input("\nMasukkan URL atau ID Video YouTube: ").strip()
        video_id = extract_youtube_video_id(user_input)

    if not video_id:
        raise PipelineError("YOUTUBE_VIDEO_URL tidak valid atau belum diatur di file .env!")

    api_key = cfg.get("YOUTUBE_API_KEY", AppConfig.YOUTUBE_API_KEY)
    max_comments = cfg.get("YOUTUBE_LIMIT_COMMENTS", AppConfig.YOUTUBE_LIMIT_COMMENTS)
    sort_by = cfg.get("YOUTUBE_SORT", AppConfig.YOUTUBE_SORT)
    include_replies = cfg.get("YOUTUBE_INCLUDE_REPLIES", AppConfig.YOUTUBE_INCLUDE_REPLIES)
    output_dir = cfg.get("OUTPUT_DIR", AppConfig.OUTPUT_YOUTUBE_DIR)

    print(f"[INFO] Target Video ID    : {video_id}")
    print(f"[INFO] URL Video          : https://www.youtube.com/watch?v={video_id}")
    print(f"[INFO] Batas Komentar     : {max_comments if max_comments else 'Semua Komentar'}")
    print(f"[INFO] Urutan Sortir      : {'Terpopuler (Top)' if sort_by == 'top' else 'Terbaru (New)'}")
    print(f"[INFO] Sertakan Balasan   : {include_replies}")

    video_meta = None
    comments = []

    if api_key:
        try:
            video_meta, comments = scrape_via_youtube_api_v3(
                video_id=video_id,
                api_key=api_key,
                max_comments=max_comments,
                sort_by=sort_by,
                include_replies=include_replies,
            )
        except Exception as e:
            print(f"\n[WARNING] YouTube Data API v3 gagal ({e}).")
            print("[INFO] Beralih otomatis ke metode fallback tanpa API key...")

    if not comments:
        video_meta, comments = scrape_via_comment_downloader(
            video_id=video_id,
            max_comments=max_comments,
            sort_by=sort_by,
            include_replies=include_replies,
        )

    if not comments:
        print("\n[WARNING] Tidak ada komentar yang berhasil diambil dari video ini.")
        return None

    return save_youtube_outputs(video_meta, comments, output_dir)


if __name__ == "__main__":
    run_scraper()
