"""Save and load inverted indexes from disk."""

from __future__ import annotations

import json
from pathlib import Path

from src.indexer import InvertedIndex


def save_index(index: InvertedIndex, path: str | Path) -> None:
    """Write an inverted index to a JSON file."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def load_index(path: str | Path) -> InvertedIndex:
    """Read an inverted index from a JSON file."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return InvertedIndex.from_dict(payload)
