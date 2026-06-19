from __future__ import annotations

import io
from pathlib import Path

from PIL import Image


SKIN_FACE_BASE = (8, 8, 16, 16)
SKIN_FACE_HAT = (40, 8, 48, 16)
OUTPUT_ICON_SIZE = (64, 64)


def load_skin_image(skin_bytes: bytes) -> Image.Image:
    try:
        with Image.open(io.BytesIO(skin_bytes)) as image:
            image_format = image.format
            image_size = image.size
            if image_format != "PNG":
                raise ValueError(f"Skin image must be PNG, got {image_format or 'unknown'}.")
            if image_size[0] != 64 or image_size[1] not in (32, 64):
                raise ValueError(f"Unexpected skin size {image_size}. Expected 64x64 or 64x32.")
            image = image.convert("RGBA").copy()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Skin PNG could not be opened: {exc}") from exc
    if image.height == 32:
        padded = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        padded.paste(image, (0, 0))
        image = padded
    return image


def build_face_icon(skin_image: Image.Image) -> Image.Image:
    base_face = skin_image.crop(SKIN_FACE_BASE)
    hat_face = skin_image.crop(SKIN_FACE_HAT)
    face_icon = Image.alpha_composite(base_face.copy(), hat_face)
    return face_icon.resize(OUTPUT_ICON_SIZE, Image.Resampling.NEAREST)


def process_skin_bytes(skin_bytes: bytes, block_texture_path: str | Path, item_icon_path: str | Path) -> None:
    skin_image = load_skin_image(skin_bytes)
    block_texture_path = Path(block_texture_path)
    item_icon_path = Path(item_icon_path)
    block_texture_path.parent.mkdir(parents=True, exist_ok=True)
    item_icon_path.parent.mkdir(parents=True, exist_ok=True)
    skin_image.save(block_texture_path, "PNG")
    build_face_icon(skin_image).save(item_icon_path, "PNG")
