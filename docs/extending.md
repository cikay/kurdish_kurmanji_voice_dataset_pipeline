# Extending the Pipeline

## Adding a new text strategy

1. Create `acquire/strategies/text/<name>.py` implementing `TextAcquireStrategy`:
   - `from_config(cls, cfg) -> Self` — instantiate from the YAML config block
   - `fetch(self, hint) -> dict | None` — return `{title, author, text, source_url}` or `None`
2. Add `"<name>": YourClass` to `_TEXT_REGISTRY` in `acquire/stage.py`

## Adding a new audio strategy

1. Create `acquire/strategies/audio/<name>.py` implementing `AudioAcquireStrategy`:
   - `from_config(cls, cfg) -> Self` — instantiate from the YAML config block
   - `source_id: str` property — unique, filesystem-safe identifier used as part of output filenames
   - `items(self, cache_path) -> list[dict]` — return items with at minimum `id` and `title`; persist to `cache_path`
   - `download(self, item, audio_dir, cookies_file) -> Path | None` — return path to 16kHz mono WAV or `None`
2. Add `"<name>": YourClass` to `_AUDIO_REGISTRY` in `acquire/stage.py`

No other files need to change.

## Adding a new endpoint method (web_scrape)

1. Add the method name to `_ENDPOINT_METHODS` in `acquire/strategies/text/web_scrape.py`
2. Add a branch to `_build_url()` that returns the URL string or `None` if the method is not applicable to the given hint

The method can then be used as `endpoint_method` or inside `endpoint_method_fallbacks` in any config.
