# Kurdish Kurmanji Voice Dataset Pipeline

A modular pipeline for building a Kurdish Kurmanji ASR/TTS voice dataset by pairing audio recordings with their matching transcription text from online sources.

## Overview

The pipeline is config-driven. Each YAML config file defines a set of stages and their sources. Currently implemented:

| Stage | Description |
|-------|-------------|
| `acquire` | Download audio + scrape matching text, validate language, save pairs |

## Project Structure

```
configs/
  config.yml                  # Pipeline config

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
    items_cache_<source_id>.json                 # Cached playlist metadata, per source

docs/
  config.md                        # Config format and strategy reference
  acquire-stage.md                 # Acquire stage behavior and output format
  extending.md                     # How to add new strategies
```

## Quickstart

**Install dependencies:**
```bash
pipenv install
```

**Run a pipeline config:**
```bash
pipenv run python -m kurdish_kurmanji_voice_dataset_pipeline.pipeline \
  --config configs/config.yml

# With YouTube cookies (needed if playlist is age-restricted):
pipenv run python -m kurdish_kurmanji_voice_dataset_pipeline.pipeline \
  --config configs/config.yml \
  --cookies cookies.txt
```

**Requirements:** `ffmpeg` must be available on `PATH`.

## Documentation

- [Config format & strategies](docs/config.md)
- [Acquire stage behavior & output format](docs/acquire-stage.md)
- [Extending the pipeline](docs/extending.md)

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
