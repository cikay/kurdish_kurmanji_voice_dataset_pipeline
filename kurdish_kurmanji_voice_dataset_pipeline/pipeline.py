"""Entry point: reads a pipeline YAML config and runs each stage in order.

Usage:
    python -m kurdish_kurmanji_voice_dataset_pipeline.pipeline --config configs/config.yml
    python -m kurdish_kurmanji_voice_dataset_pipeline.pipeline --config configs/config.yml --cookies cookies.txt
"""

import argparse
from pathlib import Path

import yaml

from .acquire.stage import AcquireStage

_STAGE_CLASSES = {
    "acquire": AcquireStage,
}


def main(config_path: str, cookies_file: str | None = None) -> None:
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    stages: list[str] = cfg.get("stages", [])
    cookies = Path(cookies_file) if cookies_file else None

    print(f"Pipeline: {config_path}")
    print(f"Stages  : {stages}")

    for stage in stages:
        stage_cls = _STAGE_CLASSES.get(stage)
        if stage_cls is None:
            print(f"Stage '{stage}' not implemented, skipping.")
            continue
        stage_cls(cfg[stage], cookies_file=cookies).run()

    print("\nPipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kurdish Kurmanji voice dataset pipeline")
    parser.add_argument("--config", required=True, help="Path to pipeline YAML config")
    parser.add_argument("--cookies", default=None, help="Path to cookies.txt for yt-dlp (optional)")
    args = parser.parse_args()
    main(args.config, args.cookies)
