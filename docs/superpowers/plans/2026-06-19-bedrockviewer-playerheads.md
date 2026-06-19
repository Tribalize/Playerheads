# BedrockViewer Playerheads Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first standalone `Tribalize/Playerheads` Python generator that uses BedrockViewer to create a Bedrock `.mcaddon` with player head items, placeable blocks, and opt-in wandering trader trades.

**Architecture:** Use a small Python package under `playerheads/` with one public CLI wrapper, `build_playerheads.py`. Keep BedrockViewer networking, head config parsing, texture processing, manifest/UUID handling, pack generation, trader table generation, and archive packaging in separate modules with unit tests around each boundary.

**Tech Stack:** Python 3.12, standard-library `argparse`, `json`, `uuid`, `zipfile`, `unittest`, plus `requests` and `Pillow`.

---

## File Structure

- Create `build_playerheads.py`: thin CLI entrypoint that calls `playerheads.cli.main`.
- Create `playerheads/__init__.py`: package marker and version export.
- Create `playerheads/heads.py`: parse comma-separated names and `heads.json`.
- Create `playerheads/bedrockviewer.py`: resolve gamertags through BedrockViewer JSON and download skin PNG bytes.
- Create `playerheads/textures.py`: validate skin images, save full block textures, and generate face icons.
- Create `playerheads/ids.py`: load or create stable manifest UUIDs.
- Create `playerheads/manifests.py`: build linked BP/RP manifests.
- Create `playerheads/trader.py`: build optional wandering trader trade table.
- Create `playerheads/pack.py`: generate pack folders, per-head JSON files, scripts, registries, recipes, texture atlas files, language file, pack icons, and `.mcaddon`.
- Create `playerheads/cli.py`: parse CLI flags and orchestrate the build.
- Create `heads.json`: default player list seeded with `PPTribalize`.
- Create `version.json`: default `[1, 0, 0]`.
- Create `playerheads_ids.json`: persisted UUID seed for the repo.
- Create `requirements.txt`: `requests` and `Pillow`.
- Create `.gitignore`: generated packs, dist, caches.
- Create `.github/workflows/build-addon.yml`: manual build workflow.
- Create `README.md`: usage, inputs, BedrockViewer source, trader option.
- Create tests under `tests/`: focused `unittest` coverage with no live network dependency.

## Task 1: Project Scaffold And Static Defaults

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `heads.json`
- Create: `version.json`
- Create: `playerheads/__init__.py`
- Create: `build_playerheads.py`
- Test: `tests/test_project_scaffold.py`

- [ ] **Step 1: Write scaffold tests**

Create `tests/test_project_scaffold.py`:

```python
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectScaffoldTests(unittest.TestCase):
    def test_default_heads_file_contains_pptribalize(self):
        data = json.loads((ROOT / "heads.json").read_text(encoding="utf-8"))
        self.assertIn("heads", data)
        self.assertIn("PPTribalize", data["heads"])

    def test_default_version_is_semver_triplet(self):
        data = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
        self.assertEqual(data, [1, 0, 0])

    def test_cli_wrapper_imports(self):
        wrapper = (ROOT / "build_playerheads.py").read_text(encoding="utf-8")
        self.assertIn("from playerheads.cli import main", wrapper)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run scaffold tests to verify they fail**

Run: `python -m unittest tests.test_project_scaffold -v`

Expected: fail because `heads.json`, `version.json`, and `build_playerheads.py` do not exist yet.

- [ ] **Step 3: Add scaffold files**

Create `requirements.txt`:

```text
Pillow>=10.0.0
requests>=2.31.0
```

Create `.gitignore`:

```gitignore
__pycache__/
*.pyc
.pytest_cache/
BPH_BP/
BPH_RP/
Playerheads_BP/
Playerheads_RP/
dist/
*.mcaddon
```

Create `heads.json`:

```json
{
  "heads": [
    "PPTribalize"
  ]
}
```

Create `version.json`:

```json
[1, 0, 0]
```

Create `playerheads/__init__.py`:

```python
"""Playerheads Bedrock add-on generator."""

__version__ = "1.0.0"
```

Create `build_playerheads.py`:

```python
from playerheads.cli import main


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run scaffold tests to verify they pass**

Run: `python -m unittest tests.test_project_scaffold -v`

Expected: all tests pass.

- [ ] **Step 5: Commit scaffold**

```powershell
git add .gitignore requirements.txt heads.json version.json playerheads/__init__.py build_playerheads.py tests/test_project_scaffold.py
git commit -m "Add Playerheads project scaffold"
```

## Task 2: Head Selection Parser

**Files:**
- Create: `playerheads/heads.py`
- Test: `tests/test_heads.py`

- [ ] **Step 1: Write parser tests**

Create `tests/test_heads.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from playerheads.heads import Head, heads_from_names, load_heads_file, slugify


class HeadParserTests(unittest.TestCase):
    def test_slugify_lowercases_and_replaces_spaces(self):
        self.assertEqual(slugify("UKM Quantus"), "ukm_quantus")

    def test_heads_from_names(self):
        heads = heads_from_names("PPTribalize, UKM Quantus\nLuckyCroi")
        self.assertEqual([head.name for head in heads], ["PPTribalize", "UKM Quantus", "LuckyCroi"])
        self.assertEqual(heads[1].slug, "ukm_quantus")
        self.assertEqual(heads[1].display_name, "UKM Quantus")
        self.assertIsNone(heads[1].model)

    def test_load_heads_file_strings_and_objects(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "heads.json"
            path.write_text(
                json.dumps(
                    {
                        "heads": [
                            "PPTribalize",
                            {
                                "name": "Other Player",
                                "display_name": "Other Display",
                                "model": "head"
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            heads = load_heads_file(path)

        self.assertEqual(heads[0], Head(name="PPTribalize", display_name="PPTribalize", model=None))
        self.assertEqual(heads[1], Head(name="Other Player", display_name="Other Display", model="head"))

    def test_rejects_empty_head_name(self):
        with self.assertRaises(ValueError):
            heads_from_names("PPTribalize,,   ")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run parser tests to verify they fail**

Run: `python -m unittest tests.test_heads -v`

Expected: fail with `ModuleNotFoundError: No module named 'playerheads.heads'`.

- [ ] **Step 3: Implement head parsing**

Create `playerheads/heads.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Iterable


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
    raw_parts = re.split(r"[,\n]+", names or "")
    if any(part == "" for part in raw_parts[1:-1]):
        raise ValueError("Empty head name found in comma-separated input.")
    heads = [_head_from_entry(part) for part in raw_parts if part.strip()]
    if not heads:
        raise ValueError("No heads selected.")
    return heads


