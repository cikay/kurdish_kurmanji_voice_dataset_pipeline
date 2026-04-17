import hashlib
import json
from pathlib import Path

import yt_dlp

from .base import AudioAcquireStrategy
from .youtube_video_downloader import YoutubeVideoDownloader


class YoutubeVideosAudioStrategy(AudioAcquireStrategy):
    def __init__(self, urls: list[str]) -> None:
        self.urls = urls
        self._downloader = YoutubeVideoDownloader()
        # Stable directory name derived from the URL list
        digest = hashlib.sha256(" ".join(sorted(urls)).encode()).hexdigest()[:12]
        self._source_id = f"youtube_videos_{digest}"

    @classmethod
    def from_config(cls, cfg: dict) -> "YoutubeVideosAudioStrategy":
        return cls(urls=cfg["urls"])

    @property
    def source_id(self) -> str:
        return self._source_id

    def items(self, cache_path: Path) -> list[dict]:
        if cache_path.exists():
            videos = json.loads(cache_path.read_text(encoding="utf-8"))
            print(f"  📋 Loaded {len(videos)} items from cache: {cache_path}")
            return videos

        print(f"  🔍 Fetching metadata for {len(self.urls)} URL(s)...")
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "cachedir": False,
        }

        videos = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in self.urls:
                try:
                    info = ydl.extract_info(url, download=False)
                    video_id = info.get("id")
                    title = info.get("title")
                    if not video_id or not title:
                        print(f"  ⚠️  Skipping {url}: missing id or title")
                        continue
                    videos.append({"id": video_id, "title": title, "url": url})
                except Exception as e:
                    print(f"  ❌ Metadata fetch failed for {url}: {e}")

        print(f"  ✅ Resolved {len(videos)} video(s)")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return videos

    def download(self, item: dict, audio_dir: Path, cookies_file: Path | None) -> Path | None:
        return self._downloader.download(item, audio_dir, cookies_file)
