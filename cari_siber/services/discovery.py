import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

import requests

from cari_siber.engine.core.config import AppConfig, extract_youtube_video_id
from cari_siber.engine.core.ai_client import generate_text
from cari_siber.settings import AppSettings

logger = logging.getLogger("cari_siber.services.discovery")


def search_youtube_innertube(query: str, max_candidates: int = 25) -> List[Dict[str, Any]]:
    """
    Mencari video YouTube berbasis kata kunci menggunakan endpoint Innertube Web
    secara instan tanpa memerlukan YouTube Data API Key.
    """
    url = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/json",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    }
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

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"Gagal menghubungi Innertube search: {e}")
        return []

    def _extract_video_renderers(obj):
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
                    res.append({
                        "video_id": vid,
                        "url": vid_url,
                        "video_url": vid_url,
                        "title": title.strip(),
                        "channel": channel.strip(),
                        "channel_name": channel.strip(),
                        "views": views.strip() or "0 views",
                        "views_str": views.strip() or "0 views",
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

    all_found = _extract_video_renderers(data)
    
    # Hilangkan duplikat video_id
    seen = set()
    unique_videos = []
    for v in all_found:
        if v["video_id"] not in seen:
            seen.add(v["video_id"])
            unique_videos.append(v)
            if len(unique_videos) >= max_candidates:
                break

    return unique_videos


def search_youtube_official_api(query: str, api_key: str, max_candidates: int = 15) -> List[Dict[str, Any]]:
    """
    Pencarian menggunakan YouTube Data API v3 resmi jika API key disediakan.
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query.strip(),
        "type": "video",
        "maxResults": min(max_candidates, 25),
        "relevanceLanguage": "id",
        "key": api_key.strip(),
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"YouTube Data API v3 search error: {e}, beralih ke Innertube...")
        return []

    items = data.get("items", [])
    candidates = []
    for it in items:
        vid = it.get("id", {}).get("videoId")
        snip = it.get("snippet", {})
        if vid and snip:
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
                "published": snip.get("publishedAt", "")[:10],
                "published_str": snip.get("publishedAt", "")[:10],
                "duration": "--:--",
                "duration_str": "--:--",
                "thumbnail": thumb or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "thumbnail_url": thumb or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "description": snip.get("description", "")[:200],
            })
    return candidates


class VideoDiscoveryService:
    """
    Layanan pencarian dan kurasi semantik video YouTube berbasis isu/keyword.
    """

    @classmethod
    def search_candidates(cls, query: str, max_candidates: int = 15) -> List[Dict[str, Any]]:
        settings = AppSettings.load()
        api_key = settings.get("youtube_api_key") or getattr(AppConfig, "YOUTUBE_API_KEY", "")

        candidates = []
        if api_key:
            candidates = search_youtube_official_api(query, api_key, max_candidates)

        if not candidates:
            candidates = search_youtube_innertube(query, max_candidates)

        return candidates

    @classmethod
    def curate_with_ai(
        cls,
        keyword: str,
        candidates: List[Dict[str, Any]],
        max_curated: int = 5,
        settings: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Menjalankan AI Curation Gate untuk mengevaluasi relevansi, menyaring clickbait,
        menilai potensi diskusi publik, dan menyusun peringkat video terbaik.
        """
        if not candidates:
            return []

        # Ringkas data kandidat untuk prompt LLM yang hemat token
        prompt_data = [
            {
                "index": idx + 1,
                "video_id": c["video_id"],
                "title": c["title"],
                "channel": c["channel_name"],
                "views": c["views_str"],
                "description": c["description"][:120],
            }
            for idx, c in enumerate(candidates[:12])
        ]

        system_instruction = (
            "Anda adalah Senior Cognitive Intelligence & OSINT Analyst. Tugas Anda adalah mengkurasi video "
            "YouTube terbaik untuk analisis opini publik dan polarisasi sosial berdasarkan isu yang diberikan."
        )

        prompt = f"""Isu / Kata Kunci Target: "{keyword}"

Berikut adalah daftar kandidat video YouTube yang ditemukan:
{json.dumps(prompt_data, ensure_ascii=False, indent=2)}

Tugas Anda:
1. Saring video yang TIDAK relevan, clickbait murni, musik/lagu latar, atau video kompilasi tanpa diskursus opini.
2. Nilai relevansi konten terhadap isu "{keyword}" (skor 0 - 100).
3. Nilai potensi perdebatan / diskursus opini di kolom komentar (Tinggi / Sedang / Rendah).
4. Berikan satu kalimat singkat profesional sebagai alasan kurasi AI (curation_reason).
5. Pilih {max_curated} video terbaik, diurutkan dari yang paling berkualitas dan representatif.

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
        model = cfg_settings.get("ai_model", "gemini-3.8-flash")
        api_key = cfg_settings.get(f"{provider}_api_key") or getattr(AppConfig, f"{provider.upper()}_API_KEY", "")
        if provider == "custom":
            AppConfig.CUSTOM_BASE_URL = cfg_settings.get("custom_base_url", "https://api.tokenai.id/v1")
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

            # Ekstrak JSON dari respon LLM
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

            # Petakan kembali ke data kandidat asli
            cand_map = {c["video_id"]: c for c in candidates}
            final_curated = []

            for item in curated_items:
                vid = item.get("video_id")
                if vid in cand_map:
                    base = cand_map[vid].copy()
                    rel_score = int(item.get("relevance_score", 85))
                    base["relevance_score"] = rel_score
                    base["discussion_viability"] = str(item.get("discussion_viability", "Tinggi"))
                    base["curation_reason"] = str(item.get("curation_reason", "Relevan dengan topik pembahasan."))
                    base["curation_tag"] = str(item.get("tag", "Rekomendasi AI"))
                    base["is_recommended"] = bool(item.get("is_recommended", rel_score >= 80))
                    final_curated.append(base)

            if final_curated:
                return final_curated

        except Exception as e:
            logger.warning(f"AI Curation Gate gagal/timeout: {e}. Menggunakan fallback heuristik.")

        # Fallback Heuristik Cerdas jika AI offline / error
        fallback_curated = []
        for idx, c in enumerate(candidates[:max_curated]):
            item = c.copy()
            item["relevance_score"] = max(70, 95 - (idx * 5))
            item["discussion_viability"] = "Tinggi" if idx < 2 else "Sedang"
            item["curation_reason"] = f"Video teratas dari kanal {c.get('channel') or c.get('channel_name')} dengan interaksi penonton aktif."
            item["curation_tag"] = "Paling Populer" if idx == 0 else "Rekomendasi"
            item["is_recommended"] = True if idx < 3 else False
            fallback_curated.append(item)

        return fallback_curated

    @classmethod
    def discover_and_curate(
        cls,
        keyword: str,
        max_curated: int = 10,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Fungsi orkestrasi lengkap: Pencarian calon video -> Kurasi AI -> Return daftar siap pilih.
        """
        if not keyword or not keyword.strip():
            return {"success": False, "error": "Kata kunci pencarian tidak boleh kosong."}

        clean_kw = keyword.strip()
        candidates = cls.search_candidates(clean_kw, max_candidates=25)
        if not candidates:
            return {
                "success": False,
                "error": f"Tidak ditemukan video terkait kata kunci '{clean_kw}'. Coba gunakan variasi kata kunci lain.",
            }

        curated = cls.curate_with_ai(clean_kw, candidates, max_curated=max_curated, settings=settings)

        return {
            "success": True,
            "keyword": clean_kw,
            "total_candidates_found": len(candidates),
            "curated_videos": curated,
        }
