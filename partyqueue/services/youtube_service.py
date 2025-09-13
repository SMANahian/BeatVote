import os
import requests

API_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"


def search_videos(query: str, api_key: str | None = None, max_results: int = 10) -> list[dict]:
    api_key = api_key or os.getenv("YOUTUBE_API_KEY", "")
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
        results.append({
            "video_id": item["id"],
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "duration": duration,
            "thumbnails": snippet.get("thumbnails", {}),
        })
    return results
