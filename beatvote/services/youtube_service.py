import os
import re

import requests

API_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

_DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def _duration_to_seconds(duration: str) -> int:
    match = _DURATION_RE.fullmatch(duration or "")
    if not match:
        return 0
    hours, minutes, seconds = (int(g or 0) for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def search_videos(
    query: str, api_key: str | None = None, max_results: int = 10
) -> list[dict]:
    api_key = api_key or os.getenv("YOUTUBE_API_KEY", "")
    if not api_key:
        raise ValueError("missing YOUTUBE_API_KEY")
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": api_key,
    }
    resp = requests.get(API_URL, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
    if not video_ids:
        return []
    # fetch durations
    params = {
        "part": "contentDetails,snippet",
        "id": ",".join(video_ids),
        "key": api_key,
    }
    v_resp = requests.get(VIDEO_URL, params=params, timeout=5)
    v_resp.raise_for_status()
    v_data = v_resp.json()
    results = []
    for item in v_data.get("items", []):
        snippet = item["snippet"]
        duration = item["contentDetails"]["duration"]
        thumbnails = snippet.get("thumbnails", {})
        thumb_url = (
            (thumbnails.get("medium") or {}).get("url")
            or (thumbnails.get("default") or {}).get("url")
            or ""
        )
        results.append(
            {
                "video_id": item["id"],
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "duration": duration,
                "duration_sec": _duration_to_seconds(duration),
                "thumbnail_url": thumb_url,
                "thumbnails": thumbnails,
            }
        )
    return results
