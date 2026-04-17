from abc import ABC, abstractmethod
from pathlib import Path


class AudioAcquireStrategy(ABC):
    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unique, filesystem-safe identifier used as the output subdirectory name."""
        ...

    @classmethod
    @abstractmethod
    def from_config(cls, cfg: dict) -> "AudioAcquireStrategy":
        """Instantiate from the YAML source audio config block."""
        ...

    @abstractmethod
    def items(self, cache_path: Path) -> list[dict]:
        """Return all items for this source.

        Each item must contain at minimum 'id' (str) and 'title' (str).
        Extra fields are forwarded to the paired TextAcquireStrategy as hint.
        Uses cache_path to persist fetched metadata so re-runs skip the network call.
        """
        ...

    @abstractmethod
    def download(self, item: dict, audio_dir: Path, cookies_file: Path | None) -> Path | None:
        """Download audio for one item into audio_dir.

        Returns the path to the produced 16kHz mono WAV, or None on failure.
        """
        ...
