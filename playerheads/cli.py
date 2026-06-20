from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .bedrockviewer import BedrockViewerClient
from .heads import heads_from_names, load_heads_file
from .ids import load_or_create_ids
from .pack import PackBuilder, missing_texture_paths
from .textures import process_skin_bytes


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HEADS_FILE = ROOT / "heads.json"
DEFAULT_VERSION_FILE = ROOT / "version.json"
DEFAULT_IDS_FILE = ROOT / "playerheads_ids.json"


def parse_version(value: str) -> list[int]:
    parts = str(value).strip().replace(",", ".").split(".")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Version must have three parts, such as 1.0.0.")
    try:
        version = [int(part) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Version parts must be integers.") from exc
    if any(part < 0 for part in version):
        raise argparse.ArgumentTypeError("Version parts must be non-negative integers.")
    return version


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build the Playerheads Bedrock .mcaddon from BedrockViewer skins.")
    parser.add_argument("--heads", help="Comma-separated Bedrock gamertags. Overrides --heads-file.")
    parser.add_argument("--heads-file", default=str(DEFAULT_HEADS_FILE), help="JSON file containing Bedrock gamertags.")
    parser.add_argument("--version", type=parse_version, help="Version to stamp into manifests, such as 1.0.0.")
    parser.add_argument("--no-version-bump", action="store_true", help="Do not change version.json.")
    parser.add_argument("--output", help="Destination .mcaddon path.")
    parser.add_argument("--require-textures", action="store_true", help="Fail if any skin texture cannot be generated.")
    parser.add_argument(
        "--include-trader-trades",
        action="store_true",
        help="Generate wandering trader trades for all selected heads.",
    )
    return parser.parse_args(argv)


def load_version(path: Path = DEFAULT_VERSION_FILE) -> list[int]:
    return [int(part) for part in json.loads(path.read_text(encoding="utf-8"))]


def save_version(version: list[int], path: Path = DEFAULT_VERSION_FILE) -> None:
    path.write_text(json.dumps(version) + "\n", encoding="utf-8")


def resolve_heads(args) -> list:
    if args.heads:
        return heads_from_names(args.heads)
    return load_heads_file(args.heads_file)


def main(
    argv=None,
    *,
    client_factory=BedrockViewerClient,
    builder_factory=PackBuilder,
    process_skin=process_skin_bytes,
    ids_path: str | Path = DEFAULT_IDS_FILE,
    version_file: str | Path = DEFAULT_VERSION_FILE,
    root: str | Path = ROOT,
    missing_texture_checker=missing_texture_paths,
) -> None:
    args = parse_args(argv)
    heads = resolve_heads(args)
    version_file = Path(version_file)
    version = args.version or load_version(version_file)

    root = Path(root)
    ids = load_or_create_ids(ids_path)
    builder = builder_factory(root, ids, version)
    builder.initialize()
    client = client_factory()

    for head in heads:
        profile = client.fetch_profile(head.name)
        if not profile.has_skin:
            print(f"Warning: BedrockViewer reports skin=false for {head.name}.", file=sys.stderr)
        skin_bytes = client.download_skin(profile.xuid)
        process_skin(
            skin_bytes,
            builder.rp_dir / "textures" / "blocks" / "skulls" / f"{head.slug}.png",
            builder.rp_dir / "textures" / "items" / "skulls" / f"{head.slug}.png",
        )
        builder.add_head(head)

    missing = missing_texture_checker(builder.rp_dir, heads)
    if args.require_textures and missing:
        for path in missing:
            print(f"Missing texture: {path}", file=sys.stderr)
        raise SystemExit(1)

    builder.finish(include_trader_trades=args.include_trader_trades)

    output = Path(args.output) if args.output else root / "dist" / f"Playerheads-v{'.'.join(str(part) for part in version)}.mcaddon"
    builder.build_mcaddon(output)
    if not args.no_version_bump:
        save_version(version, version_file)
    print(f"Built {output}")
