import json
import os
import tempfile
import unittest
from pathlib import Path

import json64


class TestJson64(unittest.TestCase):
    def roundtrip_dir(self, source: Path) -> Path:
        payload = json64.encode_path(source)
        schema = json64.load_schema()
        json64.validate_payload(payload, schema)

        temp_dir = Path(tempfile.mkdtemp())
        dest = temp_dir / "decoded"
        json64.decode_node(payload, dest)
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

    def test_comment_node_is_ignored_on_decode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out"
            node = {
                "type": "comment",
                "content": "Note about file",
                "node": {"type": "text", "content": "Hello\n"},
            }
            schema = json64.load_schema()
            json64.validate_payload(node, schema)
            json64.decode_node(node, dest / "note.txt")
            self.assertEqual((dest / "note.txt").read_text(encoding="utf-8"), "Hello\n")

    def test_schema_rejects_unknown_type(self) -> None:
        schema = json64.load_schema()
        bad = {"type": "unknown", "content": "nope"}
        with self.assertRaises(ValueError):
            json64.validate_payload(bad, schema)

    def test_sample_json_matches_schema(self) -> None:
        sample_path = Path(__file__).with_name("sample_json64.json")
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        schema = json64.load_schema()
        json64.validate_payload(data, schema)


if __name__ == "__main__":
    unittest.main()
