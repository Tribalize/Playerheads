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
