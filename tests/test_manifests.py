import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import uuid

from playerheads.ids import UUID_KEYS, load_or_create_ids
from playerheads.manifests import (
    ENGINE_VERSION,
    SERVER_MODULE_VERSION,
    build_bp_manifest,
    build_rp_manifest,
)


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

    def test_load_or_create_ids_rewrites_invalid_uuid_values(self):
        valid_ids = {
            "rp_header": "11111111-1111-4111-8111-111111111111",
            "rp_module": "22222222-2222-4222-8222-222222222222",
            "bp_header": "33333333-3333-4333-8333-333333333333",
            "bp_module": "44444444-4444-4444-8444-444444444444",
            "bp_script": "55555555-5555-4555-8555-555555555555",
        }
        invalid_values = (None, "", 123, "not-a-uuid")

        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "playerheads_ids.json"
                data = dict(valid_ids)
                data["rp_header"] = invalid_value
                path.write_text(json.dumps(data), encoding="utf-8")
                generated = [
                    uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"),
                    uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2"),
                    uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3"),
                    uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa4"),
                    uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa5"),
                ]

                with patch("playerheads.ids.uuid.uuid4", side_effect=generated):
                    ids = load_or_create_ids(path)
                written = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual(ids, {key: str(value) for key, value in zip(UUID_KEYS, generated)})
            self.assertEqual(written, ids)

    def test_load_or_create_ids_normalizes_valid_uuid_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "playerheads_ids.json"
            path.write_text(
                json.dumps(
                    {
                        "rp_header": "{11111111-1111-4111-8111-111111111111}",
                        "rp_module": "22222222222242228222222222222222",
                        "bp_header": "33333333-3333-4333-8333-333333333333",
                        "bp_module": "44444444-4444-4444-8444-444444444444",
                        "bp_script": "55555555-5555-4555-8555-555555555555",
                    }
                ),
                encoding="utf-8",
            )

            ids = load_or_create_ids(path)

        self.assertEqual(
            ids,
            {
                "rp_header": "11111111-1111-4111-8111-111111111111",
                "rp_module": "22222222-2222-4222-8222-222222222222",
                "bp_header": "33333333-3333-4333-8333-333333333333",
                "bp_module": "44444444-4444-4444-8444-444444444444",
                "bp_script": "55555555-5555-4555-8555-555555555555",
            },
        )

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
        self.assertEqual(rp["header"]["min_engine_version"], ENGINE_VERSION)
        self.assertEqual(bp["header"]["min_engine_version"], ENGINE_VERSION)
        self.assertEqual(rp["dependencies"], [{"uuid": ids["bp_header"], "version": [1, 0, 0]}])
        self.assertIn({"module_name": "@minecraft/server", "version": SERVER_MODULE_VERSION}, bp["dependencies"])
        self.assertIn({"uuid": ids["rp_header"], "version": [1, 0, 0]}, bp["dependencies"])

        script_modules = [module for module in bp["modules"] if module["type"] == "script"]
        self.assertEqual(
            script_modules,
            [
                {
                    "type": "script",
                    "language": "javascript",
                    "uuid": ids["bp_script"],
                    "version": [1, 0, 0],
                    "entry": "scripts/main.js",
                }
            ],
        )

    def test_manifests_do_not_share_mutable_version_lists(self):
        ids = {
            "rp_header": "11111111-1111-4111-8111-111111111111",
            "rp_module": "22222222-2222-4222-8222-222222222222",
            "bp_header": "33333333-3333-4333-8333-333333333333",
            "bp_module": "44444444-4444-4444-8444-444444444444",
            "bp_script": "55555555-5555-4555-8555-555555555555",
        }
        version = [1, 0, 0]
        original_engine_version = list(ENGINE_VERSION)

        try:
            rp = build_rp_manifest(ids, version)
            bp = build_bp_manifest(ids, version)
            version[0] = 9
            ENGINE_VERSION[0] = 9

            self.assertEqual(rp["header"]["version"], [1, 0, 0])
            self.assertEqual(rp["header"]["min_engine_version"], [1, 26, 30])
            self.assertEqual(rp["modules"][0]["version"], [1, 0, 0])
            self.assertEqual(rp["dependencies"][0]["version"], [1, 0, 0])
            self.assertEqual(bp["header"]["version"], [1, 0, 0])
            self.assertEqual(bp["header"]["min_engine_version"], [1, 26, 30])
            self.assertEqual(bp["modules"][0]["version"], [1, 0, 0])
            self.assertEqual(bp["modules"][1]["version"], [1, 0, 0])
            self.assertEqual(bp["dependencies"][1]["version"], [1, 0, 0])
        finally:
            ENGINE_VERSION[:] = original_engine_version


if __name__ == "__main__":
    unittest.main()
