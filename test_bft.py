import json
import os
import tempfile
import unittest
from pathlib import Path

import bft


class TestBFT(unittest.TestCase):
    def roundtrip_dir(self, source: Path) -> Path:
        payload = bft.encode_path(source)
        schema = bft.load_schema()
        bft.validate_payload(payload, schema)

        temp_dir = Path(tempfile.mkdtemp())
        dest = temp_dir / "decoded"
        bft.decode_node(payload, dest)
        return dest

    def test_roundtrip_text_and_binary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            src.mkdir()
            (src / "a.txt").write_text("Hello\nWorld\n", encoding="utf-8")
            (src / "b.bin").write_bytes(bytes([0, 1, 2, 3, 255]))
            (src / "nested").mkdir()
            (src / "nested" / "c.txt").write_text("Nested\n", encoding="utf-8")

            decoded = self.roundtrip_dir(src)

            self.assertEqual((decoded / "a.txt").read_text(encoding="utf-8"), "Hello\nWorld\n")
            self.assertEqual((decoded / "b.bin").read_bytes(), bytes([0, 1, 2, 3, 255]))
            self.assertEqual((decoded / "nested" / "c.txt").read_text(encoding="utf-8"), "Nested\n")

    def test_comment_field_is_ignored_on_decode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out"
            node = {
                "type": "text",
                "content": "Hello\n",
                "comment": "Note about file",
            }
            schema = bft.load_schema()
            bft.validate_payload(node, schema)
            bft.decode_node(node, dest / "note.txt")
            self.assertEqual((dest / "note.txt").read_text(encoding="utf-8"), "Hello\n")

    def test_schema_rejects_unknown_type(self) -> None:
        if bft.Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        schema = bft.load_schema()
        bad = {"type": "unknown", "content": "nope"}
        with self.assertRaises(ValueError):
            bft.validate_payload(bad, schema)

    def test_sample_json_matches_schema(self) -> None:
        if bft.Draft202012Validator is None:
            self.skipTest("jsonschema not installed")
        sample_path = Path(__file__).with_name("bft.json")
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        schema = bft.load_schema()
        bft.validate_payload(data, schema)


if __name__ == "__main__":
    unittest.main()
