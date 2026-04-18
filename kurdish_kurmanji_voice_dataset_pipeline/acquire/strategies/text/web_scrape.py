import json

import trafilatura
from slugify import slugify

from .base import TextAcquireStrategy

_ENDPOINT_METHODS = {"slugify-audio-name", "slugify-after-slash"}


def _build_url(base_url: str, method: str, hint: dict) -> str | None:
    title = hint["title"]
    if method == "slugify-audio-name":
        return f"{base_url.rstrip('/')}/{slugify(title)}/"
    if method == "slugify-after-slash":
        if " / " not in title:
            return None
        after_slash = title.split(" / ", maxsplit=1)[1]
        return f"{base_url.rstrip('/')}/{slugify(after_slash)}/"
    raise ValueError(f"Unknown endpoint_method: {method!r}")


def _scrape(url: str) -> dict | None:
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


class WebScrapeTextStrategy(TextAcquireStrategy):
    def __init__(
        self,
        base_url: str,
        endpoint_method: str,
        endpoint_method_fallbacks: list[str] | None = None,
    ) -> None:
        all_methods = [endpoint_method] + (endpoint_method_fallbacks or [])
        unknown = [m for m in all_methods if m not in _ENDPOINT_METHODS]
        if unknown:
            raise ValueError(
                f"Unknown endpoint_method(s): {unknown}. "
                f"Available: {sorted(_ENDPOINT_METHODS)}"
            )
        self.base_url = base_url
        self.endpoint_method = endpoint_method
        self.endpoint_method_fallbacks: list[str] = endpoint_method_fallbacks or []

    @classmethod
    def from_config(cls, cfg: dict) -> "WebScrapeTextStrategy":
        return cls(
            base_url=cfg["base_url"],
            endpoint_method=cfg["endpoint_method"],
            endpoint_method_fallbacks=cfg.get("endpoint_method_fallbacks"),
        )

    def fetch(self, hint: dict) -> dict | None:
        _, result = self._fetch(self.endpoint_method, hint)
        if result is not None:
            return result

        if not self.endpoint_method_fallbacks:
            return None

        print(f"  🔁 Primary failed, trying {len(self.endpoint_method_fallbacks)} fallback(s)...")
        for method in self.endpoint_method_fallbacks:
            applicable, result = self._fetch(method, hint)
            if not applicable:
                print(f"  ⏭️  Fallback {method!r} not applicable for: {hint['title']!r}")
                continue
            if result is not None:
                print(f"  ✅ Fallback succeeded with method: {method!r} → {result['source_url']}")
                return result
            print(f"  ❌ Fallback {method!r} failed")

        print(f"  ❌ All fallbacks exhausted, no text found for: {hint['title']!r}")
        return None

    def _fetch(self, method: str, hint: dict) -> tuple[bool, dict | None]:
        url = _build_url(self.base_url, method, hint)
        if url is None:
            return False, None
        return True, _scrape(url)
