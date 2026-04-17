import json
import re
from pathlib import Path

import yt_dlp
from slugify import slugify

from .base import AudioAcquireStrategy
from .youtube_video_downloader import YoutubeVideoDownloader


def _extract_playlist_id(url: str) -> str:
    match = re.search(r"list=([A-Za-z0-9_-]+)", url)
    return match.group(1) if match else slugify(url)[:32]


class YoutubePlaylistAudioStrategy(AudioAcquireStrategy):
    def __init__(self, playlist_url: str) -> None:
        self.playlist_url = playlist_url
        self._source_id = _extract_playlist_id(playlist_url)
        self._downloader = YoutubeVideoDownloader()

    @classmethod
    def from_config(cls, cfg: dict) -> "YoutubePlaylistAudioStrategy":
        return cls(playlist_url=cfg["playlist_url"])

    @property
    def source_id(self) -> str:
        return self._source_id

    def items(self, cache_path: Path) -> list[dict]:
        if cache_path.exists():
            videos = json.loads(cache_path.read_text(encoding="utf-8"))
            print(f"  📋 Loaded {len(videos)} items from cache: {cache_path}")
            return videos

        print(f"  🔍 Fetching playlist metadata: {self.playlist_url}")
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": "in_playlist",
            "noplaylist": False,
            "cachedir": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.playlist_url, download=False)
        except Exception as e:
            print(f"  ❌ Playlist fetch error: {e}")
            return []

        videos = []
        for entry in info.get("entries") or []:
            if not entry:
                continue
            video_id = entry.get("id") or entry.get("url")
            title = entry.get("title")
            if not video_id or not title:
                continue
            videos.append({
                "id": video_id,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
            })

        print(f"  ✅ Found {len(videos)} videos")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return videos

    def download(self, item: dict, audio_dir: Path, cookies_file: Path | None) -> Path | None:
        return self._downloader.download(item, audio_dir, cookies_file)
