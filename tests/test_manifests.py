import json
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

    def test_load_or_create_ids_rewrites_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "playerheads_ids.json"
            path.write_text("{", encoding="utf-8")

            ids = load_or_create_ids(path)
            written = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(set(ids), set(UUID_KEYS))
        self.assertEqual(ids, written)

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
