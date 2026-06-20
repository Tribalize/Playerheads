# Playerheads

Playerheads builds a Minecraft Bedrock add-on that turns selected players into placeable head blocks. It uses BedrockViewer profile data and skin downloads to resolve player identity and textures before packaging the behavior and resource packs.

## Skin Source

Player data comes from BedrockViewer:

- Profile JSON: `/profile/<gamertag>/json`
- Skin download: `/download-skin/<xuid>`

## Build Locally

Install dependencies:

```powershell
pip install -r requirements.txt
```

Build from a heads JSON file:

```powershell
python build_playerheads.py --heads-file heads.json --version 1.0.0 --no-version-bump --require-textures --output dist/Playerheads-v1.0.0.mcaddon
```

Build from an inline list of player names:

```powershell
python build_playerheads.py --heads "PPTribalize,UKM Quantus" --version 1.0.0 --no-version-bump --require-textures --output dist/Playerheads-v1.0.0.mcaddon
```

Wandering trader trades are disabled by default. Turn them on for all selected heads with `--include-trader-trades`.

## Configure Heads JSON

Use `heads.json` to define the selected heads:

```json
[
  {
    "name": "PPTribalize"
  },
  {
    "name": "UKM Quantus"
  }
]
```

## Output Archive

The `.mcaddon` archive is rooted directly at:

- `Playerheads_BP/`
- `Playerheads_RP/`

There are no `behavior_packs/` or `resource_packs/` wrapper folders.

## Tests

Run the test suite with:

```powershell
python -m unittest discover -s tests -v
```
