#!/usr/bin/env python3
import json
from pathlib import Path

import bft


OUTPUT_NAME = "bft.json"
IGNORE_NAMES = bft.parse_ignore_names_from_file(Path(".bftignore"))


def main() -> None:
    root = Path.cwd()
    output_path = root / OUTPUT_NAME
    payload = bft.encode_path(root, ignore_names=IGNORE_NAMES)
    if bft.Draft202012Validator is not None:
        schema = bft.load_schema()
        bft.validate_payload(payload, schema)

    payload_text = json.dumps(payload, ensure_ascii=False, indent=2)
    output_path.write_text(payload_text, encoding="utf-8")

    print(f"Packaged {len(payload_text)} bytes to {output_path}.")


if __name__ == "__main__":
    main()
