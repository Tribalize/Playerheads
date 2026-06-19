from __future__ import annotations

import json
from pathlib import Path
import uuid


UUID_KEYS = ("rp_header", "rp_module", "bp_header", "bp_module", "bp_script")


def load_or_create_ids(path: str | Path) -> dict[str, str]:
    path = Path(path)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict) and all(key in data for key in UUID_KEYS):
            return {key: str(data[key]) for key in UUID_KEYS}
    data = {key: str(uuid.uuid4()) for key in UUID_KEYS}
    path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
    return data
