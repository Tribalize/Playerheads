import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from playerheads.textures import process_skin_bytes


def make_skin_png() -> bytes:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for x in range(8, 16):
        for y in range(8, 16):
            image.putpixel((x, y), (10, 20, 30, 255))
    for x in range(40, 48):
        for y in range(8, 16):
            image.putpixel((x, y), (200, 0, 0, 128))
    buf = io.BytesIO()
    image.save(buf, "PNG")
    return buf.getvalue()


class TextureProcessingTests(unittest.TestCase):
    def test_process_skin_writes_full_texture_and_face_icon(self):
        with tempfile.TemporaryDirectory() as tmp:
            block_path = Path(tmp) / "blocks" / "pptribalize.png"
            item_path = Path(tmp) / "items" / "pptribalize.png"

            process_skin_bytes(make_skin_png(), block_path, item_path)

            with Image.open(block_path) as block:
                block_size = block.size
            with Image.open(item_path) as icon:
                icon_size = icon.size
                icon_first_pixel = icon.getpixel((0, 0))

        self.assertEqual(block_size, (64, 64))
        self.assertEqual(icon_size, (64, 64))
        self.assertNotEqual(icon_first_pixel, (10, 20, 30, 255))

    def test_rejects_invalid_image_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                process_skin_bytes(b"not image", Path(tmp) / "block.png", Path(tmp) / "item.png")


if __name__ == "__main__":
    unittest.main()
