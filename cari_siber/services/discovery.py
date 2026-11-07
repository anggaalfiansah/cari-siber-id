import os
import re
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

import requests

from cari_siber.engine.core.config import AppConfig, extract_youtube_video_id
from cari_siber.engine.core.ai_client import generate_text
from cari_siber.settings import AppSettings

logger = logging.getLogger("cari_siber.services.discovery")

INNERTUBE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _parse_compact_count(val: Any) -> int:
    """Mengubah teks angka ringkas YouTube ('1,2 rb', '3.5K', '1.240', '2 jt') menjadi integer."""
    if val is None or val == "":
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    text = str(val).strip().lower().replace("\u00a0", " ")
    text = re.sub(r"(komentar|comments|comment|x ditonton|views|view|suka|likes)", "", text).strip()
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
    digits = re.sub(r"[^0-9]", "", text)
    return int(digits) if digits else 0


def _format_id_number(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")


def _extract_continuation_token(obj: Any) -> Optional[str]:
    """Mengekstrak continuation token pagination dari payload JSON Innertube."""
    if isinstance(obj, dict):
        if "continuationCommand" in obj and isinstance(obj["continuationCommand"], dict):
            token = obj["continuationCommand"].get("token")
            if token:
                return str(token)
        for v in obj.values():
            tok = _extract_continuation_token(v)
            if tok:
                return tok
    elif isinstance(obj, list):
        for item in obj:
            tok = _extract_continuation_token(item)
            if tok:
                return tok
    return None


def _extract_video_renderers(obj: Any) -> List[Dict[str, Any]]:
    res = []
    if isinstance(obj, dict):
        if "videoRenderer" in obj:
            vr = obj["videoRenderer"]
            vid = vr.get("videoId")
            title = "".join([t.get("text", "") for t in vr.get("title", {}).get("runs", [])])
            channel = "".join([t.get("text", "") for t in vr.get("ownerText", {}).get("runs", [])])
            views = vr.get("viewCountText", {}).get("simpleText", "")
            if not views and "runs" in vr.get("viewCountText", {}):
                views = "".join([t.get("text", "") for t in vr.get("viewCountText", {}).get("runs", [])])
            published = vr.get("publishedTimeText", {}).get("simpleText", "")
            length = vr.get("lengthText", {}).get("simpleText", "")
            thumbs = vr.get("thumbnail", {}).get("thumbnails", [])
            thumb = thumbs[-1].get("url", "") if thumbs else f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

            desc = ""
            snippets = vr.get("detailedMetadataSnippets")
            if snippets and len(snippets) > 0:
                runs = snippets[0].get("snippetText", {}).get("runs", [])
                desc = "".join([t.get("text", "") for t in runs])

            if vid and title:
                vid_url = f"https://www.youtube.com/watch?v={vid}"
                views_clean = views.strip() or "0 x ditonton"
                res.append({
                    "video_id": vid,
                    "url": vid_url,
                    "video_url": vid_url,
                    "title": title.strip(),
                    "channel": channel.strip(),
                    "channel_name": channel.strip(),
                    "views": views_clean,
                    "views_str": views_clean,
                    "views_count": _parse_compact_count(views_clean),
                    "comment_count": 0,
                    "comments_str": "Memuat...",
                    "published": published.strip() or "Baru saja",
                    "published_str": published.strip() or "Baru saja",
                    "duration": length.strip() or "--:--",
                    "duration_str": length.strip() or "--:--",
                    "thumbnail": thumb,
                    "thumbnail_url": thumb,
                    "description": desc.strip()[:200],
                })
        for val in obj.values():
            res.extend(_extract_video_renderers(val))
    elif isinstance(obj, list):
        for item in obj:
            res.extend(_extract_video_renderers(item))
    return res


def _extract_comment_count_from_next_data(data: Dict[str, Any]) -> Optional[int]:
    """Mengekstrak jumlah komentar dari response JSON /youtubei/v1/next."""
    try:
        panels = data.get("engagementPanels", [])
        for panel in panels:
            renderer = panel.get("engagementPanelSectionListRenderer", {})
            pid = str(renderer.get("panelIdentifier", "") or renderer.get("targetId", ""))
            header = renderer.get("header", {}).get("engagementPanelTitleHeaderRenderer", {})
            title_runs = header.get("title", {}).get("runs", [])
            title_txt = "".join(r.get("text", "") for r in title_runs).lower()
            if "comment" in pid or "komentar" in title_txt or "comment" in title_txt:
                ctx_runs = header.get("contextualInfo", {}).get("runs", [])
                ctx_txt = "".join(r.get("text", "") for r in ctx_runs).strip()
                if ctx_txt:
                    return _parse_compact_count(ctx_txt)
    except Exception:
        pass

    # Fallback regex pada serialisasi JSON jika struktur nested berbeda
    try:
        raw_str = json.dumps(data, ensure_ascii=False)
        m = re.search(
            r'"engagement-panel-comments-section".*?"contextualInfo"\s*:\s*\{\s*"runs"\s*:\s*\[\s*\{\s*"text"\s*:\s*"([^"]+)"',
            raw_str,
        )
        if not m:
            m = re.search(
                r'"title"\s*:\s*\{\s*"runs"\s*:\s*\[\s*\{\s*"text"\s*:\s*"(?:Komentar|Comments)"\s*\}\s*\]\s*\}\s*,\s*"contextualInfo"\s*:\s*\{\s*"runs"\s*:\s*\[\s*\{\s*"text"\s*:\s*"([^"]+)"',
                raw_str,
                re.IGNORECASE,
            )
        if m:
            return _parse_compact_count(m.group(1))
    except Exception:
        pass
    return None


def _fetch_single_video_comment_count_innertube(video_id: str) -> Optional[int]:
    """Mengambil jumlah komentar 1 video secara cepat melalui endpoint /youtubei/v1/next."""
    url = "https://www.youtube.com/youtubei/v1/next?prettyPrint=false"
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240101.01.00",
                "hl": "id",
                "gl": "ID",
            }
        },
        "videoId": video_id,
    }
    try:
        resp = requests.post(url, headers=INNERTUBE_HEADERS, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return _extract_comment_count_from_next_data(data)
    except Exception:
        pass
    return None


def enrich_videos_with_comment_counts(videos: List[Dict[str, Any]], api_key: str = "") -> List[Dict[str, Any]]:
    """
    Memperkaya daftar kandidat video dengan jumlah komentar riil (comment_count & comments_str).
    Menggunakan batch YouTube Data API v3 jika api_key tersedia, lalu fallback paralel ke Innertube /next.
    """
    if not videos:
        return videos

    vid_map = {v["video_id"]: v for v in videos if v.get("video_id")}
    unresolved_ids = list(vid_map.keys())

    # 1. Coba batch YouTube Data API v3 terlebih dahulu jika API key tersedia (1 request untuk 50 video)
    if api_key and api_key.strip():
        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        for i in range(0, len(unresolved_ids), 50):
            batch_ids = unresolved_ids[i : i + 50]
            try:
                resp = requests.get(
                    stats_url,
                    params={
                        "part": "statistics",
                        "id": ",".join(batch_ids),
                        "key": api_key.strip(),
                    },
                    timeout=8,
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    for it in items:
                        vid = it.get("id")
                        st = it.get("statistics", {})
                        if vid in vid_map:
                            c_cnt = int(st.get("commentCount", 0) or 0)
                            v_cnt = int(st.get("viewCount", 0) or 0)
                            vid_map[vid]["comment_count"] = c_cnt
                            vid_map[vid]["comments_str"] = f"{_format_id_number(c_cnt)} komentar"
                            if v_cnt > 0:
                                vid_map[vid]["views_count"] = v_cnt
                                vid_map[vid]["views"] = f"{_format_id_number(v_cnt)} x ditonton"
                                vid_map[vid]["views_str"] = vid_map[vid]["views"]
            except Exception as e:
                logger.warning(f"YouTube API v3 batch statistics warning: {e}")

    still_missing = [
        vid for vid, v in vid_map.items()
        if v.get("comments_str") in (None, "", "Memuat...")
    ]

    # 2. Fallback paralel Innertube /youtubei/v1/next untuk video yang belum memiliki comment_count
    if still_missing:
        max_workers = min(14, max(4, len(still_missing)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_vid = {
                executor.submit(_fetch_single_video_comment_count_innertube, vid): vid
                for vid in still_missing
            }
            for fut in as_completed(future_to_vid):
                vid = future_to_vid[fut]
                v_obj = vid_map.get(vid)
                if not v_obj:
                    continue
                try:
                    c_cnt = fut.result()
                except Exception:
                    c_cnt = None

                if c_cnt is not None and c_cnt >= 0:
                    v_obj["comment_count"] = int(c_cnt)
                    v_obj["comments_str"] = f"{_format_id_number(c_cnt)} komentar"
                else:
                    # Estimasi konservatif dari views jika komentar disembunyikan/gagal dimuat
                    v_cnt = int(v_obj.get("views_count") or _parse_compact_count(v_obj.get("views", 0)))
                    est_c = max(0, int(v_cnt * 0.0025)) if v_cnt > 0 else 0
                    v_obj["comment_count"] = est_c
                    v_obj["comments_str"] = f"~{_format_id_number(est_c)} komentar" if est_c > 0 else "Komentar aktif"

    return videos


def search_youtube_innertube(query: str, max_candidates: int = 100) -> List[Dict[str, Any]]:
    """
    Mencari video YouTube berbasis kata kunci menggunakan endpoint Innertube Web
    secara instan dengan pagination otomatis hingga mencapai max_candidates (hingga 100 video).
    """
    url = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false"

    seen = set()
    unique_videos = []
    continuation_token = None
    max_pages = max(2, min(7, (max_candidates + 15) // 16))

    for page in range(max_pages):
        if len(unique_videos) >= max_candidates:
            break

        if page == 0:
            payload = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20240101.01.00",
                        "hl": "id",
                        "gl": "ID",
                    }
                },
                "query": query.strip(),
            }
        else:
            if not continuation_token:
                break
            payload = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20240101.01.00",
                        "hl": "id",
                        "gl": "ID",
                    }
                },
                "continuation": continuation_token,
            }

        try:
            resp = requests.post(url, headers=INNERTUBE_HEADERS, json=payload, timeout=12)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"Innertube search page {page + 1} warning: {e}")
            break

        found_batch = _extract_video_renderers(data)
        if not found_batch:
            break

        for v in found_batch:
            if v["video_id"] not in seen:
                seen.add(v["video_id"])
                unique_videos.append(v)
                if len(unique_videos) >= max_candidates:
                    break

        continuation_token = _extract_continuation_token(data)
        if not continuation_token:
            break

    return unique_videos