def normalize_heads_data(data) -> list[Head]:
    if isinstance(data, dict) and "heads" in data:
        data = data["heads"]
    if isinstance(data, dict):
        data = [{"name": name, **(value if isinstance(value, dict) else {"model": value})} for name, value in data.items()]
    if not isinstance(data, list):
        raise ValueError("Heads file must contain a list, object, or object with a heads list.")
    heads = [_head_from_entry(entry) for entry in data]
    if not heads:
        raise ValueError("Heads file did not contain any heads.")
    return heads


def load_heads_file(path: str | Path) -> list[Head]:
    return normalize_heads_data(json.loads(Path(path).read_text(encoding="utf-8")))
```

- [ ] **Step 4: Run parser tests to verify they pass**

Run: `python -m unittest tests.test_heads -v`

Expected: all tests pass.

- [ ] **Step 5: Commit parser**

```powershell
git add playerheads/heads.py tests/test_heads.py
git commit -m "Add head selection parser"
```

## Task 3: BedrockViewer Client

**Files:**
- Create: `playerheads/bedrockviewer.py`
- Test: `tests/test_bedrockviewer.py`

- [ ] **Step 1: Write BedrockViewer client tests**

Create `tests/test_bedrockviewer.py`:

```python
import unittest

from playerheads.bedrockviewer import BedrockViewerClient, Profile


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, content=b"", headers=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.content = content
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        return self.responses.pop(0)


class BedrockViewerClientTests(unittest.TestCase):
    def test_resolves_profile_json(self):
        session = FakeSession([
            FakeResponse(json_data={"Gamertag": "PPTribalize", "XUID": "2535407405283318", "skin": True})
        ])
        client = BedrockViewerClient(session=session)

        profile = client.fetch_profile("PPTribalize")

        self.assertEqual(profile, Profile(gamertag="PPTribalize", xuid="2535407405283318", has_skin=True))
        self.assertEqual(session.calls[0][0], "https://bedrockviewer.com/profile/PPTribalize/json")

    def test_download_skin_url_uses_xuid(self):
        self.assertEqual(
            BedrockViewerClient.skin_download_url("2535407405283318"),
            "https://bedrockviewer.com/download-skin/2535407405283318",
        )

    def test_download_skin_requires_png_response(self):
        session = FakeSession([
            FakeResponse(content=b"not html", headers={"Content-Type": "image/png"})
        ])
        client = BedrockViewerClient(session=session)

        content = client.download_skin("2535407405283318")

        self.assertEqual(content, b"not html")

    def test_missing_xuid_raises_value_error(self):
        session = FakeSession([FakeResponse(json_data={"Gamertag": "NoSkin"})])
        client = BedrockViewerClient(session=session)

        with self.assertRaises(ValueError):
            client.fetch_profile("NoSkin")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run BedrockViewer tests to verify they fail**

Run: `python -m unittest tests.test_bedrockviewer -v`

Expected: fail with `ModuleNotFoundError: No module named 'playerheads.bedrockviewer'`.

- [ ] **Step 3: Implement BedrockViewer client**

Create `playerheads/bedrockviewer.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

import requests


PROFILE_URL = "https://bedrockviewer.com/profile/{gamertag}/json"
SKIN_DOWNLOAD_URL = "https://bedrockviewer.com/download-skin/{xuid}"


@dataclass(frozen=True)
class Profile:
    gamertag: str
    xuid: str
    has_skin: bool


class BedrockViewerClient:
    def __init__(self, session=None, timeout: int = 20):
        self.session = session or requests.Session()
        self.timeout = timeout

    @staticmethod
    def profile_url(gamertag: str) -> str:
        return PROFILE_URL.format(gamertag=gamertag)

    @staticmethod
    def skin_download_url(xuid: str) -> str:
        return SKIN_DOWNLOAD_URL.format(xuid=xuid)

    def fetch_profile(self, gamertag: str) -> Profile:
        url = self.profile_url(gamertag)
        response = self.session.get(url, timeout=self.timeout)
        if response.status_code != 200:
            raise ValueError(f"BedrockViewer profile request failed for {gamertag}: HTTP {response.status_code} at {url}")
        data = response.json()
        xuid = str(data.get("XUID") or "").strip()
        if not xuid:
            keys = ", ".join(sorted(str(key) for key in data.keys()))
            raise ValueError(f"BedrockViewer profile for {gamertag} did not include XUID. Response keys: {keys}")
        resolved_name = str(data.get("Gamertag") or gamertag)
        return Profile(gamertag=resolved_name, xuid=xuid, has_skin=bool(data.get("skin")))

    def download_skin(self, xuid: str) -> bytes:
        url = self.skin_download_url(xuid)
        response = self.session.get(url, timeout=self.timeout)
        if response.status_code != 200:
            raise ValueError(f"BedrockViewer skin download failed for XUID {xuid}: HTTP {response.status_code} at {url}")
        content_type = str(response.headers.get("Content-Type", "")).lower()
        if "image/png" not in content_type:
            raise ValueError(f"BedrockViewer skin download for XUID {xuid} did not return image/png. Content-Type: {content_type}")
        return response.content
```

- [ ] **Step 4: Run BedrockViewer tests to verify they pass**

Run: `python -m unittest tests.test_bedrockviewer -v`

Expected: all tests pass.

- [ ] **Step 5: Commit BedrockViewer client**

```powershell
git add playerheads/bedrockviewer.py tests/test_bedrockviewer.py
git commit -m "Add BedrockViewer client"
```

## Task 4: Texture Processing

**Files:**
- Create: `playerheads/textures.py`
- Test: `tests/test_textures.py`

- [ ] **Step 1: Write texture tests**

Create `tests/test_textures.py`:

```python
import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from playerheads.textures import process_skin_bytes


def make_skin_png() -> bytes:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for x in range(8, 16):
        for y in range(8, 16):
            image.putpixel((x, y), (10, 20, 30, 255))
    for x in range(40, 48):
        for y in range(8, 16):
            image.putpixel((x, y), (200, 0, 0, 128))
    buf = io.BytesIO()
    image.save(buf, "PNG")
    return buf.getvalue()


class TextureProcessingTests(unittest.TestCase):
    def test_process_skin_writes_full_texture_and_face_icon(self):
        with tempfile.TemporaryDirectory() as tmp:
            block_path = Path(tmp) / "blocks" / "pptribalize.png"
            item_path = Path(tmp) / "items" / "pptribalize.png"

            process_skin_bytes(make_skin_png(), block_path, item_path)

            block = Image.open(block_path)
            icon = Image.open(item_path)

        self.assertEqual(block.size, (64, 64))
        self.assertEqual(icon.size, (64, 64))
        self.assertNotEqual(icon.getpixel((0, 0)), (10, 20, 30, 255))

    def test_rejects_invalid_image_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                process_skin_bytes(b"not image", Path(tmp) / "block.png", Path(tmp) / "item.png")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run texture tests to verify they fail**

Run: `python -m unittest tests.test_textures -v`

Expected: fail with `ModuleNotFoundError: No module named 'playerheads.textures'`.

- [ ] **Step 3: Implement texture processing**

Create `playerheads/textures.py`:

```python
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image


