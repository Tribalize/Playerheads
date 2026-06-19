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


def make_image_bytes(size: tuple[int, int], image_format: str = "PNG") -> bytes:
    if image_format == "JPEG":
        image = Image.new("RGB", size, (1, 2, 3))
    else:
        image = Image.new("RGBA", size, (1, 2, 3, 255))
    buf = io.BytesIO()
    image.save(buf, image_format)
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
        self.assertEqual(icon_first_pixel, (105, 10, 15, 255))

    def test_pads_64x32_skin_to_full_texture(self):
        with tempfile.TemporaryDirectory() as tmp:
            block_path = Path(tmp) / "block.png"
            item_path = Path(tmp) / "item.png"

            process_skin_bytes(make_image_bytes((64, 32)), block_path, item_path)

            with Image.open(block_path) as block:
                block_size = block.size
                padded_pixel = block.getpixel((0, 63))

        self.assertEqual(block_size, (64, 64))
        self.assertEqual(padded_pixel, (0, 0, 0, 0))

    def test_rejects_invalid_image_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                process_skin_bytes(b"not image", Path(tmp) / "block.png", Path(tmp) / "item.png")

    def test_rejects_non_png_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "PNG"):
                process_skin_bytes(
                    make_image_bytes((64, 64), "JPEG"),
                    Path(tmp) / "block.png",
                    Path(tmp) / "item.png",
                )

    def test_rejects_invalid_skin_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Expected 64x64 or 64x32"):
                process_skin_bytes(
                    make_image_bytes((32, 32)),
                    Path(tmp) / "block.png",
                    Path(tmp) / "item.png",
                )


if __name__ == "__main__":
    unittest.main()
