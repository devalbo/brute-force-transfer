#!/usr/bin/env python3
import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - optional dependency
    Draft202012Validator = None


TYPE_KEY = "type"
CONTENT_KEY = "content"
ENCODING_KEY = "encoding"
ENTRIES_KEY = "entries"


def parse_ignore_names(ignore_names: Iterable[str] | None = None) -> Iterable[str]:
    if ignore_names is None:
        return ()
    ignore_lines = [line.strip() for line in ignore_names.splitlines()]
    ignore_names = [line for line in ignore_lines if line and not line.startswith("#")]
    return ignore_names


def parse_ignore_names_from_file(ignore_file: Path) -> Iterable[str]:
    if not ignore_file.exists() or not ignore_file.is_file():
        raise FileNotFoundError(f"Ignore file not found: {ignore_file}")
    return parse_ignore_names(ignore_file.read_text(encoding="utf-8"))


def is_text_bytes(data: bytes) -> bool:
    if not data:
        return True
    sample = data[:8192]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def encode_path(path: Path, ignore_names: Iterable[str] | None = None) -> Dict[str, Any]:
    ignore = set(ignore_names or ())
    if path.is_dir():
        entries: Dict[str, Any] = {}
        for child in sorted(path.iterdir(), key=lambda p: p.name):
            if child.name in ignore:
                continue
            entries[child.name] = encode_path(child, ignore_names=ignore)
        return {
            TYPE_KEY: "directory",
            ENTRIES_KEY: entries,
        }

    data = path.read_bytes()
    if is_text_bytes(data):
        content = data.decode("utf-8")
        return {
            TYPE_KEY: "text",
            CONTENT_KEY: content,
        }

    encoded = base64.b64encode(data).decode("ascii")
    return {
        TYPE_KEY: "binary",
        ENCODING_KEY: "base64",
        CONTENT_KEY: encoded,
    }


def decode_node(node: Any, dest: Path) -> None:
    if not isinstance(node, dict):
        raise ValueError(f"Unsupported node type at {dest}: {type(node).__name__}")

    node_type = node.get(TYPE_KEY)
    if node_type == "binary":
        if node.get(ENCODING_KEY) != "base64":
            raise ValueError(f"Unsupported encoding for binary node: {node.get(ENCODING_KEY)}")
        data = base64.b64decode(node.get(CONTENT_KEY, ""))
        dest.write_bytes(data)
        return

    if node_type == "text":
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(node.get(CONTENT_KEY, ""), encoding="utf-8")
        return

    if node_type == "directory":
        dest.mkdir(parents=True, exist_ok=True)
        entries = node.get(ENTRIES_KEY, {})
        for name, child in entries.items():
            decode_node(child, dest / name)
        return

    raise ValueError(f"Unsupported node type at {dest}: {node_type}")


def load_schema() -> Dict[str, Any]:
    schema_path = Path(__file__).with_name("brute-force-transfer.schema.json")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_payload(payload: Any, schema: Dict[str, Any]) -> None:
    if Draft202012Validator is None:
        print("Warning: jsonschema not installed; skipping schema validation.", file=sys.stderr)
        return
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        lines = []
        for err in errors[:5]:
            location = "/".join(str(p) for p in err.path)
            lines.append(f"{location or '<root>'}: {err.message}")
        summary = "; ".join(lines)
        raise ValueError(f"Payload does not match schema: {summary}")


def encode_command(src_dir: Path, output: Path | None, peer_output: bool) -> None:
    if not src_dir.exists() or not src_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    payload = encode_path(src_dir)
    if Draft202012Validator is not None:
        schema = load_schema()
        validate_payload(payload, schema)
    text = json.dumps(payload, ensure_ascii=False, indent=2)

    if output is None and peer_output:
        output = src_dir.parent / f"{src_dir.name}.bft"

    if output is None:
        print(text)
    else:
        output.write_text(text, encoding="utf-8")


def decode_command(json_file: Path, dest_dir: Path) -> None:
    if not json_file.exists() or not json_file.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_file}")

    data = json.loads(json_file.read_text(encoding="utf-8"))
    if Draft202012Validator is not None:
        schema = load_schema()
        validate_payload(data, schema)
    dest_dir.mkdir(parents=True, exist_ok=True)
    decode_node(data, dest_dir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Encode a directory to JSON with base64 for binary files, and decode back."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_parser = subparsers.add_parser("encode", help="Encode a directory to JSON")
    encode_parser.add_argument("src_dir", type=Path, help="Source directory to encode")
    encode_parser.add_argument(
        "-o", "--output", type=Path, default=None, help="Output JSON file (default: stdout)"
    )
    encode_parser.add_argument(
        "-d",
        "--peer-output",
        action="store_true",
        help="Write output as a peer to the source directory (name.bft.json)",
    )

    decode_parser = subparsers.add_parser("decode", help="Decode JSON into a directory")
    decode_parser.add_argument("json_file", type=Path, help="JSON file to decode")
    decode_parser.add_argument("dest_dir", type=Path, help="Destination directory")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "encode":
        encode_command(args.src_dir, args.output, args.peer_output)
        return

    if args.command == "decode":
        decode_command(args.json_file, args.dest_dir)
        return

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
