# This file eill pull the metadata for an Instagram Video 

import yt_dlp
import httpx
import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

# Extract Insta shortcode from Reel URL
def extract_shortcode(url:str)->str:
    match = re.search(r"/(?:reel|p|tv)/([A-Za-z0-9_-]+)",url)
    if not match:
        raise ValueError(f"Could not extract shortcode from URL:{url}")
    return match.group(1)

# Extarct the captiona from Insta video
def get_caption_and_video(url:str)->dict:
    ydl_opts = {
        "quiet":True,
        "skip_download":True,
        "extract_flat":False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url,download = False)

    return {
        "title": info.get("title",""),
        "description":info.get("description","") or info.get("title",""),
        "duration": info.get("duration",0),
        "thumbnail": info.get("thumbnail",""),
        "upload_date": info.get("upload_date",""),
        "creator_username": info.get("uploader_id","") or info.get("uploader",""),
    }


# help to get real data through Nokia API (RapidAPI)
def get_instagram_api_stats(shortcode:str,api_key:str)->dict:
    reel_url = f"https://www.instagram.com/reel/{shortcode}/"

    url = "https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items"
    headers = {"Content-Type": "application/json"}
    params = {"token": api_key, "timeout": 120}

    payload = {
        "directUrls": [reel_url],
        "resultsType": "posts",
        "resultsLimit": 1,
        "addParentData": False,
    }

    print(f"[Instagram] Calling apify/instagram-scraper")
    try:
        resp = httpx.post(
            url, headers=headers, params=params, json=payload, timeout=130
        )
        print(f"[Instagram] Status: {resp.status_code}")

        if resp.status_code not in (200,201):
            print(f"[Instagram] Error: {resp.text[:500]}")
            return {}

        items = resp.json()
        if not items:
            print("[Instagram] No items returned")
            return {}

        post = items[0]
        print(f"[Instagram] Full post data: {json.dumps(post, indent=2)[:2000]}")

        likes    = post.get("likesCount", 0) or 0
        comments = post.get("commentsCount", 0) or 0
        views    = post.get("videoViewCount", 0) or post.get("videoPlayCount", 0) or 0

        return {
            "likes": likes,
            "comments": comments,
            "views": views,
            "creator_username": post.get("ownerUsername", ""),
            "creator_full_name": post.get("ownerFullName", ""),
            "creator_verified": post.get("ownerIsVerified", False),
            "hashtags": post.get("hashtags", []),
        }

    except httpx.TimeoutException:
        print("[Instagram] Timed out after 120s")
        return {}
    except Exception as e:
        print(f"[Instagram] Error: {e}")
        return {}


# return transcript and metadata combined
def extract_instagram(url:str)->dict:
    shortcode = extract_shortcode(url)
    print(f"[Instagram] Extracting Shortcode: {shortcode}")
    print(f"[Instagram] Fetching caption + basic info via yt-dlf")
    base = get_caption_and_video(url)

    transcript_text = base["description"]

    api_key = os.getenv("APIFY_TOKEN")
    stats = {}
    if api_key:
        print("[Instagram] Fetching real stats via Apify")
        stats = get_instagram_api_stats(shortcode,api_key)
    else:
        print("[Instagram] No Apify Token - stats will be limited")

    views = stats.get("views",0)
    likes = stats.get("likes",0)
    comments = stats.get("comments",0)

    engagement_rate = (
        round((likes+comments)/views*100,4) if views > 0 else 0
    )
    metadata = {
        "title": base["title"],
        "creator": stats.get("creator_username") or base["creator_username"],
        "creator_full_name": stats.get("creator_full_name", ""),
        "creator_verified": stats.get("creator_verified", False),
        "upload_date": base["upload_date"],
        "duration": base["duration"],
        "thumbnail": base["thumbnail"],
        "views": views,
        "likes": likes,
        "comments": comments,
        "hashtags": stats.get("hashtags", []),
        "engagement_rate": engagement_rate,
    }

    return {
        "video_id":"B",
        "source":"instagram",
        "url": url,
        "shortcode":shortcode,
        "transcript_text":transcript_text,
        "transcript_segments": [{"text": transcript_text, "start": 0.0, "end": float(base["duration"])}],
        "metadata":metadata,
    }
