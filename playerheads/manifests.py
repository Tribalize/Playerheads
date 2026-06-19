from __future__ import annotations


ENGINE_VERSION = [1, 26, 30]
SERVER_MODULE_VERSION = "2.8.0"


def build_rp_manifest(ids: dict[str, str], version: list[int]) -> dict:
    return {
        "format_version": 2,
        "header": {
            "name": "Playerheads_RP",
            "description": "BedrockViewer-powered player head resources.",
            "uuid": ids["rp_header"],
            "version": version,
            "min_engine_version": ENGINE_VERSION,
        },
        "capabilities": ["pbr"],
        "modules": [
            {"type": "resources", "uuid": ids["rp_module"], "version": version}
        ],
        "dependencies": [
            {"uuid": ids["bp_header"], "version": version}
        ],
    }


def build_bp_manifest(ids: dict[str, str], version: list[int]) -> dict:
    return {
        "format_version": 2,
        "header": {
            "name": "Playerheads",
            "description": "BedrockViewer-powered player head behavior pack.",
            "uuid": ids["bp_header"],
            "version": version,
            "min_engine_version": ENGINE_VERSION,
        },
        "modules": [
            {"type": "data", "uuid": ids["bp_module"], "version": version},
            {
                "type": "script",
                "language": "javascript",
                "uuid": ids["bp_script"],
                "version": version,
                "entry": "scripts/main.js",
            },
        ],
        "dependencies": [
            {"module_name": "@minecraft/server", "version": SERVER_MODULE_VERSION},
            {"uuid": ids["rp_header"], "version": version},
        ],
    }
