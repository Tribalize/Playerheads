import json
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
            self.assertIn(
                "PPTribalize's Head",
                (root / "Playerheads_RP" / "texts" / "en_US.lang").read_text(encoding="utf-8"),
            )
            self.assertFalse((root / "Playerheads_BP" / "trading").exists())

    def test_missing_texture_paths_reports_block_and_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = missing_texture_paths(Path(tmp) / "Playerheads_RP", [Head("PPTribalize", "PPTribalize")])

        joined = "\n".join(str(path).replace("\\", "/") for path in paths)
        self.assertIn("textures/blocks/skulls/pptribalize.png", joined)
        self.assertIn("textures/items/skulls/pptribalize.png", joined)

    def test_recipes_convert_between_generated_head_and_block_identifiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder = PackBuilder(root, IDS, [1, 0, 0])
            builder.initialize()
            builder.add_head(Head("PPTribalize", "PPTribalize"))
            builder.finish(include_trader_trades=False)

            to_block = json.loads(
                (root / "Playerheads_BP" / "recipes" / "pptribalize_toBlock.json").read_text(encoding="utf-8")
            )["minecraft:recipe_shapeless"]
            to_head = json.loads(
                (root / "Playerheads_BP" / "recipes" / "pptribalize_toHead.json").read_text(encoding="utf-8")
            )["minecraft:recipe_shapeless"]

        self.assertEqual([{"item": "bph:pptribalize_head"}], to_block["ingredients"])
        self.assertEqual({"item": "bph:pptribalize_head_block", "count": 1}, to_block["result"])
        self.assertEqual([{"item": "bph:pptribalize_head_block"}], to_head["ingredients"])
        self.assertEqual({"item": "bph:pptribalize_head", "count": 1}, to_head["result"])

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

    def test_trader_enabled_writes_trade_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder = PackBuilder(root, IDS, [1, 0, 0])
            builder.initialize()
            builder.add_head(Head("PPTribalize", "PPTribalize"))
            builder.finish(include_trader_trades=True)

            self.assertTrue(
                (root / "Playerheads_BP" / "trading" / "economy_trades" / "wandering_trader_trades.json").is_file()
            )

    def test_geometry_maps_full_skin_sheet_head_faces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder = PackBuilder(root, IDS, [1, 0, 0])
            builder.initialize()
            builder.add_head(Head("PPTribalize", "PPTribalize"))

            block_geo = json.loads(
                (root / "Playerheads_RP" / "models" / "blocks" / "pptribalize_head.geo.json").read_text(
                    encoding="utf-8"
                )
            )
            attachable_geo = json.loads(
                (root / "Playerheads_RP" / "models" / "entity" / "pptribalize_head_attachable.geo.json").read_text(
                    encoding="utf-8"
                )
            )

        block_cube = block_geo["minecraft:geometry"][0]["bones"][0]["cubes"][0]
        attachable_cube = attachable_geo["minecraft:geometry"][0]["bones"][0]["cubes"][0]
        expected_uv = {
            "north": {"uv": [8, 8], "uv_size": [8, 8]},
            "south": {"uv": [24, 8], "uv_size": [8, 8]},
            "east": {"uv": [16, 8], "uv_size": [8, 8]},
            "west": {"uv": [0, 8], "uv_size": [8, 8]},
            "up": {"uv": [8, 0], "uv_size": [8, 8]},
            "down": {"uv": [16, 0], "uv_size": [8, 8]},
        }
        self.assertEqual(expected_uv, block_cube["uv"])
        self.assertEqual(expected_uv, attachable_cube["uv"])

    def test_blocks_and_script_support_placement_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder = PackBuilder(root, IDS, [1, 0, 0])
            builder.initialize()
            builder.add_head(Head("PPTribalize", "PPTribalize"))
            builder.finish(include_trader_trades=False)

            block = json.loads(
                (root / "Playerheads_BP" / "blocks" / "pptribalize_head.json").read_text(encoding="utf-8")
            )["minecraft:block"]
            script = (root / "Playerheads_BP" / "scripts" / "main.js").read_text(encoding="utf-8")

        self.assertIn("minecraft:placement_position", block["description"]["traits"])
        self.assertIn("bph:head_rotation", block["description"]["states"])
        self.assertTrue(any("minecraft:block_face') == 'east'" in item["condition"] for item in block["permutations"]))
        rotations_by_condition = {
            item["condition"]: item["components"].get("minecraft:transformation", {}).get("rotation")
            for item in block["permutations"]
        }
        self.assertEqual(
            [0, -90, 0],
            rotations_by_condition["q.block_state('minecraft:block_face') == 'east'"],
        )
        self.assertEqual(
            [0, 180, 0],
            rotations_by_condition["q.block_state('minecraft:block_face') == 'south'"],
        )
        self.assertEqual(
            [0, 90, 0],
            rotations_by_condition["q.block_state('minecraft:block_face') == 'west'"],
        )
        self.assertIsNone(rotations_by_condition["q.block_state('minecraft:block_face') == 'north'"])
        self.assertEqual(
            [0, -90, 0],
            rotations_by_condition[
                "q.block_state('minecraft:block_face') == 'up' && "
                "q.block_state('bph:head_rotation') >= 4 && q.block_state('bph:head_rotation') <= 7"
            ],
        )
        self.assertEqual(
            [0, 180, 0],
            rotations_by_condition[
                "q.block_state('minecraft:block_face') == 'up' && "
                "q.block_state('bph:head_rotation') >= 8 && q.block_state('bph:head_rotation') <= 11"
            ],
        )
        self.assertEqual(
            [0, 90, 0],
            rotations_by_condition[
                "q.block_state('minecraft:block_face') == 'up' && q.block_state('bph:head_rotation') >= 12"
            ],
        )
        self.assertIn("playerPlaceBlock", script)
        self.assertIn('withState("bph:head_rotation", rot)', script)


if __name__ == "__main__":
    unittest.main()
