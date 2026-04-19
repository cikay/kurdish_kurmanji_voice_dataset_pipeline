import json
import time
from functools import lru_cache
from pathlib import Path

import fasttext
from huggingface_hub import hf_hub_download
from slugify import slugify

from .strategies.audio.base import AudioAcquireStrategy
from .strategies.audio.youtube_playlist import YoutubePlaylistAudioStrategy
from .strategies.audio.youtube_videos import YoutubeVideosAudioStrategy
from .strategies.text.base import TextAcquireStrategy
from .strategies.text.web_scrape import WebScrapeTextStrategy


@lru_cache(maxsize=1)
def _load_fasttext_model() -> fasttext.FastText._FastText:
    model_path = hf_hub_download(
        repo_id="facebook/fasttext-language-identification", filename="model.bin"
    )
    return fasttext.load_model(model_path)


class AcquireStage:
    _DEFAULT_MIN_LANG_CONFIDENCE = 0.60

    # Registry: add new strategies here, no other file needs to change
    _AUDIO_REGISTRY: dict[str, type[AudioAcquireStrategy]] = {
        "youtube_playlist": YoutubePlaylistAudioStrategy,
        "youtube_videos": YoutubeVideosAudioStrategy,
    }

    _TEXT_REGISTRY: dict[str, type[TextAcquireStrategy]] = {
        "web_scrape": WebScrapeTextStrategy,
    }

    def __init__(self, cfg: dict, cookies_file: Path | None = None) -> None:
        self.sources: list[dict] = cfg["sources"]
        self.output_dir = Path(cfg["output_dir"])
        self.cookies_file = cookies_file
        self.language: str = cfg["language"]
        self.min_lang_confidence: float = cfg.get(
            "min_lang_confidence", self._DEFAULT_MIN_LANG_CONFIDENCE
        )

    @classmethod
    def _build_audio_strategy(cls, cfg: dict) -> AudioAcquireStrategy:
        strategy_type = cfg["strategy"]
        strategy_cls = cls._AUDIO_REGISTRY.get(strategy_type)
        if strategy_cls is None:
            raise ValueError(
                f"Unknown audio strategy: {strategy_type!r}. "
                f"Available: {sorted(cls._AUDIO_REGISTRY)}"
            )
        return strategy_cls.from_config(cfg)

    @classmethod
    def _build_text_strategy(cls, cfg: dict) -> TextAcquireStrategy:
        strategy_type = cfg["strategy"]
        strategy_cls = cls._TEXT_REGISTRY.get(strategy_type)
        if strategy_cls is None:
            raise ValueError(
                f"Unknown text strategy: {strategy_type!r}. "
                f"Available: {sorted(cls._TEXT_REGISTRY)}"
            )
        return strategy_cls.from_config(cfg)

    @staticmethod
    def _detect_lang(text: str) -> tuple[str | None, float]:
        normalized = " ".join((text or "").split())
        if not normalized:
            return None, 0.0
        labels, probs = _load_fasttext_model().predict(normalized, k=1)
        if not labels:
            return None, 0.0
        return labels[0].replace("__label__", ""), float(probs[0])

    def run(self) -> None:
        print(f"\n🚀 Acquire: {len(self.sources)} source(s) → {self.output_dir}")

        processed_ids: set[str] = set()

        for i, source_cfg in enumerate(self.sources, 1):
            print(f"\n── Source {i}/{len(self.sources)} ──")

            audio_strategy = self._build_audio_strategy(source_cfg["audio"])
            text_strategy = self._build_text_strategy(source_cfg["text"])

            source_id = audio_strategy.source_id
            audio_dir = self.output_dir / "audio"
            text_dir = self.output_dir / "text"
            cache_path = self.output_dir / f"items_cache_{source_id}.json"
            meta_path = self.output_dir / f"metadata_{source_id}.jsonl"

            audio_dir.mkdir(parents=True, exist_ok=True)
            text_dir.mkdir(parents=True, exist_ok=True)

            items = audio_strategy.items(cache_path)
            if not items:
                print("  ⚠️  No items found, skipping source.")
                continue

            metadata_entries = []
            success = fail = skipped = 0

            for j, item in enumerate(items, 1):
                item_id, title = item["id"], item["title"]
                print(f"\n  [{j}/{len(items)}] {title}")

                if item_id in processed_ids:
                    print(f"  ⏭️  Duplicate {item_id}, skipping")
                    skipped += 1
                    continue

                content = text_strategy.fetch(item)
                if not content:
                    fail += 1
                    continue

                lang, prob = self._detect_lang(content["text"])
                if lang != self.language:
                    print(f"  ⚠️  Language mismatch (expected={self.language}, got={lang}), skipping")
                    fail += 1
                    continue

                if prob < self.min_lang_confidence:
                    print(
                        f"  ⚠️  Language score mismatch (expected={prob:.2f}, got={self.min_lang_confidence:.2f}), skipping"
                    )
                    fail += 1
                    continue

                full_text = "\n".join(
                    part for part in [content["author"], content["title"], content["text"]] if part
                )
                text_path = text_dir / f"{item_id}.txt"
                text_path.write_text(full_text, encoding="utf-8")

                audio_path = audio_strategy.download(item, audio_dir, self.cookies_file)
                if not audio_path:
                    fail += 1
                    continue

                processed_ids.add(item_id)
                print(f"  ✅ Saved: {audio_path.name} | {len(full_text)} chars")

                metadata_entries.append({
                    "id": item_id,
                    "title": content["title"],
                    "author": content["author"],
                    "slug": slugify(title),
                    "audio_file": f"audio/{audio_path.name}",
                    "text_file": f"text/{item_id}.txt",
                    "text_length": len(full_text),
                    "source_url": content.get("source_url", ""),
                    "source_id": source_id,
                })
                success += 1
                time.sleep(1)

            with open(meta_path, "w", encoding="utf-8") as f:
                for entry in metadata_entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            print(
                f"\n  ✅ {success} saved  ❌ {fail} failed  ⏭️  {skipped} duplicates"
                f"\n  📁 {self.output_dir.resolve()}"
            )
