import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

import instaloader
from instaloader.exceptions import (
    InstaloaderException,
    LoginRequiredException,
    QueryReturnedBadRequestException,
    ConnectionException,
    ProfileNotExistsException,
)

from cari_siber.engine.core.config import AppConfig, extract_instagram_shortcode
from cari_siber.engine.core.exceptions import PipelineError
from cari_siber.engine.pipelines.youtube_comments.pipeline_scrape import save_youtube_outputs

logger = logging.getLogger("cari_siber.engine.instagram")


def _init_instaloader_context(session_user: Optional[str] = None) -> instaloader.Instaloader:
    """
    Menginisialisasi objek Instaloader.
    Mendukung pemuatan session file otomatis jika ada session_user yang disimpan sebelumnya.
    """
    loader = instaloader.Instaloader(
        quiet=True,
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        save_metadata=False,
        compress_json=False,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )

    if session_user:
        try:
            loader.load_session_from_file(session_user)
            print(f"[INSTAGRAM] Sesi login untuk pengguna '{session_user}' berhasil dimuat.")
        except Exception as e:
            logger.warning(f"[INSTAGRAM] Tidak dapat memuat file sesi '{session_user}': {e}. Berjalan dalam mode Guest.")
            print(f"[INSTAGRAM] Berjalan dalam mode Guest (tanpa login)...")
    else:
        print("[INSTAGRAM] Berjalan dalam mode Guest (publik / tanpa login)...")

    return loader


