import json

import trafilatura
from slugify import slugify

from .base import TextAcquireStrategy

_ENDPOINT_METHODS = {"slugify-audio-name"}


class WebScrapeTextStrategy(TextAcquireStrategy):
    def __init__(self, base_url: str, endpoint_method: str) -> None:
        if endpoint_method not in _ENDPOINT_METHODS:
            raise ValueError(
                f"Unknown endpoint_method: {endpoint_method!r}. "
                f"Available: {sorted(_ENDPOINT_METHODS)}"
            )
        self.base_url = base_url
        self.endpoint_method = endpoint_method

    @classmethod
    def from_config(cls, cfg: dict) -> "WebScrapeTextStrategy":
        return cls(
            base_url=cfg["base_url"],
            endpoint_method=cfg["endpoint_method"],
        )

    def _build_url(self, hint: dict) -> str:
        if self.endpoint_method == "slugify-audio-name":
            return f"{self.base_url.rstrip('/')}/{slugify(hint['title'])}/"
        raise ValueError(f"Unhandled endpoint_method: {self.endpoint_method!r}")

    def fetch(self, hint: dict) -> dict | None:
        url = self._build_url(hint)
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                print(f"  ❌ No page at {url}")
                return None

            output_bytes = trafilatura.extract(
                downloaded,
                favor_precision=True,
                output_format="json",
                with_metadata=True,
            )
            if not output_bytes:
                print(f"  ⚠️  No text extracted from {url}")
                return None

            output = json.loads(output_bytes)
            if not output:
                return None

            return {
                "title": output.get("title") or "",
                "author": output.get("author") or "",
                "text": output.get("text") or "",
                "source_url": url,
            }
        except Exception as e:
            print(f"  ❌ Scrape error for {url}: {e}")
            return None
