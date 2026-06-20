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
