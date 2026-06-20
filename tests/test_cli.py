import argparse
import json
import tempfile
import unittest
from pathlib import Path

from playerheads.cli import parse_args, parse_version, resolve_heads


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


if __name__ == "__main__":
    unittest.main()