SKIN_FACE_BASE = (8, 8, 16, 16)
SKIN_FACE_HAT = (40, 8, 48, 16)
OUTPUT_ICON_SIZE = (64, 64)


def load_skin_image(skin_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(skin_bytes)).convert("RGBA")
    except Exception as exc:
        raise ValueError(f"Skin PNG could not be opened: {exc}") from exc
    if image.width != 64 or image.height not in (32, 64):
        raise ValueError(f"Unexpected skin size {image.size}. Expected 64x64 or 64x32.")
    if image.height == 32:
        padded = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        padded.paste(image, (0, 0))
        image = padded
    return image


def build_face_icon(skin_image: Image.Image) -> Image.Image:
    base_face = skin_image.crop(SKIN_FACE_BASE)
    hat_face = skin_image.crop(SKIN_FACE_HAT)
    face_icon = Image.alpha_composite(base_face.copy(), hat_face)
    return face_icon.resize(OUTPUT_ICON_SIZE, Image.Resampling.NEAREST)


def process_skin_bytes(skin_bytes: bytes, block_texture_path: str | Path, item_icon_path: str | Path) -> None:
    skin_image = load_skin_image(skin_bytes)
    block_texture_path = Path(block_texture_path)
    item_icon_path = Path(item_icon_path)
    block_texture_path.parent.mkdir(parents=True, exist_ok=True)
    item_icon_path.parent.mkdir(parents=True, exist_ok=True)
    skin_image.save(block_texture_path, "PNG")
    build_face_icon(skin_image).save(item_icon_path, "PNG")
```

- [ ] **Step 4: Run texture tests to verify they pass**

Run: `python -m unittest tests.test_textures -v`

Expected: all tests pass.

- [ ] **Step 5: Commit texture processing**

```powershell
git add playerheads/textures.py tests/test_textures.py
git commit -m "Add skin texture processing"
```

## Task 5: IDs, Versions, And Linked Manifests

**Files:**
- Create: `playerheads/ids.py`
- Create: `playerheads/manifests.py`
- Test: `tests/test_manifests.py`

- [ ] **Step 1: Write manifest tests**

Create `tests/test_manifests.py`:

```python
import tempfile
import unittest
from pathlib import Path

from playerheads.ids import UUID_KEYS, load_or_create_ids
from playerheads.manifests import build_bp_manifest, build_rp_manifest


