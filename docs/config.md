# Config Format

Each YAML config file targets one dataset source collection. Pass it to the pipeline with `--config`.

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

    - audio:
        strategy: youtube_videos
        urls:
          - https://www.youtube.com/watch?v=...
      text:
        strategy: video_of_audio_url          # OCR text pages displayed in the video

  output_dir: data/acquire
  language: kmr_Latn          # FastText language code — prefix-matched (kmr matches kmr_Latn, kmr_Arab)
  min_lang_confidence: 0.60   # Optional, defaults to 0.60
```

## Audio strategies

| Strategy | Config keys | Description |
|----------|------------|-------------|
| `youtube_playlist` | `playlist_url` | All videos from a YouTube playlist |
| `youtube_videos` | `urls` (list) | Explicit YouTube video URLs; pass a single-item list for one video |

## Text strategies

| Strategy | Config keys | Description |
|----------|------------|-------------|
| `web_scrape` | `base_url`, `endpoint_method`, `endpoint_method_fallbacks` (optional) | Scrapes article text via [trafilatura](https://trafilatura.readthedocs.io) |
| `video_of_audio_url` | _(none)_ | Extracts on-screen text from the audio item's YouTube video using frame-by-frame OCR (PaddleOCR). Use when the audio source is a video that displays its transcript as text pages. Requires the audio strategy to provide a `url` field on each item (e.g. `youtube_videos`). |

### Endpoint methods

| Method | URL produced | Notes |
|--------|-------------|-------|
| `slugify-audio-name` | `{base_url}/{slugify(video_title)}/` | Slugifies the full title |
| `slugify-after-slash` | `{base_url}/{slugify(part_after_slash)}/` | For titles like `"Author / Column"` — takes text after ` / ` |

### Fallback chain

`endpoint_method_fallbacks` is an ordered list tried only when the primary returns no content. A fallback whose URL cannot be built (e.g. `slugify-after-slash` with no ` / ` in the title) is silently skipped with a log message.

## Debugging and testing

`configs/debug.yml` is a minimal config with one source per strategy type and single items each. Output goes to `dataset/debug` so it does not touch the real dataset.

```bash
python -m kurdish_kurmanji_voice_dataset_pipeline --config configs/debug.yml
```
