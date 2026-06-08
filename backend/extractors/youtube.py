# This file will do two things
# 1. Pull the transcript using youtube-transcript-api
# 2. Pull metadata ( views , likes , duration , upload date , etc) using yt-dlp

import yt_dlp 
import httpx
import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.proxies import WebshareProxyConfig
from urllib.parse import urlparse , parse_qs
from dotenv import load_dotenv

load_dotenv()
proxy_url = os.getenv("WEBSHARE_PROXY_URL")
proxy_username = os.getenv("WEBSHARE_PROXY_USERNAME")
proxy_password = os.getenv("WEBSHARE_PROXY_PASSWORD")

# Extracts video ID from any Youtube URL format
def extract_video_id(url:str)->str:
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path[1:]
    if parsed.hostname in ("www.youtube.com","youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query)["v"][0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/shorts/")[1]
    raise ValueError(f"Could not extract video ID from URL:{url}")

# Return list of segments [{text,start,duration}]
def get_transcript(video_id: str)-> list[dict]:
    api_key = os.getenv("YOUTUBE_API_KEY")

    # --- Primary: Official captions via timedtext API ---
    if api_key:
        try:
            return get_transcript_via_api(video_id, api_key)
        except Exception as e:
            print(f"[YouTube] API transcript failed: {e}, trying fallback...")

    return get_transcript_via_scraper(video_id)

def get_transcript_via_api(video_id: str, api_key: str) -> list[dict]:
    captions_url = (
        f"https://www.googleapis.com/youtube/v3/captions"
        f"?part=snippet&videoId={video_id}&key={api_key}"
    )
    resp = httpx.get(captions_url, timeout=10)
    data = resp.json()

    if "error" in data:
        raise ValueError(f"Captions API error: {data['error']['message']}")

    items = data.get("items", [])
    if not items:
        raise ValueError("No captions found via API")

    caption_id = None
    for item in items:
        snippet = item.get("snippet", {})
        if snippet.get("language") == "en":
            caption_id = item["id"]
            if snippet.get("trackKind") == "standard":
                break  

    if not caption_id:
        caption_id = items[0]["id"]  

    timedtext_url = (
        f"https://www.youtube.com/api/timedtext"
        f"?v={video_id}&lang=en&fmt=json3"
    )
    resp = httpx.get(timedtext_url, timeout=10)

    if resp.status_code != 200 or not resp.text:
        raise ValueError("Timedtext endpoint returned empty")

    data = resp.json()
    events = data.get("events", [])

    segments = []
    for event in events:
        segs = event.get("segs", [])
        start = event.get("tStartMs", 0) / 1000
        duration = event.get("dDurationMs", 0) / 1000
        text = "".join(s.get("utf8", "") for s in segs).strip()
        if text and text != "\n":
            segments.append({
                "text": text,
                "start": round(start, 2),
                "duration": round(duration, 2),
            })

    if not segments:
        raise ValueError("No segments in timedtext response")

    print(f"[YouTube] Got {len(segments)} segments via timedtext API")
    return segments


def get_transcript_via_scraper(video_id: str) -> list[dict]:
    if proxy_username and proxy_password:
        ytt_api = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password,
                filter_ip_locations=["in", "us", "gb"],
            )
        )
    else:
        ytt_api = YouTubeTranscriptApi()

    try:
        transcript_list = ytt_api.list(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript(["en"])

        fetched = transcript.fetch()
        return [
            {"text": s.text, "start": s.start, "duration": s.duration}
            for s in fetched
        ]
    except TranscriptsDisabled:
        raise ValueError(f"Transcripts disabled for: {video_id}")
    except Exception as e:
        raise ValueError(f"Could not fetch transcript: {str(e)}")



# help to get real data through YouTube Data API v3
def get_yt_api_stats(video_id: str, api_key:str)->dict:
    url = (
        f"https://www.googleapis.com/youtube/v3/videos"
        f"?part=statistics,snippet&id={video_id}&key={api_key}"
    )
    resp = httpx.get(url,timeout=10)
    data = resp.json()

    if not data.get("items"):
        return {}
    
    stats = data["items"][0]["statistics"]
    snippet = data["items"][0]["snippet"]

    return {
        "views": int(stats.get("viewCount",0)),
        "likes": int(stats.get("likeCount",0)),
        "comments": int(stats.get("commentCount",0)),
        "title": snippet.get("title",""),
        "creator": snippet.get("channelTitle",""),
        "upload_date": snippet.get("publishedAt",'')[:10],
        "hashtags":snippet.get("tags",[]),
        "description":snippet.get("description","")[:500],
        "thumbnail":snippet.get("thumbnails",{}).get("high",{}).get("url",""),
    }


# uses yt-dlp to pull video metadata without downloading 
def get_metadata(url:str)->dict:
    ydl_opts = {
        "quiet":True,
        "skip_download":True,
    }
    if proxy_url:
        ydl_opts["proxy"] = proxy_url
        print("[YouTube] Using proxy for yt-dlp metadata")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url,download=False)

    return {
        "title":info.get("title",""),
        "creator": info.get("uploader", ""),
        "channel_url": info.get("channel_url", ""),
        "upload_date": info.get("upload_date", ""),
        "duration": info.get("duration", 0),
        "views": info.get("view_count",0) or 0,
        "likes": info.get("like_count",0) or 0,
        "comments": info.get("comment_count",0) or 0,
        "hashtags": info.get("tags", []),
        "description":info.get("description",""[:500]),
        "thumbnail":info.get("thumbnail",""),
    }

# return transcript and metadata combined
def extract_youtube(url:str)->dict:
    video_id = extract_video_id(url)
    print(f"[YouTube] Extracting video_id: {video_id}")

    transcript_raw = get_transcript(video_id)

    transcript_text = " ".join([seg["text"] for seg in transcript_raw])
    transcript_with_timestamps = [
        {
            "text":seg["text"],
            "start":round(seg["start"],2),
            "end":round(seg["start"]+seg["duration"],2),
        }
        for seg in transcript_raw
    ]

    api_key = os.getenv("YOUTUBE_API_KEY")
    if api_key:
        print("[YouTube] Using YouTube Data Api v3 for stats")
        stats = get_yt_api_stats(video_id,api_key)
        ydl_opts = {"quiet":True,"skip_download":True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url,download=False)
        stats["duration"]=info.get("duration",0)
        metadata = stats
    else:
        print("[YouTube] Using yt-dlp (likes/comments may be 0)")
        metadata = get_metadata(url)

    views = metadata.get("views",0)
    likes = metadata.get("likes",0)
    comments = metadata.get("comments",0)
    metadata["engagement_rate"]=(
        round((likes+comments)/views*100,4) if views>0 else 0
    )

    return {
        "video_id":"A",
        "source":"youtube",
        "url":url,
        "yt_video_id":video_id,
        "transcript_text":transcript_text,
        "transcript_segments":transcript_with_timestamps,
        "metadata":metadata,
    }