class ManifestTests(unittest.TestCase):
    def test_load_or_create_ids_persists_required_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "playerheads_ids.json"
            ids = load_or_create_ids(path)
            loaded = load_or_create_ids(path)

        self.assertEqual(set(ids), set(UUID_KEYS))
        self.assertEqual(ids, loaded)

    def test_manifests_link_behavior_and_resource_packs(self):
        ids = {
            "rp_header": "11111111-1111-4111-8111-111111111111",
            "rp_module": "22222222-2222-4222-8222-222222222222",
            "bp_header": "33333333-3333-4333-8333-333333333333",
            "bp_module": "44444444-4444-4444-8444-444444444444",
            "bp_script": "55555555-5555-4555-8555-555555555555",
        }

        rp = build_rp_manifest(ids, [1, 0, 0])
        bp = build_bp_manifest(ids, [1, 0, 0])

        self.assertEqual(rp["header"]["name"], "Playerheads_RP")
        self.assertEqual(bp["header"]["name"], "Playerheads")
        self.assertTrue(any(dep.get("uuid") == ids["rp_header"] for dep in bp["dependencies"]))
        self.assertTrue(any(dep.get("uuid") == ids["bp_header"] for dep in rp["dependencies"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run manifest tests to verify they fail**

Run: `python -m unittest tests.test_manifests -v`

Expected: fail with missing `playerheads.ids` and `playerheads.manifests`.

- [ ] **Step 3: Implement IDs and manifests**

Create `playerheads/ids.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
import uuid


UUID_KEYS = ("rp_header", "rp_module", "bp_header", "bp_module", "bp_script")


def load_or_create_ids(path: str | Path) -> dict[str, str]:
    path = Path(path)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if all(key in data for key in UUID_KEYS):
            return {key: str(data[key]) for key in UUID_KEYS}
    data = {key: str(uuid.uuid4()) for key in UUID_KEYS}
    path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
    return data
```

Create `playerheads/manifests.py`:

```python
from __future__ import annotations


ENGINE_VERSION = [1, 26, 30]
SERVER_MODULE_VERSION = "2.8.0"


def build_rp_manifest(ids: dict[str, str], version: list[int]) -> dict:
    return {
        "format_version": 2,
        "header": {
            "name": "Playerheads_RP",
            "description": "BedrockViewer-powered player head resources.",
            "uuid": ids["rp_header"],
            "version": version,
            "min_engine_version": ENGINE_VERSION,
        },
        "capabilities": ["pbr"],
        "modules": [
            {"type": "resources", "uuid": ids["rp_module"], "version": version}
        ],
        "dependencies": [
            {"uuid": ids["bp_header"], "version": version}
        ],
    }


def build_bp_manifest(ids: dict[str, str], version: list[int]) -> dict:
    return {
        "format_version": 2,
        "header": {
            "name": "Playerheads",
            "description": "BedrockViewer-powered player head behavior pack.",
            "uuid": ids["bp_header"],
            "version": version,
            "min_engine_version": ENGINE_VERSION,
        },
        "modules": [
            {"type": "data", "uuid": ids["bp_module"], "version": version},
            {
                "type": "script",
                "language": "javascript",
                "uuid": ids["bp_script"],
                "version": version,
                "entry": "scripts/main.js",
            },
        ],
        "dependencies": [
            {"module_name": "@minecraft/server", "version": SERVER_MODULE_VERSION},
            {"uuid": ids["rp_header"], "version": version},
        ],
    }
```

- [ ] **Step 4: Run manifest tests to verify they pass**

Run: `python -m unittest tests.test_manifests -v`

Expected: all tests pass.

- [ ] **Step 5: Commit IDs and manifests**

```powershell
git add playerheads/ids.py playerheads/manifests.py tests/test_manifests.py
git commit -m "Add pack IDs and manifests"
```

## Task 6: Pack Generation Core

**Files:**
- Create: `playerheads/pack.py`
- Test: `tests/test_pack.py`

- [ ] **Step 1: Write pack generation tests**

Create `tests/test_pack.py`:

```python
import tempfile
import unittest
import zipfile
from pathlib import Path

from playerheads.heads import Head
from playerheads.pack import PackBuilder, missing_texture_paths


IDS = {
    "rp_header": "11111111-1111-4111-8111-111111111111",
    "rp_module": "22222222-2222-4222-8222-222222222222",
    "bp_header": "33333333-3333-4333-8333-333333333333",
    "bp_module": "44444444-4444-4444-8444-444444444444",
    "bp_script": "55555555-5555-4555-8555-555555555555",
}


class PackGenerationTests(unittest.TestCase):
    def test_writes_core_pack_files_for_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder = PackBuilder(root, IDS, [1, 0, 0])
            builder.initialize()
            builder.add_head(Head("PPTribalize", "PPTribalize"))
            builder.finish(include_trader_trades=False)

            self.assertTrue((root / "Playerheads_BP" / "manifest.json").is_file())
            self.assertTrue((root / "Playerheads_RP" / "manifest.json").is_file())
            self.assertTrue((root / "Playerheads_BP" / "items" / "pptribalize_head.json").is_file())
            self.assertTrue((root / "Playerheads_BP" / "blocks" / "pptribalize_head.json").is_file())
            self.assertTrue((root / "Playerheads_RP" / "texts" / "en_US.lang").read_text(encoding="utf-8").find("PPTribalize's Head") >= 0)
            self.assertFalse((root / "Playerheads_BP" / "trading").exists())

    def test_missing_texture_paths_reports_block_and_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = missing_texture_paths(Path(tmp) / "Playerheads_RP", [Head("PPTribalize", "PPTribalize")])

        joined = "\n".join(str(path).replace("\\", "/") for path in paths)
        self.assertIn("textures/blocks/skulls/pptribalize.png", joined)
        self.assertIn("textures/items/skulls/pptribalize.png", joined)

    def test_mcaddon_root_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder = PackBuilder(root, IDS, [1, 0, 0])
            builder.initialize()
            builder.add_head(Head("PPTribalize", "PPTribalize"))
            builder.finish(include_trader_trades=False)
            output = root / "dist" / "Playerheads-v1.0.0.mcaddon"
            builder.build_mcaddon(output)

            with zipfile.ZipFile(output) as zf:
                names = zf.namelist()

        self.assertIn("Playerheads_BP/manifest.json", names)
        self.assertIn("Playerheads_RP/manifest.json", names)
        self.assertFalse(any(name.startswith("behavior_packs/") for name in names))
        self.assertFalse(any(name.startswith("resource_packs/") for name in names))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run pack tests to verify they fail**

Run: `python -m unittest tests.test_pack -v`

Expected: fail with `ModuleNotFoundError: No module named 'playerheads.pack'`.

- [ ] **Step 3: Implement pack generation core**

Create `playerheads/pack.py` with these public functions and class:

```python
from __future__ import annotations

import json
from pathlib import Path
import shutil
import zipfile

from PIL import Image

from .heads import Head
from .manifests import build_bp_manifest, build_rp_manifest
from .trader import write_trade_table


BP_NAME = "Playerheads_BP"
RP_NAME = "Playerheads_RP"
NAMESPACE = "bph"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")


def missing_texture_paths(rp_dir: Path, heads: list[Head]) -> list[Path]:
    missing = []
    for head in heads:
        for rel in (
            Path("textures") / "blocks" / "skulls" / f"{head.slug}.png",
            Path("textures") / "items" / "skulls" / f"{head.slug}.png",
        ):
            path = rp_dir / rel
            if not path.is_file():
                missing.append(path)
    return missing


class PackBuilder:
    def __init__(self, root: str | Path, ids: dict[str, str], version: list[int]):
        self.root = Path(root)
        self.ids = ids
        self.version = version
        self.bp_dir = self.root / BP_NAME
        self.rp_dir = self.root / RP_NAME
        self.heads: list[Head] = []

    def initialize(self) -> None:
        for directory in (self.bp_dir, self.rp_dir):
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True)
        write_json(self.bp_dir / "manifest.json", build_bp_manifest(self.ids, self.version))
        write_json(self.rp_dir / "manifest.json", build_rp_manifest(self.ids, self.version))
        write_json(self.bp_dir / "loot_tables" / "empty.json", {"pools": []})
        (self.rp_dir / "texts").mkdir(parents=True, exist_ok=True)
        (self.rp_dir / "texts" / "languages.json").write_text(json.dumps(["en_US"], indent=4) + "\n", encoding="utf-8")

    def add_head(self, head: Head) -> None:
        self.heads.append(head)
        slug = head.slug
        item_id = f"{NAMESPACE}:{slug}_head"
        block_id = f"{NAMESPACE}:{slug}_head_block"
        write_json(self.bp_dir / "items" / f"{slug}_head.json", self._bp_item(item_id, block_id, head))
        write_json(self.bp_dir / "blocks" / f"{slug}_head.json", self._bp_block(block_id, head))
        write_json(self.rp_dir / "items" / f"{slug}_head.json", self._rp_item(item_id, slug, head))
        write_json(self.rp_dir / "attachables" / f"{slug}_head.json", self._attachable(item_id, slug))
        write_json(self.bp_dir / "recipes" / f"{slug}_toBlock.json", self._recipe(item_id, f"{NAMESPACE}:{slug}_head_block_item"))
        write_json(self.bp_dir / "recipes" / f"{slug}_toHead.json", self._recipe(f"{NAMESPACE}:{slug}_head_block_item", item_id))
        self._write_geometry(slug)

    def finish(self, include_trader_trades: bool) -> None:
        self._write_scripts()
        self._write_lang()
        self._write_blocks_json()
        self._write_terrain_texture()
        self._write_item_texture()
        self._write_texture_sets()
        self._write_pack_icons()
        if include_trader_trades:
            write_trade_table(self.bp_dir, self.heads)

    def build_mcaddon(self, output_path: str | Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for pack_dir, prefix in ((self.bp_dir, BP_NAME), (self.rp_dir, RP_NAME)):
                for path in pack_dir.rglob("*"):
                    if path.is_file():
                        zf.write(path, f"{prefix}/{path.relative_to(pack_dir).as_posix()}")
```

Then complete the private helper methods in the same file:

```python
    def _bp_item(self, item_id: str, block_id: str, head: Head) -> dict:
        return {
            "format_version": "1.20.80",
            "minecraft:item": {
                "description": {"identifier": item_id, "menu_category": {"category": "items", "group": "itemGroup.name.player_heads"}},
                "components": {
                    "minecraft:display_name": {"value": f"item.{item_id}"},
                    "minecraft:icon": {"texture": f"{head.slug}_head"},
                    "minecraft:max_stack_size": 1,
                    "minecraft:wearable": {"slot": "slot.armor.head"},
                    "minecraft:block_placer": {"block": block_id},
                },
            },
        }

    def _bp_block(self, block_id: str, head: Head) -> dict:
        return {
            "format_version": "1.20.80",
            "minecraft:block": {
                "description": {"identifier": block_id, "menu_category": {"category": "construction"}},
                "components": {
                    "minecraft:display_name": f"tile.{block_id}.name",
                    "minecraft:geometry": f"geometry.{head.slug}_head",
                    "minecraft:material_instances": {"*": {"texture": f"{head.slug}_head", "render_method": "alpha_test"}},
                    "minecraft:loot": "loot_tables/empty.json",
                    "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.8},
                    "minecraft:collision_box": {"origin": [-4, 0, -4], "size": [8, 8, 8]},
                    "minecraft:selection_box": {"origin": [-4, 0, -4], "size": [8, 8, 8]},
                },
            },
        }

    def _rp_item(self, item_id: str, slug: str, head: Head) -> dict:
        return {
            "format_version": "1.10.0",
            "minecraft:item": {
                "description": {
                    "identifier": item_id,
                    "category": "Equipment",
                },
                "components": {
                    "minecraft:icon": f"{slug}_head",
                },
            },
        }

    def _attachable(self, item_id: str, slug: str) -> dict:
        return {
            "format_version": "1.10.0",
            "minecraft:attachable": {
                "description": {
                    "identifier": item_id,
                    "materials": {"default": "armor", "enchanted": "armor_enchanted"},
                    "textures": {"default": f"textures/blocks/skulls/{slug}"},
                    "geometry": {"default": f"geometry.{slug}_head_attachable"},
                    "render_controllers": ["controller.render.armor"],
                    "scripts": {"parent_setup": "variable.helmet_layer_visible = 0.0;"},
                }
            },
        }

    def _recipe(self, source_item: str, result_item: str) -> dict:
        return {
            "format_version": "1.20.10",
            "minecraft:recipe_shapeless": {
                "description": {"identifier": f"{source_item.replace(':', '_')}_convert"},
                "tags": ["crafting_table"],
                "ingredients": [{"item": source_item}],
                "result": {"item": result_item, "count": 1},
            },
        }

    def _write_geometry(self, slug: str) -> None:
        block_geo = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {"identifier": f"geometry.{slug}_head", "texture_width": 64, "texture_height": 64},
                    "bones": [{"name": "head", "pivot": [0, 0, 0], "cubes": [{"origin": [-4, 0, -4], "size": [8, 8, 8], "uv": [0, 0]}]}],
                }
            ],
        }
        attachable_geo = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {"identifier": f"geometry.{slug}_head_attachable", "texture_width": 64, "texture_height": 64},
                    "bones": [{"name": "head", "pivot": [0, 24, 0], "cubes": [{"origin": [-4, 24, -4], "size": [8, 8, 8], "uv": [0, 0], "inflate": 0.5}]}],
                }
            ],
        }
        write_json(self.rp_dir / "models" / "blocks" / f"{slug}_head.geo.json", block_geo)
        write_json(self.rp_dir / "models" / "entity" / f"{slug}_head_attachable.geo.json", attachable_geo)
