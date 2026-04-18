# Kurdish Kurmanji Voice Dataset Pipeline

A modular pipeline for building a Kurdish Kurmanji (kmr) TTS voice dataset by pairing audio recordings with their matching transcription text from online sources.

## Overview

The pipeline is config-driven. Each YAML config file defines a set of stages and their sources. Currently implemented:

| Stage | Description |
|-------|-------------|
| `acquire` | Download audio + scrape matching text, validate language, save pairs |

## Project Structure

```
configs/
  botan-times.yml                  # Pipeline config for botantimes.com

kurdish_kurmanji_voice_dataset_pipeline/
  pipeline.py                      # Entry point — reads YAML, runs stages

  acquire/
    stage.py                       # AcquireStage — orchestrates sources
    strategies/
      audio/
        base.py                    # AudioAcquireStrategy ABC
        youtube_playlist.py        # Items from a YouTube playlist
        youtube_videos.py          # Items from an explicit list of URLs
        youtube_video_downloader.py # Shared yt-dlp + ffmpeg download logic
      text/
        base.py                    # TextAcquireStrategy ABC
        web_scrape.py              # Text via trafilatura (slugified URL)

data/
  acquire/
    audio/            *.wav                      # 16kHz mono WAV (all sources, flat)
    text/             *.txt                      # UTF-8 transcription (all sources, flat)
    metadata_<source_id>.jsonl                   # One JSON record per audio–text pair, per source
    items_cache_<source_id>.json                 # Cached playlist metadata (speeds up re-runs), per source
```

## Quickstart

**Install dependencies:**
```bash
pipenv install
```

**Run a pipeline config:**
```bash
pipenv run python -m kurdish_kurmanji_voice_dataset_pipeline.pipeline \
  --config configs/botan-times.yml

# With YouTube cookies (needed if playlist is age-restricted):
pipenv run python -m kurdish_kurmanji_voice_dataset_pipeline.pipeline \
  --config configs/botan-times.yml \
  --cookies cookies.txt
```

**Requirements:** `ffmpeg` must be available on `PATH`.

## Config Format

```yaml
stages:
  - acquire           # Stages run in this order

acquire:
  sources:
    - audio:
        strategy: youtube_playlist
        playlist_url: https://www.youtube.com/playlist?list=...
      text:
        strategy: web_scrape
        base_url: https://example.com/
        endpoint_method: slugify-audio-name        # primary: URL = base_url/{slugify(video_title)}/
        endpoint_method_fallbacks:                 # optional: tried in order if primary returns no content
          - slugify-after-slash                    # for titles like "Author / Column" → base_url/{slugify("Column")}/

    - audio:
        strategy: youtube_videos              # One or more explicit URLs
        urls:
          - https://www.youtube.com/watch?v=...
      text:
        strategy: web_scrape
        base_url: https://example.com/
        endpoint_method: slugify-audio-name

  output_dir: data/raw
  language: kmr_Latn                        # FastText language prefix — matches kmr_Latn, kmr_Arab, etc.
  min_lang_confidence: 0.60            # Optional, defaults to 0.60
```

### Audio strategies

| Strategy | Config keys | Description |
|----------|------------|-------------|
| `youtube_playlist` | `playlist_url` | All videos from a YouTube playlist |
| `youtube_videos` | `urls` (list) | Explicit YouTube video URLs; pass a single-item list for one video |

### Text strategies

| Strategy | Config keys | Description |
|----------|------------|-------------|
| `web_scrape` | `base_url`, `endpoint_method`, `endpoint_method_fallbacks` (optional) | Scrapes article text via [trafilatura](https://trafilatura.readthedocs.io) |

**Endpoint methods:**

| Method | URL produced | Notes |
|--------|-------------|-------|
| `slugify-audio-name` | `{base_url}/{slugify(video_title)}/` | Default — slugifies the full title |
| `slugify-after-slash` | `{base_url}/{slugify(part_after_slash)}/` | For titles like `"Author / Column"` — takes text after ` / ` |

**Fallback chain:** `endpoint_method_fallbacks` is an ordered list tried only when the primary returns no content. A fallback whose URL cannot be built (e.g. `slugify-after-slash` with no ` / ` in the title) is silently skipped.

## Acquire Stage Behaviour

For each source the stage:

1. Fetches item metadata (cached to `items_cache_<source_id>.json` after first run)
2. Skips items whose `video_id` was already processed by an earlier source (cross-playlist deduplication)
3. Scrapes the matching article text
4. Validates language with [fastText](https://fasttext.cc/docs/en/language-identification.html) (`kmr_Latn`, min confidence `0.60`)
5. Downloads audio via `yt-dlp`, converts to **16kHz mono WAV** via `ffmpeg`
6. Saves the text file and appends a record to `metadata_<source_id>.jsonl`

The fastText model (`facebook/fasttext-language-identification`) is loaded once and cached for the entire run.

## Output Format

### `metadata.jsonl`
One JSON object per line:

```json
{
  "id": "GCd8A1pShVs",
  "title": "Wezîra Karûbarên Derve ya Tirkiyeyê...",
  "author": "Botan Times",
  "slug": "wezira-karubare-derve-ya-tirkiyeye",
  "audio_file": "audio/GCd8A1pShVs.wav",
  "text_file": "text/GCd8A1pShVs.txt",
  "text_length": 843,
  "source_url": "https://botantimes.com/wezira-karubare-derve-ya-tirkiyeye/",
  "source_id": "PLXRqvgEq6VESn7sQzzmaXp_r3H6stjri6"
}
```

### Text files
Plain UTF-8, reading order matches the audio recording:
```
<author>
<article title>
<article body>
```

## Adding a New Strategy

**New text strategy** (e.g. PDF):
1. Create `acquire/strategies/text/pdf.py` implementing `TextAcquireStrategy`
2. Add `"pdf": PdfTextStrategy` to `_TEXT_REGISTRY` in `acquire/stage.py`

**New audio strategy** (e.g. direct web audio):
1. Create `acquire/strategies/audio/web_audio.py` implementing `AudioAcquireStrategy`
2. Add `"web_audio": WebAudioStrategy` to `_AUDIO_REGISTRY` in `acquire/stage.py`

No other files need to change.

## Dependencies

| Package | Purpose |
|---------|---------|
| `yt-dlp` | YouTube audio download |
| `ffmpeg` | Audio conversion to 16kHz mono WAV |
| `trafilatura` | Web article scraping |
| `fasttext` | Language identification |
| `huggingface-hub` | fastText model download |
| `python-slugify` | URL generation from video titles |
| `pyyaml` | Pipeline config parsing |
