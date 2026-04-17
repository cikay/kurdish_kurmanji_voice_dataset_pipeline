import subprocess
from pathlib import Path

import yt_dlp

SAMPLE_RATE = 16000


class YoutubeVideoDownloader:
    """Downloads a single YouTube video as a 16kHz mono WAV.

    Shared by any audio strategy that sources from YouTube, regardless of
    whether items come from a playlist, a single URL, or a list of URLs.
    """

    def download(self, item: dict, audio_dir: Path, cookies_file: Path | None) -> Path | None:
        """Download audio for one item into audio_dir.

        item must contain 'id' (str) and 'url' (str).
        Returns the WAV path on success, None on failure.
        """
        video_id = item["id"]
        output_path = audio_dir / f"{video_id}.wav"

        if output_path.exists():
            print(f"  ⏭️  Audio already exists: {output_path.name}")
            return output_path

        temp_dir = audio_dir / "_tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": str(temp_dir / f"{video_id}.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "retries": 3,
                "fragment_retries": 3,
                "cachedir": False,
            }
            if cookies_file and cookies_file.exists():
                ydl_opts["cookiefile"] = str(cookies_file)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item["url"], download=True)
                temp_path = Path(ydl.prepare_filename(info))

            if not temp_path.exists():
                matches = sorted(temp_dir.glob(f"{video_id}.*"))
                temp_path = matches[0] if matches else temp_path

            if not temp_path.exists():
                raise FileNotFoundError(f"No audio file produced for {video_id}")

            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(temp_path),
                    "-vn", "-ar", str(SAMPLE_RATE),
                    "-ac", "1",
                    "-acodec", "pcm_s16le",
                    str(output_path),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            temp_path.unlink(missing_ok=True)
            return output_path if output_path.exists() else None

        except yt_dlp.utils.DownloadError as e:
            print(f"  ❌ Audio download failed: {e}")
            print("     Hint: try updating yt-dlp (e.g. `pipenv update yt-dlp`).")
        except Exception as e:
            print(f"  ❌ Audio failed: {e}")

        for p in temp_dir.glob(f"{video_id}.*"):
            p.unlink(missing_ok=True)
        return None
