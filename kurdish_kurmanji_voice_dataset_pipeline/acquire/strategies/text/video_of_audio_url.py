import difflib
import tempfile
from pathlib import Path

import cv2
import yt_dlp
from paddleocr import PaddleOCR

from .base import TextAcquireStrategy

_CHANGE_THRESHOLD = 8.0
_SAMPLE_FPS = 1.0
_SIMILARITY_CUTOFF = 0.92
_OCR_CONFIDENCE = 0.5


def _download_video(url: str, out_dir: Path) -> Path | None:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestvideo[ext=mp4]/best[ext=mp4]/best",
        "outtmpl": str(out_dir / "video.%(ext)s"),
        "noplaylist": True,
        "cachedir": False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        ext = info.get("ext", "mp4")
        path = out_dir / f"video.{ext}"
        return path if path.exists() else None
    except Exception as e:
        print(f"  ❌ Video download failed: {e}")
        return None


def _group_into_lines(words: list[tuple[float, float, float, float, str]]) -> str:
    """Group (x1, y1, x2, y2, text) word boxes into text lines."""
    if not words:
        return ""
    avg_height = sum(w[3] - w[1] for w in words) / len(words)
    y_threshold = avg_height * 0.6

    items = sorted(words, key=lambda w: (w[1] + w[3]) / 2)
    lines: list[list] = [[items[0]]]

    for item in items[1:]:
        y_center = (item[1] + item[3]) / 2
        last_y = sum((w[1] + w[3]) / 2 for w in lines[-1]) / len(lines[-1])
        if abs(y_center - last_y) <= y_threshold:
            lines[-1].append(item)
        else:
            lines.append([item])

    return "\n".join(
        " ".join(w[4] for w in sorted(line, key=lambda w: w[0]))
        for line in lines
    )


def _ocr_frame(ocr: PaddleOCR, frame) -> str:
    result = ocr.ocr(frame)
    if not result or not result[0]:
        return ""

    page = result[0]
    words: list[tuple[float, float, float, float, str]] = []
    for box, text, score in zip(
        page.get("rec_boxes", []),
        page.get("rec_texts", []),
        page.get("rec_scores", []),
    ):
        if score >= _OCR_CONFIDENCE:
            words.append((box[0], box[1], box[2], box[3], text))

    return _group_into_lines(words)


def _is_duplicate(text: str, previous: str) -> bool:
    return difflib.SequenceMatcher(None, text, previous).ratio() >= _SIMILARITY_CUTOFF


def _extract_text_from_video(video_path: Path) -> str:
    ocr = PaddleOCR(use_angle_cls=True, lang="ku")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return ""

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_interval = max(1, int(video_fps / _SAMPLE_FPS))

    texts: list[str] = []
    frame_idx = 0
    _, first_frame = cap.read()
    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval != 0:
            frame_idx += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray, prev_gray).mean()
        if diff > _CHANGE_THRESHOLD:
            text = _ocr_frame(ocr, frame)
            if text and not (texts and _is_duplicate(text, texts[-1])):
                texts.append(text)

        prev_gray = gray
        frame_idx += 1

    cap.release()
    return "\n\n".join(texts)


class VideoOfAudioUrlTextStrategy(TextAcquireStrategy):
    @classmethod
    def from_config(cls, cfg: dict) -> "VideoOfAudioUrlTextStrategy":
        return cls()

    def fetch(self, hint: dict) -> dict | None:
        url = hint.get("url")
        if not url:
            print(f"  ❌ No URL in hint for: {hint.get('title')!r}")
            return None

        print(f"  🎬 Downloading video: {url}")
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = _download_video(url, Path(tmp_dir))
            if not video_path:
                return None

            print("  🔍 Scanning frames for text...")
            text = _extract_text_from_video(video_path)

        if not text:
            print(f"  ⚠️  No text extracted from video: {url}")
            return None

        return {
            "title": hint.get("title") or "",
            "author": "",
            "text": text,
            "source_url": url,
        }
