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
                                "model": "head",
                            },
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
