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
HEAD_UV = {
    "north": {"uv": [8, 8], "uv_size": [8, 8]},
    "south": {"uv": [24, 8], "uv_size": [8, 8]},
    "east": {"uv": [16, 8], "uv_size": [8, 8]},
    "west": {"uv": [0, 8], "uv_size": [8, 8]},
    "up": {"uv": [8, 0], "uv_size": [8, 8]},
    "down": {"uv": [16, 0], "uv_size": [8, 8]},
}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")


def missing_texture_paths(rp_dir: Path, heads: list[Head]) -> list[Path]:
    missing = []
    for head in heads:
        for rel_path in (
            Path("textures") / "blocks" / "skulls" / f"{head.slug}.png",
            Path("textures") / "items" / "skulls" / f"{head.slug}.png",
        ):
            path = rp_dir / rel_path
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

        texts_dir = self.rp_dir / "texts"
        texts_dir.mkdir(parents=True, exist_ok=True)
        (texts_dir / "languages.json").write_text(json.dumps(["en_US"], indent=4) + "\n", encoding="utf-8")

    def add_head(self, head: Head) -> None:
        self.heads.append(head)
        slug = head.slug
        item_id = f"{NAMESPACE}:{slug}_head"
        block_id = f"{NAMESPACE}:{slug}_head_block"

        write_json(self.bp_dir / "items" / f"{slug}_head.json", self._bp_item(item_id, block_id, head))
        write_json(self.bp_dir / "blocks" / f"{slug}_head.json", self._bp_block(block_id, head))
        write_json(self.rp_dir / "items" / f"{slug}_head.json", self._rp_item(item_id, slug))
        write_json(self.rp_dir / "attachables" / f"{slug}_head.json", self._attachable(item_id, slug))
        write_json(self.bp_dir / "recipes" / f"{slug}_toBlock.json", self._recipe(item_id, block_id))
        write_json(self.bp_dir / "recipes" / f"{slug}_toHead.json", self._recipe(block_id, item_id))
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

    def _bp_item(self, item_id: str, block_id: str, head: Head) -> dict:
        return {
            "format_version": "1.20.80",
            "minecraft:item": {
                "description": {
                    "identifier": item_id,
                    "menu_category": {"category": "items", "group": "itemGroup.name.player_heads"},
                },
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
                "description": {
                    "identifier": block_id,
                    "menu_category": {"category": "construction"},
                    "traits": {
                        "minecraft:placement_position": {
                            "enabled_states": ["minecraft:block_face"],
                        }
                    },
                    "states": {
                        "bph:head_rotation": {
                            "values": {"min": 0, "max": 15},
                        }
                    },
                },
                "components": {
                    "minecraft:display_name": f"tile.{block_id}.name",
                    "minecraft:geometry": {
                        "identifier": f"geometry.{head.slug}_head",
                        "bone_visibility": {
                            "up_0": (
                                "q.block_state('minecraft:block_face') == 'up' && "
                                "math.mod(q.block_state('bph:head_rotation'), 4) == 0"
                            ),
                            "up_22_5": (
                                "q.block_state('minecraft:block_face') == 'up' && "
                                "math.mod(q.block_state('bph:head_rotation'), 4) == 1"
                            ),
                            "up_45": (
                                "q.block_state('minecraft:block_face') == 'up' && "
                                "math.mod(q.block_state('bph:head_rotation'), 4) == 2"
                            ),
                            "up_67_5": (
                                "q.block_state('minecraft:block_face') == 'up' && "
                                "math.mod(q.block_state('bph:head_rotation'), 4) == 3"
                            ),
                            "side": "q.block_state('minecraft:block_face') != 'up'",
                        },
                    },
                    "minecraft:material_instances": {
                        "*": {"texture": f"{head.slug}_head", "render_method": "alpha_test"}
                    },
                    "minecraft:loot": "loot_tables/empty.json",
                    "minecraft:placement_filter": {"conditions": [{"allowed_faces": ["up", "side"]}]},
                    "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.8},
                    "minecraft:collision_box": {"origin": [-4, 0, -4], "size": [8, 8, 8]},
                    "minecraft:selection_box": {"origin": [-4, 0, -4], "size": [8, 8, 8]},
                },
                "permutations": self._placement_permutations(),
            },
        }

    def _rp_item(self, item_id: str, slug: str) -> dict:
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

    def _placement_permutations(self) -> list[dict]:
        side_box = {"origin": [-4, 3, 0], "size": [8, 8, 8]}
        floor_box = {"origin": [-4, 0, -4], "size": [8, 8, 8]}
        return [
            {
                "condition": "q.block_state('minecraft:block_face') == 'east'",
                "components": {
                    "minecraft:transformation": {"rotation": [0, 180, 0]},
                    "minecraft:collision_box": side_box,
                    "minecraft:selection_box": side_box,
                },
            },
            {
                "condition": "q.block_state('minecraft:block_face') == 'south'",
                "components": {
                    "minecraft:transformation": {"rotation": [0, 90, 0]},
                    "minecraft:collision_box": side_box,
                    "minecraft:selection_box": side_box,
                },
            },
            {
                "condition": "q.block_state('minecraft:block_face') == 'west'",
                "components": {
                    "minecraft:transformation": {"rotation": [0, 0, 0]},
                    "minecraft:collision_box": side_box,
                    "minecraft:selection_box": side_box,
                },
            },
            {
                "condition": "q.block_state('minecraft:block_face') == 'north'",
                "components": {
                    "minecraft:transformation": {"rotation": [0, 270, 0]},
                    "minecraft:collision_box": side_box,
                    "minecraft:selection_box": side_box,
                },
            },
            {
                "condition": (
                    "q.block_state('minecraft:block_face') == 'up' && "
                    "q.block_state('bph:head_rotation') >= 4 && q.block_state('bph:head_rotation') <= 7"
                ),
                "components": {
                    "minecraft:transformation": {"rotation": [0, 90, 0]},
                    "minecraft:collision_box": floor_box,
                    "minecraft:selection_box": floor_box,
                },
            },
            {
                "condition": (
                    "q.block_state('minecraft:block_face') == 'up' && "
                    "q.block_state('bph:head_rotation') >= 8 && q.block_state('bph:head_rotation') <= 11"
                ),
                "components": {
                    "minecraft:transformation": {"rotation": [0, 180, 0]},
                    "minecraft:collision_box": floor_box,
                    "minecraft:selection_box": floor_box,
                },
            },
            {
                "condition": (
                    "q.block_state('minecraft:block_face') == 'up' && "
                    "q.block_state('bph:head_rotation') >= 12"
                ),
                "components": {
                    "minecraft:transformation": {"rotation": [0, 270, 0]},
                    "minecraft:collision_box": floor_box,
                    "minecraft:selection_box": floor_box,
                },
            },
        ]

    def _write_geometry(self, slug: str) -> None:
        block_geo = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": f"geometry.{slug}_head",
                        "texture_width": 64,
                        "texture_height": 64,
                    },
                    "bones": [
                        {
                            "name": "up_0",
                            "pivot": [0, 0, 0],
                            "cubes": [{"origin": [-4, 0, -4], "size": [8, 8, 8], "uv": HEAD_UV}],
                        },
                        {
                            "name": "up_22_5",
                            "pivot": [0, 0, 0],
                            "rotation": [0, 22.5, 0],
                            "cubes": [{"origin": [-4, 0, -4], "size": [8, 8, 8], "uv": HEAD_UV}],
                        },
                        {
                            "name": "up_45",
                            "pivot": [0, 0, 0],
                            "rotation": [0, 45, 0],
                            "cubes": [{"origin": [-4, 0, -4], "size": [8, 8, 8], "uv": HEAD_UV}],
                        },
                        {
                            "name": "up_67_5",
                            "pivot": [0, 0, 0],
                            "rotation": [0, 67.5, 0],
                            "cubes": [{"origin": [-4, 0, -4], "size": [8, 8, 8], "uv": HEAD_UV}],
                        },
                        {
                            "name": "side",
                            "pivot": [0, 7, 4],
                            "cubes": [{"origin": [-4, 3, 0], "size": [8, 8, 8], "uv": HEAD_UV}],
                        },
                    ],
                }
            ],
        }
        attachable_geo = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": f"geometry.{slug}_head_attachable",
                        "texture_width": 64,
                        "texture_height": 64,
                    },
                    "bones": [
                        {
                            "name": "head",
                            "pivot": [0, 24, 0],
                            "cubes": [
                                {
                                    "origin": [-4, 24, -4],
                                    "size": [8, 8, 8],
                                    "uv": HEAD_UV,
                                    "inflate": 0.5,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        write_json(self.rp_dir / "models" / "blocks" / f"{slug}_head.geo.json", block_geo)
        write_json(self.rp_dir / "models" / "entity" / f"{slug}_head_attachable.geo.json", attachable_geo)

    def _write_scripts(self) -> None:
        entries = ",\n".join(
            f'    ["{NAMESPACE}:{head.slug}_head", "{NAMESPACE}:{head.slug}_head_block"]' for head in self.heads
        )
        content = f"""import {{ world, ItemStack }} from "@minecraft/server";

const headArray = [
{entries}
];

world.afterEvents.playerPlaceBlock.subscribe((event) => {{
    const {{ player, block }} = event;
    if (!block.typeId.startsWith("{NAMESPACE}:") || !block.typeId.endsWith("_head_block")) return;
    const yaw = ((player.getRotation().y % 360) + 360) % 360;
    const rot = Math.round(yaw / 22.5) % 16;
    block.setPermutation(block.permutation.withState("bph:head_rotation", rot));
}});

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
        data = {
            "resource_pack_name": "Playerheads",
            "texture_name": "atlas.terrain",
            "padding": 8,
            "num_mip_levels": 4,
            "texture_data": {},
        }
        for head in self.heads:
            data["texture_data"][f"{head.slug}_head"] = {"textures": f"textures/blocks/skulls/{head.slug}"}
        write_json(self.rp_dir / "textures" / "terrain_texture.json", data)

    def _write_item_texture(self) -> None:
        data = {"resource_pack_name": "Playerheads", "texture_name": "atlas.items", "texture_data": {}}
        for head in self.heads:
            data["texture_data"][f"{head.slug}_head"] = {"textures": f"textures/items/skulls/{head.slug}"}
        write_json(self.rp_dir / "textures" / "item_texture.json", data)

    def _write_texture_sets(self) -> None:
        for folder in (
            self.rp_dir / "textures" / "blocks" / "skulls",
            self.rp_dir / "textures" / "items" / "skulls",
        ):
            folder.mkdir(parents=True, exist_ok=True)
            for png in folder.glob("*.png"):
                write_json(
                    png.with_suffix(".texture_set.json"),
                    {
                        "format_version": "1.21.30",
                        "minecraft:texture_set": {
                            "color": png.stem,
                            "metalness_emissive_roughness": [0, 0, 255],
                        },
                    },
                )

    def _write_pack_icons(self) -> None:
        for pack_dir, color in ((self.bp_dir, (60, 80, 180, 255)), (self.rp_dir, (30, 160, 100, 255))):
            image = Image.new("RGBA", (512, 512), color)
            image.save(pack_dir / "pack_icon.png", "PNG")
