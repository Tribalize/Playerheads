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
