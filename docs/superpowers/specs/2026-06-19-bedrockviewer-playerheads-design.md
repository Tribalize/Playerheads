# BedrockViewer Playerheads Generator Design

## Goal

Create a standalone `Tribalize/Playerheads` project that builds a Minecraft Bedrock `.mcaddon` containing custom player head items and placeable head blocks. The generator must use BedrockViewer only for player skin data and must not be combined with the existing `Tribalize/StreamerHeads` repository.

The first implementation should provide a reliable command-line generator, GitHub Actions build workflow, documentation, and focused tests.

## Repository Shape

The empty `Tribalize/Playerheads` repository will become a small Python project:

- `build_playerheads.py`: main generator script.
- `heads.json`: default gamertag list.
- `playerheads_ids.json`: persisted UUID store for pack upgrade stability.
- `version.json`: persisted default add-on version.
- `requirements.txt`: Python runtime dependencies.
- `README.md`: local and GitHub Actions usage.
- `.github/workflows/build-addon.yml`: manual workflow that builds and uploads the `.mcaddon`.
- `tests/`: unit tests and small fixtures.

The project may borrow proven generation ideas from StreamerHeads, but it should use its own names, docs, defaults, and BedrockViewer skin source.

## Inputs

The generator supports two head selection paths:

- `--heads "PPTribalize,OtherGamertag"` for a one-off comma-separated list.
- `--heads-file heads.json` for a saved list.

`heads.json` accepts either strings or objects:

```json
{
  "heads": [
    "PPTribalize",
    {
      "name": "OtherGamertag",
      "display_name": "Other Gamertag",
      "model": "head"
    }
  ]
}
```

`name` is the Bedrock gamertag used with BedrockViewer. `display_name` is optional and controls language-file text. `model` is optional and defaults to the standard head model.

The build also supports:

- `--version 1.0.0` to stamp manifests and output filenames.
- `--no-version-bump` for deterministic CI builds.
- `--output dist/Playerheads-v1.0.0.mcaddon`.
- `--require-textures` to fail if a BedrockViewer skin cannot be downloaded or processed.
- `--include-trader-trades` to enable wandering trader head trades for the whole build.

By default, wandering trader trades are disabled.

## BedrockViewer Data Flow

For each gamertag:

1. Request `https://bedrockviewer.com/profile/<gamertag>/json`.
2. Validate that the response contains an `XUID`.
3. Prefer `skin: true` as a signal that a downloadable skin should exist.
4. Download the full skin PNG from `https://bedrockviewer.com/download-skin/<xuid>`.
5. Validate that the downloaded asset is a PNG and can be opened by Pillow.
6. Save the complete skin image as the block and attachable texture.
7. Crop the head front face and overlay layer to create the 64x64 item icon.

The generator should report clear per-player errors. With `--require-textures`, any missing or invalid skin stops the build. Without it, the build may continue only if placeholder behavior is intentionally implemented and documented.

## Generated Add-on

The `.mcaddon` archive contains the two pack folders directly at the archive root:

- `Playerheads_BP/`
- `Playerheads_RP/`

The behavior pack includes:

- manifest linked to the resource pack.
- Script API module.
- generated item files for wearable head items.
- generated block files for placeable head blocks.
- recipes to convert between head item and placed-block item forms where needed.
- script support for placement/death-drop behavior, following the proven shape from the reference add-ons.
- empty loot table for generated blocks.
- optional wandering trader economy trade table.

The resource pack includes:

- manifest linked to the behavior pack.
- generated attachables.
- generated block and attachable geometry.
- full skin textures under `textures/blocks/skulls/`.
- face icons under `textures/items/skulls/`.
- texture atlas updates.
- language entries.
- pack icon.
- Vibrant Visuals texture-set metadata for generated skull textures.

## Wandering Trader Option

Trader support is controlled for the whole build:

- Disabled by default.
- Enabled by `--include-trader-trades`.
- When enabled, trader trades include all selected heads in the build.

When enabled, the generator writes `Playerheads_BP/trading/economy_trades/wandering_trader_trades.json` using the existing safe pattern: preserve vanilla wandering trader groups and append a custom head group in the same tier.

When disabled, the generator does not write the trade-table override at all. This avoids changing wandering trader behavior for worlds that should only use death drops, recipes, or creative inventory access.

## Naming

The add-on identity uses Playerheads-specific names:

- Add-on name: `Playerheads`.
- Behavior pack folder: `Playerheads_BP`.
- Resource pack folder: `Playerheads_RP`.
- Namespace: `bph`, matching the existing BedrockPlayerHeads item and block identifiers unless implementation testing shows a strong reason to change it.

Gamertags are slugged to lowercase with spaces converted to underscores for file names and identifiers.

## Error Handling

The generator should make failures actionable:

- Missing BedrockViewer profile: report the gamertag and profile URL.
- Missing `XUID`: report the response shape enough to debug without dumping huge data.
- `skin: false`: warn that BedrockViewer did not report a downloadable skin.
- Skin download HTTP failure: report status code and download URL.
- Invalid image: report the file/player and Pillow error.
- Missing output texture paths under `--require-textures`: list every missing path.

Network calls should use timeouts.

## GitHub Actions

The manual workflow should:

1. Check out the repo.
2. Set up Python 3.12.
3. Install `requirements.txt`.
4. Run unit tests.
5. Build the add-on.
6. Upload the `.mcaddon` artifact.

Workflow inputs:

- `player_names`: optional comma-separated Bedrock gamertags.
- `heads_file`: default `heads.json` when `player_names` is empty.
- `version`: required version string.
- `include_trader_trades`: boolean default `false`; set to `true` to pass `--include-trader-trades` and generate wandering trader trades for all selected heads.

Because live BedrockViewer calls can be rate-limited or temporarily protected, tests should not depend on the live service.

## Tests

Initial tests should cover:

- Loading `heads.json` from string and object entries.
- Parsing BedrockViewer profile JSON.
- Building `/download-skin/<xuid>` URLs.
- Cropping a face icon from a fixture PNG.
- Trader enabled writes a trade-table override.
- Trader disabled omits the trade-table override.
- Manifest dependencies link BP and RP.
- `.mcaddon` archive root contains `Playerheads_BP/` and `Playerheads_RP/`, not `behavior_packs/` or `resource_packs/` wrappers.
- Missing texture checks report both block and item texture paths.

## Open Decisions Resolved

- This belongs in `Tribalize/Playerheads`, not `Tribalize/StreamerHeads`.
- The generator uses BedrockViewer only.
- The trader option applies to the whole build, not individual players.
- Trader trades are disabled by default; `--include-trader-trades` or Actions `include_trader_trades: true` enables trades for all selected heads.