```

Finish registries and support files:

```python
    def _write_scripts(self) -> None:
        entries = ",\n".join(f'    ["{NAMESPACE}:{head.slug}_head", "{NAMESPACE}:{head.slug}_head_block"]' for head in self.heads)
        content = f"""import {{ world, ItemStack }} from "@minecraft/server";

const headArray = [
{entries}
];

world.afterEvents.entityDie.subscribe((event) => {{
    const deadEntity = event.deadEntity;
    if (deadEntity.typeId !== "minecraft:player") return;
    const slug = deadEntity.name.toLowerCase().replace(/ /g, "_");
    const entry = headArray.find((head) => head[0] === `bph:${{slug}}_head`);
    if (!entry) return;
    deadEntity.dimension.spawnItem(new ItemStack(entry[0], 1), deadEntity.location);
}});
"""
        path = self.bp_dir / "scripts" / "main.js"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_lang(self) -> None:
        lines = ["## Playerheads language file", ""]
        for head in self.heads:
            lines.append(f"tile.{NAMESPACE}:{head.slug}_head_block.name={head.display_name}'s Head")
            lines.append(f"item.{NAMESPACE}:{head.slug}_head={head.display_name}'s Head")
            lines.append("")
        lines.append("itemGroup.name.player_heads=Player Heads")
        (self.rp_dir / "texts" / "en_US.lang").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_blocks_json(self) -> None:
        data = {"format_version": [1, 1, 0]}
        for head in self.heads:
            data[f"{NAMESPACE}:{head.slug}_head_block"] = {"sound": "stone"}
        write_json(self.rp_dir / "blocks.json", data)

    def _write_terrain_texture(self) -> None:
        data = {"resource_pack_name": "Playerheads", "texture_name": "atlas.terrain", "padding": 8, "num_mip_levels": 4, "texture_data": {}}
        for head in self.heads:
            data["texture_data"][f"{head.slug}_head"] = {"textures": f"textures/blocks/skulls/{head.slug}"}
        write_json(self.rp_dir / "textures" / "terrain_texture.json", data)

    def _write_item_texture(self) -> None:
        data = {"resource_pack_name": "Playerheads", "texture_name": "atlas.items", "texture_data": {}}
        for head in self.heads:
            data["texture_data"][f"{head.slug}_head"] = {"textures": f"textures/items/skulls/{head.slug}"}
        write_json(self.rp_dir / "textures" / "item_texture.json", data)

    def _write_texture_sets(self) -> None:
        for folder in (self.rp_dir / "textures" / "blocks" / "skulls", self.rp_dir / "textures" / "items" / "skulls"):
            folder.mkdir(parents=True, exist_ok=True)
            for png in folder.glob("*.png"):
                write_json(png.with_suffix(".texture_set.json"), {"format_version": "1.21.30", "minecraft:texture_set": {"color": png.stem, "metalness_emissive_roughness": [0, 0, 255]}})

    def _write_pack_icons(self) -> None:
        for pack_dir, color in ((self.bp_dir, (60, 80, 180, 255)), (self.rp_dir, (30, 160, 100, 255))):
            image = Image.new("RGBA", (512, 512), color)
            image.save(pack_dir / "pack_icon.png", "PNG")
