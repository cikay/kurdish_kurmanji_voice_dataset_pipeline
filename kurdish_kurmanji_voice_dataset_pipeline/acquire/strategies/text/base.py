from abc import ABC, abstractmethod


class TextAcquireStrategy(ABC):
    @classmethod
    @abstractmethod
    def from_config(cls, cfg: dict) -> "TextAcquireStrategy":
        """Instantiate from the YAML source text config block."""
        ...

    @abstractmethod
    def fetch(self, hint: dict) -> dict | None:
        """Fetch text content for one audio item.

        hint: the item dict produced by AudioAcquireStrategy.items().
        Returns {'title': str, 'author': str, 'text': str, 'source_url': str}
        or None on failure.
        """
        ...
