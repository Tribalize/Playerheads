from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path


@dataclass(frozen=True)
class Head:
    name: str
    display_name: str
    model: str | None = None

    @property
    def slug(self) -> str:
        return slugify(self.name)


def slugify(name: str) -> str:
    return str(name).strip().lower().replace(" ", "_")


def _head_from_entry(entry) -> Head:
    if isinstance(entry, str):
        name = entry.strip()
        if not name:
            raise ValueError("Head entries must include a non-empty name.")
        return Head(name=name, display_name=name)

    if isinstance(entry, dict):
        name = str(entry.get("name", "")).strip()
        if not name:
            raise ValueError("Head object entries must include a non-empty name.")
        display_name = str(entry.get("display_name") or name).strip()
        model = entry.get("model")
        model = str(model).strip() if model is not None and str(model).strip() else None
        return Head(name=name, display_name=display_name, model=model)

    raise ValueError(f"Unsupported head entry: {entry!r}")


def heads_from_names(names: str) -> list[Head]:
    raw_parts = re.split(r"[,\n]", names or "")
    if any(not part.strip() for part in raw_parts[1:-1]):
        raise ValueError("Empty head name found in comma-separated input.")
    heads = [_head_from_entry(part) for part in raw_parts if part.strip()]
    if not heads:
        raise ValueError("No heads selected.")
    return heads


def normalize_heads_data(data) -> list[Head]:
    if isinstance(data, dict) and "heads" in data:
        data = data["heads"]
    if isinstance(data, dict):
        data = [
            {"name": name, **(value if isinstance(value, dict) else {"model": value})}
            for name, value in data.items()
        ]
    if not isinstance(data, list):
        raise ValueError("Heads file must contain a list, object, or object with a heads list.")
    heads = [_head_from_entry(entry) for entry in data]
    if not heads:
        raise ValueError("Heads file did not contain any heads.")
    return heads


def load_heads_file(path: str | Path) -> list[Head]:
    return normalize_heads_data(json.loads(Path(path).read_text(encoding="utf-8")))