```

- [ ] **Step 4: Run pack tests to verify they fail only on missing trader module**

Run: `python -m unittest tests.test_pack -v`

Expected: fail with `ModuleNotFoundError: No module named 'playerheads.trader'`.

- [ ] **Step 5: Create a temporary trader module stub**

Create `playerheads/trader.py`:

```python
from pathlib import Path


def write_trade_table(bp_dir: str | Path, heads) -> None:
    return None
```

- [ ] **Step 6: Run pack tests to verify they pass for trader-disabled generation**

Run: `python -m unittest tests.test_pack -v`

Expected: all tests pass because the tested path uses `include_trader_trades=False`.

- [ ] **Step 7: Commit pack generation core**

```powershell
git add playerheads/pack.py playerheads/trader.py tests/test_pack.py
git commit -m "Add core pack generation"
```

## Task 7: Trader Trade Table

**Files:**
- Modify: `playerheads/trader.py`
- Test: `tests/test_trader.py`
- Modify: `tests/test_pack.py`

- [ ] **Step 1: Write trader tests**

Create `tests/test_trader.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from playerheads.heads import Head
from playerheads.trader import build_trade_table, write_trade_table


class TraderTests(unittest.TestCase):
    def test_trade_table_includes_all_selected_heads(self):
        heads = [Head("PPTribalize", "PPTribalize"), Head("UKM Quantus", "UKM Quantus")]
        table = build_trade_table(heads)
        groups = table["tiers"][0]["groups"]
        head_group = groups[-1]

        self.assertEqual(head_group["num_to_select"], 2)
        gives = [trade["gives"][0]["item"] for trade in head_group["trades"]]
        self.assertEqual(gives, ["bph:pptribalize_head", "bph:ukm_quantus_head"])

    def test_write_trade_table_uses_vanilla_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            bp_dir = Path(tmp) / "Playerheads_BP"
            write_trade_table(bp_dir, [Head("PPTribalize", "PPTribalize")])
            path = bp_dir / "trading" / "economy_trades" / "wandering_trader_trades.json"
            data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(data["tiers"][0]["groups"][-1]["trades"][0]["gives"][0]["item"], "bph:pptribalize_head")


if __name__ == "__main__":
    unittest.main()
```

Add this method to `tests/test_pack.py`:

```python
    def test_trader_enabled_writes_trade_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder = PackBuilder(root, IDS, [1, 0, 0])
            builder.initialize()
            builder.add_head(Head("PPTribalize", "PPTribalize"))
            builder.finish(include_trader_trades=True)

            self.assertTrue((root / "Playerheads_BP" / "trading" / "economy_trades" / "wandering_trader_trades.json").is_file())
```

- [ ] **Step 2: Run trader tests to verify they fail**

Run: `python -m unittest tests.test_trader tests.test_pack -v`

Expected: fail because `playerheads.trader.write_trade_table` raises `NotImplementedError`.

- [ ] **Step 3: Implement trader generation**

Replace `playerheads/trader.py` with:

```python
from __future__ import annotations

import copy
import json
from pathlib import Path

from .heads import Head


TRADER_MAX_USES = 3
TRADER_PRICE_ITEM = "minecraft:diamond_block"
TRADER_PRICE_QTY = 1

VANILLA_GROUP1 = {
    "num_to_select": 5,
    "trades": [
        {"max_uses": 5, "wants": [{"item": "minecraft:emerald", "quantity": 2}], "gives": [{"item": "minecraft:sea_pickle"}]},
        {"max_uses": 5, "wants": [{"item": "minecraft:emerald", "quantity": 4}], "gives": [{"item": "minecraft:slime_ball"}]},
        {"max_uses": 5, "wants": [{"item": "minecraft:emerald", "quantity": 2}], "gives": [{"item": "minecraft:glowstone"}]},
        {"max_uses": 5, "wants": [{"item": "minecraft:emerald", "quantity": 5}], "gives": [{"item": "minecraft:nautilus_shell"}]},
        {"max_uses": 12, "wants": [{"item": "minecraft:emerald", "quantity": 1}], "gives": [{"item": "minecraft:wheat_seeds"}]},
    ],
}

VANILLA_GROUP2 = {
    "num_to_select": 1,
    "trades": [
        {"max_uses": 4, "wants": [{"item": "minecraft:emerald", "quantity": 5}], "gives": [{"item": "minecraft:bucket:4"}]},
        {"max_uses": 4, "wants": [{"item": "minecraft:emerald", "quantity": 5}], "gives": [{"item": "minecraft:bucket:5"}]},
        {"max_uses": 6, "wants": [{"item": "minecraft:emerald", "quantity": 3}], "gives": [{"item": "minecraft:packed_ice"}]},
        {"max_uses": 6, "wants": [{"item": "minecraft:emerald", "quantity": 6}], "gives": [{"item": "minecraft:blue_ice"}]},
    ],
}


def build_trade_table(heads: list[Head]) -> dict:
    head_trades = []
    for head in heads:
        head_trades.append(
            {
                "wants": [{"item": TRADER_PRICE_ITEM, "quantity": TRADER_PRICE_QTY}],
                "gives": [{"item": f"bph:{head.slug}_head"}],
                "max_uses": TRADER_MAX_USES,
            }
        )
    return {
        "tiers": [
            {
                "groups": [
                    copy.deepcopy(VANILLA_GROUP1),
                    copy.deepcopy(VANILLA_GROUP2),
                    {"num_to_select": len(head_trades), "trades": head_trades},
                ]
            }
        ]
    }


def write_trade_table(bp_dir: str | Path, heads: list[Head]) -> None:
    path = Path(bp_dir) / "trading" / "economy_trades" / "wandering_trader_trades.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_trade_table(heads), indent=4) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run trader and pack tests to verify they pass**

Run: `python -m unittest tests.test_trader tests.test_pack -v`

Expected: all tests pass.

- [ ] **Step 5: Commit trader generation**

```powershell
git add playerheads/trader.py tests/test_trader.py tests/test_pack.py
git commit -m "Add opt-in wandering trader trades"
```