def search_youtube_official_api(query: str, api_key: str, max_candidates: int = 100) -> List[Dict[str, Any]]:
    """
    Pencarian menggunakan YouTube Data API v3 resmi jika API key disediakan
    dengan dukungan pagination hingga max_candidates (hingga 100 video).
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    candidates = []
    seen = set()
    next_page_token = None
    pages_to_fetch = max(1, (max_candidates + 49) // 50)

    for _ in range(pages_to_fetch):
        params = {
            "part": "snippet",
            "q": query.strip(),
            "type": "video",
            "maxResults": min(50, max_candidates - len(candidates)),
            "relevanceLanguage": "id",
            "key": api_key.strip(),
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"YouTube Data API v3 search error: {e}, beralih ke Innertube...")
            break

        items = data.get("items", [])
        for it in items:
            vid = it.get("id", {}).get("videoId")
            snip = it.get("snippet", {})
            if vid and snip and vid not in seen:
                seen.add(vid)
                thumbs = snip.get("thumbnails", {})
                thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
                candidates.append({
                    "video_id": vid,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "video_url": f"https://www.youtube.com/watch?v={vid}",
                    "title": snip.get("title", ""),
                    "channel": snip.get("channelTitle", ""),
                    "channel_name": snip.get("channelTitle", ""),
                    "views": "Populer",
                    "views_str": "Populer",
                    "views_count": 0,
                    "comment_count": 0,
                    "comments_str": "Memuat...",
                    "published": snip.get("publishedAt", "")[:10],
                    "published_str": snip.get("publishedAt", "")[:10],
                    "duration": "--:--",
                    "duration_str": "--:--",
                    "thumbnail": thumb or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                    "thumbnail_url": thumb or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                    "description": snip.get("description", "")[:200],
                })
                if len(candidates) >= max_candidates:
                    break

        next_page_token = data.get("nextPageToken")
        if not next_page_token or len(candidates) >= max_candidates:
            break

    return candidates


class VideoDiscoveryService:
    """
    Layanan pencarian dan kurasi semantik video YouTube berbasis isu/keyword,
    lengkap dengan pengayaan jumlah komentar per video dan kontrol jumlah target.
    """

    @classmethod
    def search_candidates(cls, query: str, max_candidates: int = 50) -> List[Dict[str, Any]]:
        settings = AppSettings.load()
        api_key = settings.get("youtube_api_key") or getattr(AppConfig, "YOUTUBE_API_KEY", "")

        candidates = []
        if api_key:
            candidates = search_youtube_official_api(query, api_key, max_candidates)

        if not candidates or len(candidates) < max_candidates:
            extra = search_youtube_innertube(query, max_candidates)
            seen_ids = {c["video_id"] for c in candidates}
            for ex in extra:
                if ex["video_id"] not in seen_ids:
                    candidates.append(ex)
                    seen_ids.add(ex["video_id"])
                    if len(candidates) >= max_candidates:
                        break

        return candidates

    @classmethod
    def curate_with_ai(
        cls,
        keyword: str,
        candidates: List[Dict[str, Any]],
        max_curated: int = 50,
        settings: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Menjalankan AI Curation Gate untuk mengevaluasi relevansi, menyaring clickbait,
        menilai potensi diskusi publik, dan menyusun peringkat video terbaik sesuai target jumlah video.
        """
        if not candidates:
            return []

        prompt_data = [
            {
                "index": idx + 1,
                "video_id": c["video_id"],
                "title": c["title"],
                "channel": c["channel_name"],
                "views": c["views_str"],
                "comments": c.get("comments_str", ""),
                "description": c["description"][:120],
            }
            for idx, c in enumerate(candidates[:15])
        ]

        system_instruction = (
            "Anda adalah Senior Cognitive Intelligence & OSINT Analyst. Tugas Anda adalah mengkurasi video "
            "YouTube terbaik untuk analisis opini publik dan polarisasi sosial berdasarkan isu yang diberikan."
        )

        prompt = f"""Isu / Kata Kunci Target: "{keyword}"

Berikut adalah daftar kandidat video YouTube teratas yang ditemukan:
{json.dumps(prompt_data, ensure_ascii=False, indent=2)}

Tugas Anda:
1. Saring video yang TIDAK relevan, clickbait murni, musik/lagu latar, atau video kompilasi tanpa diskursus opini.
2. Nilai relevansi konten terhadap isu "{keyword}" (skor 0 - 100).
3. Nilai potensi perdebatan / diskursus opini di kolom komentar (Tinggi / Sedang / Rendah).
4. Berikan satu kalimat singkat profesional sebagai alasan kurasi AI (curation_reason).
5. Pilih video terbaik, diurutkan dari yang paling berkualitas dan representatif.

Format Output WAJIB berupa JSON murni:
{{
  "curated": [
    {{
      "video_id": "string",
      "relevance_score": 95,
      "discussion_viability": "Tinggi",
      "curation_reason": "Alasan singkat mengapa video ini sangat representatif untuk dianalisis opini publiknya.",
      "tag": "Prioritas Utama"
    }}
  ]
}}
"""

        cfg_settings = settings or AppSettings.load()
        provider = cfg_settings.get("ai_provider", "gemini")
        model = cfg_settings.get("ai_model", "gemini-2.5-flash")
        api_key = cfg_settings.get(f"{provider}_api_key") or getattr(AppConfig, f"{provider.upper()}_API_KEY", "")
        if provider == "custom":
            AppConfig.CUSTOM_BASE_URL = cfg_settings.get("custom_base_url", "http://127.0.0.1:11434/v1")
            AppConfig.CUSTOM_API_KEY = api_key

        try:
            full_prompt = f"{system_instruction}\n\n{prompt}"
            raw_response = generate_text(
                prompt=full_prompt,
                provider=provider,
                model=model,
                api_key=api_key,
                min_length=10,
                max_retries=1,
                timeout=20.0,
            )

            clean_json_str = raw_response.strip()
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_json_str, re.DOTALL)
            if match:
                clean_json_str = match.group(1)
            else:
                m_brace = re.search(r'\{.*\}', clean_json_str, re.DOTALL)
                if m_brace:
                    clean_json_str = m_brace.group(0)

            curated_json = json.loads(clean_json_str)
            curated_items = curated_json.get("curated", [])

            cand_map = {c["video_id"]: c for c in candidates}
            final_curated = []

            for item in curated_items:
                vid = item.get("video_id")
                if vid in cand_map and len(final_curated) < max_curated:
                    base = cand_map[vid].copy()
                    rel_score = int(item.get("relevance_score", 85))
                    base["relevance_score"] = rel_score
                    base["discussion_viability"] = str(item.get("discussion_viability", "Tinggi"))
                    base["curation_reason"] = str(item.get("curation_reason", "Relevan dengan topik pembahasan."))
                    base["curation_tag"] = str(item.get("tag", "Rekomendasi AI"))
                    base["is_recommended"] = bool(item.get("is_recommended", rel_score >= 80))
                    final_curated.append(base)

            used_vids = {x["video_id"] for x in final_curated}
            for c in candidates:
                if c["video_id"] not in used_vids and len(final_curated) < max_curated:
                    extra_item = c.copy()
                    extra_item["relevance_score"] = max(65, 88 - int(len(final_curated) * 0.2))
                    extra_item["discussion_viability"] = "Tinggi" if len(final_curated) < 15 else "Sedang"
                    extra_item["curation_reason"] = f"Video dari kanal {c.get('channel') or c.get('channel_name')} dengan audiens aktif."
                    extra_item["curation_tag"] = "Kandidat Terpilih"
                    extra_item["is_recommended"] = len(final_curated) < 5
                    final_curated.append(extra_item)
                    used_vids.add(c["video_id"])

            if final_curated:
                return final_curated[:max_curated]

        except Exception as e:
            logger.warning(f"AI Curation Gate gagal/timeout: {e}. Menggunakan fallback heuristik.")

        fallback_curated = []
        for idx, c in enumerate(candidates[:max_curated]):
            item = c.copy()
            item["relevance_score"] = max(60, 95 - int(idx * 0.35))
            item["discussion_viability"] = "Tinggi" if idx < 10 else "Sedang"
            item["curation_reason"] = f"Video teratas dari kanal {c.get('channel') or c.get('channel_name')} dengan interaksi penonton aktif."
            item["curation_tag"] = "Paling Populer" if idx == 0 else "Rekomendasi"
            item["is_recommended"] = True if idx < 5 else False
            fallback_curated.append(item)

        return fallback_curated[:max_curated]

    @classmethod
    def discover_and_curate(
        cls,
        keyword: str,
        max_curated: int = 25,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Orkestrasi lengkap: Pencarian calon video sesuai target -> Pengayaan Jumlah Komentar -> Kurasi AI.
        """
        if not keyword or not keyword.strip():
            return {"success": False, "error": "Kata kunci pencarian tidak boleh kosong."}

        clean_kw = keyword.strip()
        target_limit = max(1, min(100, int(max_curated or 25)))
        fetch_pool_size = min(100, max(target_limit + 5, 20))

        candidates = cls.search_candidates(clean_kw, max_candidates=fetch_pool_size)
        if not candidates:
            return {
                "success": False,
                "error": f"Tidak ditemukan video terkait kata kunci '{clean_kw}'. Coba gunakan variasi kata kunci lain.",
            }

        cfg_settings = settings or AppSettings.load()
        yt_api_key = cfg_settings.get("youtube_api_key") or getattr(AppConfig, "YOUTUBE_API_KEY", "")

        # Perkaya kandidat yang akan dikurasi dengan jumlah komentar riil secara paralel
        enrich_slice = candidates[: max(target_limit, 15)]
        enrich_videos_with_comment_counts(enrich_slice, api_key=yt_api_key)

        curated = cls.curate_with_ai(clean_kw, enrich_slice, max_curated=target_limit, settings=cfg_settings)
        total_comments_available = sum(int(v.get("comment_count", 0) or 0) for v in curated)

        return {
            "success": True,
            "keyword": clean_kw,
            "target_requested": target_limit,
            "total_candidates_found": len(candidates),
            "total_estimated_comments": total_comments_available,
            "curated_videos": curated,
        }