def scrape_instagram_comments(
    url_or_shortcode: str,
    max_comments: int = 1000,
    include_replies: bool = True,
    output_dir: Optional[str] = None,
    session_user: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Mengunduh metadata dan komentar dari postingan atau reel Instagram via Instaloader.
    """
    shortcode = extract_instagram_shortcode(url_or_shortcode)
    if not shortcode:
        raise PipelineError(f"URL atau Shortcode Instagram tidak valid: '{url_or_shortcode}'. Format contoh: https://www.instagram.com/p/ABC123xyz/")

    target_dir = output_dir or AppConfig.OUTPUT_DIR
    os.makedirs(target_dir, exist_ok=True)

    print("\n" + "=" * 65)
    print("   LANGKAH 0: INSTAGRAM POST & REELS SCRAPER (INSTALOADER)")
    print("=" * 65)
    print(f"[INFO] Target Shortcode   : {shortcode}")
    print(f"[INFO] URL Instagram      : https://www.instagram.com/p/{shortcode}/")
    print(f"[INFO] Batas Komentar     : {max_comments}")
    print(f"[INFO] Sertakan Balasan   : {include_replies}")

    loader = _init_instaloader_context(session_user or getattr(AppConfig, "INSTAGRAM_SESSION_USER", None))

    try:
        print(f"[INFO] Menghubungi Instagram untuk post '{shortcode}'...")
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
    except LoginRequiredException:
        raise PipelineError("Instagram memerlukan login untuk melihat postingan ini (konten dibatasi usia atau privat).")
    except ProfileNotExistsException:
        raise PipelineError(f"Postingan Instagram dengan shortcode '{shortcode}' tidak ditemukan atau telah dihapus.")
    except Exception as e:
        raise PipelineError(f"Gagal mengambil metadata postingan Instagram '{shortcode}': {str(e)}")

    # Metadata Postingan
    caption = (post.caption or "").strip()
    title_display = caption.split("\n")[0][:90] if caption else f"Instagram Post {shortcode}"
    owner_username = post.owner_username or "instagram_user"
    owner_id = str(post.owner_id or "")
    published_iso = post.date_utc.strftime("%Y-%m-%d %H:%M:%S") if post.date_utc else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    views_count = int(post.video_view_count or 0) if post.is_video else 0
    likes_count = int(post.likes or 0)
    total_comments_rep = int(post.comments or 0)

    print(f" -> Pemilik Post : @{owner_username} (ID: {owner_id})")
    print(f" -> Teks Caption : {title_display}...")
    print(f" -> Likes Post   : {likes_count:,} | Views: {views_count:,} | Total Komentar Dilaporkan: {total_comments_rep:,}")

    video_meta = {
        "video_id": shortcode,
        "video_url": f"https://www.instagram.com/p/{shortcode}/",
        "video_title": f"Instagram - {owner_username}: {title_display}",
        "channel_name": f"@{owner_username}",
        "channel_id": owner_id,
        "published_at": published_iso,
        "views": views_count,
        "video_likes": likes_count,
        "total_comments_reported": total_comments_rep,
        "description": caption,
    }

    # Pengambilan Komentar
    print(f"[DOWNLOADER] Mengambil komentar via Instaloader...")
    comments_collected: List[Dict[str, Any]] = []
    seen_ids = set()

    try:
        comment_iterator = post.get_comments()
        for c in comment_iterator:
            if max_comments and len(comments_collected) >= max_comments:
                break

            cid = str(c.id)
            if cid in seen_ids:
                continue
            seen_ids.add(cid)

            c_author = c.owner.username if c.owner else "Anonim"
            c_author_id = str(c.owner.userid) if c.owner else ""
            c_text = str(c.text or "").strip()
            c_time = c.created_at_utc.strftime("%Y-%m-%d %H:%M:%S") if c.created_at_utc else published_iso
            c_likes = int(c.likes_count or 0)
            is_creator = (c_author.lower() == owner_username.lower())

            comments_collected.append({
                "video_id": shortcode,
                "video_title": video_meta["video_title"],
                "channel_name": video_meta["channel_name"],
                "channel_id": owner_id,
                "comment_id": cid,
                "username": c_author,
                "author_channel_id": c_author_id,
                "avatar": "",
                "comment_text": c_text,
                "like_count": c_likes,
                "reply_count": 0,
                "is_hearted": False,
                "is_pinned": False,
                "is_official": is_creator,
                "created_at": c_time,
                "is_reply": False,
                "parent_comment_id": "",
            })

            # Sub-replies jika diizinkan
            if include_replies:
                try:
                    for ans in c.answers:
                        if max_comments and len(comments_collected) >= max_comments:
                            break
                        aid = str(ans.id)
                        if aid in seen_ids:
                            continue
                        seen_ids.add(aid)

                        a_author = ans.owner.username if ans.owner else "Anonim"
                        a_author_id = str(ans.owner.userid) if ans.owner else ""
                        a_text = str(ans.text or "").strip()
                        a_time = ans.created_at_utc.strftime("%Y-%m-%d %H:%M:%S") if ans.created_at_utc else c_time
                        a_likes = int(ans.likes_count or 0)
                        a_is_creator = (a_author.lower() == owner_username.lower())

                        comments_collected.append({
                            "video_id": shortcode,
                            "video_title": video_meta["video_title"],
                            "channel_name": video_meta["channel_name"],
                            "channel_id": owner_id,
                            "comment_id": aid,
                            "username": a_author,
                            "author_channel_id": a_author_id,
                            "avatar": "",
                            "comment_text": a_text,
                            "like_count": a_likes,
                            "reply_count": 0,
                            "is_hearted": False,
                            "is_pinned": False,
                            "is_official": a_is_creator,
                            "created_at": a_time,
                            "is_reply": True,
                            "parent_comment_id": cid,
                        })
                except Exception as reply_err:
                    logger.debug(f"Lewati balasan untuk komentar {cid}: {reply_err}")

            if len(comments_collected) % 50 == 0:
                print(f" -> Terkumpul {len(comments_collected)} komentar...")

    except LoginRequiredException:
        print(f"\n[PERINGATAN] Instagram membatasi akses guest/tanpa login setelah {len(comments_collected)} komentar.")
    except QueryReturnedBadRequestException:
        print(f"\n[PERINGATAN] Instagram mengirim bad request / rate limit setelah {len(comments_collected)} komentar.")
    except Exception as scrape_err:
        if len(comments_collected) > 0:
            print(f"\n[PERINGATAN] Scraping Instagram terhenti ({str(scrape_err)}), melanjutkan dengan {len(comments_collected)} komentar yang telah terkumpul.")
        else:
            raise PipelineError(f"Gagal mengunduh komentar Instagram: {str(scrape_err)}")

    if not comments_collected:
        raise PipelineError(
            f"Tidak ada komentar yang berhasil diambil dari postingan Instagram '{shortcode}'. "
            "Postingan ini mungkin tidak memiliki komentar aktif atau dibatasi oleh Instagram."
        )

    print(f"\n[SUCCESS] Berhasil mengunduh total {len(comments_collected)} komentar Instagram!")

    # Simpan dalam format CSV yang identik dengan pipeline YouTube agar kompatibel 100%
    save_youtube_outputs(video_meta, comments_collected, target_dir)

    return {
        "shortcode": shortcode,
        "video_meta": video_meta,
        "comments_count": len(comments_collected),
    }


def run_instagram_scraper(config_override: Optional[Dict[str, Any]] = None):
    """
    Orkestrator Langkah 0 untuk scraping postingan / reels Instagram.
    Dipanggil langsung oleh PipelineRunner ketika platform target adalah 'instagram'.
    """
    cfg = config_override or {}
    url_target = cfg.get("INSTAGRAM_URL") or cfg.get("TARGET_URL") or AppConfig.YOUTUBE_VIDEO_URL
    max_comments = cfg.get("LIMIT_COMMENTS") or AppConfig.YOUTUBE_LIMIT_COMMENTS
    include_replies = cfg.get("INCLUDE_REPLIES", AppConfig.YOUTUBE_INCLUDE_REPLIES)
    output_dir = cfg.get("OUTPUT_DIR", AppConfig.OUTPUT_DIR)

    return scrape_instagram_comments(
        url_or_shortcode=url_target,
        max_comments=max_comments,
        include_replies=include_replies,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scrape_instagram_comments(sys.argv[1])
    else:
        print("Penggunaan: python pipeline_scrape.py <url_atau_shortcode_instagram>")