## Task 8: CLI Build Orchestration

**Files:**
- Create: `playerheads/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write CLI tests**

Create `tests/test_cli.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from playerheads.cli import parse_args, parse_version, resolve_heads


class CliTests(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(parse_version("1.2.3"), [1, 2, 3])

    def test_include_trader_trades_defaults_false(self):
        args = parse_args(["--heads", "PPTribalize", "--no-version-bump"])
        self.assertFalse(args.include_trader_trades)

    def test_include_trader_trades_true_when_flag_passed(self):
        args = parse_args(["--heads", "PPTribalize", "--include-trader-trades"])
        self.assertTrue(args.include_trader_trades)

    def test_resolve_heads_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "heads.json"
            path.write_text(json.dumps({"heads": ["PPTribalize"]}), encoding="utf-8")
            args = parse_args(["--heads-file", str(path)])
            heads = resolve_heads(args)

        self.assertEqual(heads[0].name, "PPTribalize")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run CLI tests to verify they fail**

Run: `python -m unittest tests.test_cli -v`

Expected: fail with `ModuleNotFoundError: No module named 'playerheads.cli'`.

- [ ] **Step 3: Implement CLI orchestration**

Create `playerheads/cli.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .bedrockviewer import BedrockViewerClient
from .heads import heads_from_names, load_heads_file
from .ids import load_or_create_ids
from .pack import PackBuilder, missing_texture_paths
from .textures import process_skin_bytes


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HEADS_FILE = ROOT / "heads.json"
DEFAULT_VERSION_FILE = ROOT / "version.json"
DEFAULT_IDS_FILE = ROOT / "playerheads_ids.json"


def parse_version(value: str) -> list[int]:
    parts = str(value).strip().replace(",", ".").split(".")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Version must have three parts, such as 1.0.0.")
    try:
        return [int(part) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Version parts must be integers.") from exc


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build the Playerheads Bedrock .mcaddon from BedrockViewer skins.")
    parser.add_argument("--heads", help="Comma-separated Bedrock gamertags. Overrides --heads-file.")
    parser.add_argument("--heads-file", default=str(DEFAULT_HEADS_FILE), help="JSON file containing Bedrock gamertags.")
    parser.add_argument("--version", type=parse_version, help="Version to stamp into manifests, such as 1.0.0.")
    parser.add_argument("--no-version-bump", action="store_true", help="Do not change version.json.")
    parser.add_argument("--output", help="Destination .mcaddon path.")
    parser.add_argument("--require-textures", action="store_true", help="Fail if any skin texture cannot be generated.")
    parser.add_argument("--include-trader-trades", action="store_true", help="Generate wandering trader trades for all selected heads.")
    return parser.parse_args(argv)


def load_version(path: Path = DEFAULT_VERSION_FILE) -> list[int]:
    return [int(part) for part in json.loads(path.read_text(encoding="utf-8"))]


def save_version(version: list[int], path: Path = DEFAULT_VERSION_FILE) -> None:
    path.write_text(json.dumps(version) + "\n", encoding="utf-8")


def resolve_heads(args) -> list:
    if args.heads:
        return heads_from_names(args.heads)
    return load_heads_file(args.heads_file)


def main(argv=None) -> None:
    args = parse_args(argv)
    heads = resolve_heads(args)
    version = args.version or load_version()
    if not args.no_version_bump:
        save_version(version)

    root = ROOT
    ids = load_or_create_ids(DEFAULT_IDS_FILE)
    builder = PackBuilder(root, ids, version)
    builder.initialize()
    client = BedrockViewerClient()

    for head in heads:
        profile = client.fetch_profile(head.name)
        if not profile.has_skin:
            print(f"Warning: BedrockViewer reports skin=false for {head.name}.", file=sys.stderr)
        skin_bytes = client.download_skin(profile.xuid)
        process_skin_bytes(
            skin_bytes,
            builder.rp_dir / "textures" / "blocks" / "skulls" / f"{head.slug}.png",
            builder.rp_dir / "textures" / "items" / "skulls" / f"{head.slug}.png",
        )
        builder.add_head(head)

    missing = missing_texture_paths(builder.rp_dir, heads)
    if args.require_textures and missing:
        for path in missing:
            print(f"Missing texture: {path}", file=sys.stderr)
        raise SystemExit(1)

    builder.finish(include_trader_trades=args.include_trader_trades)

    output = Path(args.output) if args.output else root / "dist" / f"Playerheads-v{'.'.join(str(part) for part in version)}.mcaddon"
    builder.build_mcaddon(output)
    print(f"Built {output}")
```

- [ ] **Step 4: Run CLI tests to verify they pass**

Run: `python -m unittest tests.test_cli -v`

Expected: all tests pass.

- [ ] **Step 5: Run full unit suite**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 6: Commit CLI**

```powershell
git add playerheads/cli.py tests/test_cli.py
git commit -m "Add Playerheads build CLI"
```

## Task 9: GitHub Actions And README

**Files:**
- Create: `.github/workflows/build-addon.yml`
- Create: `README.md`
- Test: `tests/test_docs_and_workflow.py`

- [ ] **Step 1: Write docs and workflow tests**

Create `tests/test_docs_and_workflow.py`:

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocsWorkflowTests(unittest.TestCase):
    def test_readme_documents_bedrockviewer_and_trader_default(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("BedrockViewer", text)
        self.assertIn("--include-trader-trades", text)
        self.assertIn("disabled by default", text)

    def test_workflow_has_false_trader_default(self):
        text = (ROOT / ".github" / "workflows" / "build-addon.yml").read_text(encoding="utf-8")
        self.assertIn("include_trader_trades", text)
        self.assertIn("default: false", text)
        self.assertIn("--include-trader-trades", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run docs workflow tests to verify they fail**

Run: `python -m unittest tests.test_docs_and_workflow -v`

Expected: fail because `README.md` and workflow file do not exist.

- [ ] **Step 3: Add README**

Create `README.md`:

```markdown
# Playerheads

Playerheads is a Minecraft Bedrock add-on generator for custom player head items and placeable head blocks. It uses BedrockViewer profile data and skin downloads, so the generated heads are based on Bedrock player skins.

## Skin Source

For each gamertag, the generator reads:

- `https://bedrockviewer.com/profile/<gamertag>/json`
- `https://bedrockviewer.com/download-skin/<xuid>`

The downloaded skin is saved as the block texture, and the face is cropped into a 64x64 item icon.

## Build Locally

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Build from `heads.json`:

```powershell
python build_playerheads.py --heads-file heads.json --version 1.0.0 --no-version-bump --require-textures --output dist/Playerheads-v1.0.0.mcaddon
```

Build with one-off names:

```powershell
python build_playerheads.py --heads "PPTribalize,UKM Quantus" --version 1.0.0 --no-version-bump --require-textures --output dist/Playerheads-custom.mcaddon
```

Wandering trader trades are disabled by default. Turn them on for all selected heads:

```powershell
python build_playerheads.py --heads-file heads.json --include-trader-trades
```

## Configure Heads

```json
{
  "heads": [
    "PPTribalize",
    {
      "name": "UKM Quantus",
      "display_name": "UKM Quantus",
      "model": "head"
    }
  ]
}
```

## Output

The generated `.mcaddon` contains pack folders directly at the archive root:

- `Playerheads_BP/`
- `Playerheads_RP/`

Do not wrap those folders inside `behavior_packs/` or `resource_packs/`.

## Tests

```powershell
python -m unittest discover -s tests -v
```
```

- [ ] **Step 4: Add GitHub Actions workflow**

Create `.github/workflows/build-addon.yml`:

```yaml
name: Build Playerheads Add-on

on:
  workflow_dispatch:
    inputs:
      player_names:
        description: "Optional comma-separated Bedrock gamertags. Leave empty to use heads.json."
        required: false
        type: string
      heads_file:
        description: "Heads JSON file to use when player_names is empty."
        required: true
        default: "heads.json"
        type: string
      version:
        description: "Add-on version to stamp into manifests and the artifact name."
        required: true
        default: "1.0.0"
        type: string
      include_trader_trades:
        description: "Set true to add wandering trader trades for all selected heads."
        required: true
        default: false
        type: boolean

jobs:
  build:
    name: Build .mcaddon
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: python -m pip install -r requirements.txt

      - name: Run tests
        run: python -m unittest discover -s tests -v

      - name: Build add-on
        env:
          PLAYER_NAMES: ${{ inputs.player_names }}
          HEADS_FILE: ${{ inputs.heads_file }}
          ADDON_VERSION: ${{ inputs.version }}
          INCLUDE_TRADER_TRADES: ${{ inputs.include_trader_trades }}
        run: |
          mkdir -p dist
          EXTRA_ARGS=""
          if [ "$INCLUDE_TRADER_TRADES" = "true" ]; then
            EXTRA_ARGS="--include-trader-trades"
          fi
          if [ -n "$PLAYER_NAMES" ]; then
            python build_playerheads.py \
              --heads "$PLAYER_NAMES" \
              --version "$ADDON_VERSION" \
              --no-version-bump \
              --require-textures \
              --output "dist/Playerheads-v${ADDON_VERSION}.mcaddon" \
              $EXTRA_ARGS
          else
            python build_playerheads.py \
              --heads-file "$HEADS_FILE" \
              --version "$ADDON_VERSION" \
              --no-version-bump \
              --require-textures \
              --output "dist/Playerheads-v${ADDON_VERSION}.mcaddon" \
              $EXTRA_ARGS
          fi

      - name: Upload .mcaddon artifact
        uses: actions/upload-artifact@v4
        with:
          name: Playerheads-v${{ inputs.version }}
          path: dist/*.mcaddon
          if-no-files-found: error
```

- [ ] **Step 5: Run docs workflow tests to verify they pass**

Run: `python -m unittest tests.test_docs_and_workflow -v`

Expected: all tests pass.

- [ ] **Step 6: Commit docs and workflow**

```powershell
git add README.md .github/workflows/build-addon.yml tests/test_docs_and_workflow.py
git commit -m "Add docs and build workflow"
```

## Task 10: End-To-End Verification

**Files:**
- Modify only if verification reveals a defect in earlier tasks.

- [ ] **Step 1: Install dependencies**

Run: `python -m pip install -r requirements.txt`

Expected: `Pillow` and `requests` are installed or already satisfied.

- [ ] **Step 2: Run the full unit suite**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 3: Run a live BedrockViewer build for PPTribalize without trader trades**

Run:

```powershell
python build_playerheads.py --heads "PPTribalize" --version 1.0.0 --no-version-bump --require-textures --output dist/Playerheads-v1.0.0.mcaddon
```

Expected:

- command exits with code `0`.
- `dist/Playerheads-v1.0.0.mcaddon` exists.
- archive contains `Playerheads_BP/manifest.json`.
- archive contains `Playerheads_RP/manifest.json`.
- archive does not contain `Playerheads_BP/trading/economy_trades/wandering_trader_trades.json`.

- [ ] **Step 4: Run a live BedrockViewer build for PPTribalize with trader trades**

Run:

```powershell
python build_playerheads.py --heads "PPTribalize" --version 1.0.0 --no-version-bump --require-textures --include-trader-trades --output dist/Playerheads-v1.0.0-trader.mcaddon
```

Expected:

- command exits with code `0`.
- `dist/Playerheads-v1.0.0-trader.mcaddon` exists.
- archive contains `Playerheads_BP/trading/economy_trades/wandering_trader_trades.json`.
- trade table contains `bph:pptribalize_head`.

- [ ] **Step 5: Inspect archive root layout**

Run:

```powershell
python -c "import zipfile; p='dist/Playerheads-v1.0.0.mcaddon'; z=zipfile.ZipFile(p); names=z.namelist(); print(any(n.startswith('Playerheads_BP/') for n in names)); print(any(n.startswith('Playerheads_RP/') for n in names)); print(any(n.startswith('behavior_packs/') or n.startswith('resource_packs/') for n in names))"
```

Expected output:

```text
True
True
False
```

- [ ] **Step 6: Commit final verification fixes**

If Step 1 through Step 5 pass without file edits, skip this commit. If fixes were needed:

```powershell
git add .
git commit -m "Fix Playerheads build verification"
```

- [ ] **Step 7: Prepare publish branch**

Run:

```powershell
git status --short
git log --oneline --max-count=8
```

Expected:

- `git status --short` is empty or only shows generated files that are ignored.
- recent commits show scaffold, parser, BedrockViewer client, textures, manifests, pack generation, trader, CLI, docs/workflow.

## Self-Review

- Spec coverage: repository separation, BedrockViewer-only source, whole-build trader option default false, Actions `include_trader_trades: true`, BP/RP root archive layout, CLI inputs, tests, and README/workflow are all mapped to tasks.
- Placeholder scan: no task relies on an undefined future step or unspecified behavior.
- Type consistency: `Head`, `Profile`, `PackBuilder`, `BedrockViewerClient`, and CLI flag names are consistent across tasks.
