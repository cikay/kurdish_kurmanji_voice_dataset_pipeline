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

### Endpoint methods

| Method | URL produced | Notes |
|--------|-------------|-------|
| `slugify-audio-name` | `{base_url}/{slugify(video_title)}/` | Slugifies the full title |
| `slugify-after-slash` | `{base_url}/{slugify(part_after_slash)}/` | For titles like `"Author / Column"` — takes text after ` / ` |

### Fallback chain

`endpoint_method_fallbacks` is an ordered list tried only when the primary returns no content. A fallback whose URL cannot be built (e.g. `slugify-after-slash` with no ` / ` in the title) is silently skipped with a log message.
