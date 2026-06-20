import argparse
import contextlib
import io
import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from playerheads.cli import main, parse_args, parse_version, resolve_heads


@dataclass(frozen=True)
class FakeProfile:
    gamertag: str
    xuid: str
    has_skin: bool = True


class CliTests(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(parse_version("1.2.3"), [1, 2, 3])

    def test_parse_version_rejects_malformed_values(self):
        for value in ("1.2", "1.2.x", "1.-2.3"):
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_version(value)

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

    def test_main_orchestrates_build_and_saves_version_after_success(self):
        events = []

        class FakeClient:
            def fetch_profile(self, gamertag):
                events.append(("fetch_profile", gamertag))
                return FakeProfile(gamertag=gamertag, xuid="xuid-1")

            def download_skin(self, xuid):
                events.append(("download_skin", xuid))
                return b"skin-bytes"

        class FakeBuilder:
            def __init__(self, root, ids, version):
                self.root = Path(root)
                self.rp_dir = self.root / "Playerheads_RP"
                events.append(("builder_init", self.root, ids, version))

            def initialize(self):
                events.append(("initialize",))

            def add_head(self, head):
                events.append(("add_head", head.name))

            def finish(self, include_trader_trades):
                events.append(("finish", include_trader_trades))

            def build_mcaddon(self, output_path):
                events.append(("build_mcaddon", Path(output_path)))
                events.append(("version_during_build", json.loads(version_file.read_text(encoding="utf-8"))))

        def fake_process_skin(skin_bytes, block_texture_path, item_icon_path):
            events.append(
                (
                    "process_skin",
                    skin_bytes,
                    Path(block_texture_path).as_posix(),
                    Path(item_icon_path).as_posix(),
                )
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version_file = root / "version.json"
            version_file.write_text("[1, 0, 0]\n", encoding="utf-8")
            ids_file = root / "ids.json"

            with contextlib.redirect_stdout(io.StringIO()):
                main(
                    [
                        "--heads",
                        "PPTribalize",
                        "--version",
                        "2.0.0",
                        "--include-trader-trades",
                    ],
                    client_factory=FakeClient,
                    builder_factory=FakeBuilder,
                    process_skin=fake_process_skin,
                    ids_path=ids_file,
                    version_file=version_file,
                    root=root,
                    missing_texture_checker=lambda rp_dir, heads: [],
                )

            saved_version = json.loads(version_file.read_text(encoding="utf-8"))

        self.assertIn(("fetch_profile", "PPTribalize"), events)
        self.assertIn(("download_skin", "xuid-1"), events)
        self.assertIn(("add_head", "PPTribalize"), events)
        self.assertIn(("finish", True), events)
        self.assertIn(("build_mcaddon", root / "dist" / "Playerheads-v2.0.0.mcaddon"), events)
        self.assertIn(("version_during_build", [1, 0, 0]), events)
        self.assertEqual(saved_version, [2, 0, 0])
        process_events = [event for event in events if event[0] == "process_skin"]
        self.assertEqual(process_events[0][1], b"skin-bytes")
        self.assertIn("textures/blocks/skulls/pptribalize.png", process_events[0][2])
        self.assertIn("textures/items/skulls/pptribalize.png", process_events[0][3])

    def test_main_no_version_bump_does_not_save_version(self):
        class FakeClient:
            def fetch_profile(self, gamertag):
                return FakeProfile(gamertag=gamertag, xuid="xuid-1")

            def download_skin(self, xuid):
                return b"skin-bytes"

        class FakeBuilder:
            def __init__(self, root, ids, version):
                self.rp_dir = Path(root) / "Playerheads_RP"

            def initialize(self):
                pass

            def add_head(self, head):
                pass

            def finish(self, include_trader_trades):
                pass

            def build_mcaddon(self, output_path):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version_file = root / "version.json"
            version_file.write_text("[1, 0, 0]\n", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                main(
                    ["--heads", "PPTribalize", "--version", "2.0.0", "--no-version-bump"],
                    client_factory=FakeClient,
                    builder_factory=FakeBuilder,
                    process_skin=lambda *args: None,
                    ids_path=root / "ids.json",
                    version_file=version_file,
                    root=root,
                    missing_texture_checker=lambda rp_dir, heads: [],
                )

            saved_version = json.loads(version_file.read_text(encoding="utf-8"))

        self.assertEqual(saved_version, [1, 0, 0])

    def test_main_failure_does_not_save_version(self):
        class FailingClient:
            def fetch_profile(self, gamertag):
                raise ValueError("temporary fetch failure")

        class FakeBuilder:
            def __init__(self, root, ids, version):
                self.rp_dir = Path(root) / "Playerheads_RP"

            def initialize(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version_file = root / "version.json"
            version_file.write_text("[1, 0, 0]\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                main(
                    ["--heads", "PPTribalize", "--version", "2.0.0"],
                    client_factory=FailingClient,
                    builder_factory=FakeBuilder,
                    ids_path=root / "ids.json",
                    version_file=version_file,
                    root=root,
                )

            saved_version = json.loads(version_file.read_text(encoding="utf-8"))

        self.assertEqual(saved_version, [1, 0, 0])

    def test_main_build_failure_does_not_save_version(self):
        class FakeClient:
            def fetch_profile(self, gamertag):
                return FakeProfile(gamertag=gamertag, xuid="xuid-1")

            def download_skin(self, xuid):
                return b"skin-bytes"

        class FailingBuilder:
            def __init__(self, root, ids, version):
                self.rp_dir = Path(root) / "Playerheads_RP"

            def initialize(self):
                pass

            def add_head(self, head):
                pass

            def finish(self, include_trader_trades):
                pass

            def build_mcaddon(self, output_path):
                raise RuntimeError("build failed")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version_file = root / "version.json"
            version_file.write_text("[1, 0, 0]\n", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                main(
                    ["--heads", "PPTribalize", "--version", "2.0.0"],
                    client_factory=FakeClient,
                    builder_factory=FailingBuilder,
                    process_skin=lambda *args: None,
                    ids_path=root / "ids.json",
                    version_file=version_file,
                    root=root,
                    missing_texture_checker=lambda rp_dir, heads: [],
                )

            saved_version = json.loads(version_file.read_text(encoding="utf-8"))

        self.assertEqual(saved_version, [1, 0, 0])

    def test_main_require_textures_reports_missing_paths(self):
        class FakeClient:
            def fetch_profile(self, gamertag):
                return FakeProfile(gamertag=gamertag, xuid="xuid-1")

            def download_skin(self, xuid):
                return b"skin-bytes"

        class FakeBuilder:
            def __init__(self, root, ids, version):
                self.rp_dir = Path(root) / "Playerheads_RP"

            def initialize(self):
                pass

            def add_head(self, head):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version_file = root / "version.json"
            version_file.write_text("[1, 0, 0]\n", encoding="utf-8")
            missing_path = root / "Playerheads_RP" / "textures" / "blocks" / "skulls" / "pptribalize.png"
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                main(
                    ["--heads", "PPTribalize", "--version", "2.0.0", "--require-textures"],
                    client_factory=FakeClient,
                    builder_factory=FakeBuilder,
                    process_skin=lambda *args: None,
                    ids_path=root / "ids.json",
                    version_file=version_file,
                    root=root,
                    missing_texture_checker=lambda rp_dir, heads: [missing_path],
                )

            saved_version = json.loads(version_file.read_text(encoding="utf-8"))

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("Missing texture:", stderr.getvalue())
        self.assertIn("pptribalize.png", stderr.getvalue())
        self.assertEqual(saved_version, [1, 0, 0])


if __name__ == "__main__":
    unittest.main()
