# Acquire Stage

## Behaviour

For each source the stage:

1. Fetches item metadata (cached to `items_cache_<source_id>.json` after first run)
2. Skips items whose `id` was already processed by an earlier source (cross-source deduplication)
3. Fetches text using the configured text strategy (web scrape, video OCR, etc.)
4. Validates language with [fastText](https://fasttext.cc/docs/en/language-identification.html) using the `language` and `min_lang_confidence` values from config
5. Downloads audio via `yt-dlp`, converts to **16kHz mono WAV** via `ffmpeg`
6. Saves the text file and appends a record to `metadata_<source_id>.jsonl`

The fastText model (`facebook/fasttext-language-identification`) is loaded once as a singleton and reused across all sources.

## Output layout

```
data/acquire/
  audio/                              # 16kHz mono WAV files (all sources, flat)
  text/                               # UTF-8 transcription files (all sources, flat)
  metadata_<source_id>.jsonl          # One JSON record per audio–text pair, per source
  items_cache_<source_id>.json        # Cached playlist metadata, per source
```

## Output format

### `metadata_<source_id>.jsonl`

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
