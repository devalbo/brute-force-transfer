#!/usr/bin/env python3
import json
from pathlib import Path


def main() -> None:
    content_file = "bft.json"
    data = json.loads(Path(content_file).read_text(encoding="utf-8"))
    node_content = data["entries"]["bft.py"]["content"]
    print(node_content)


if __name__ == "__main__":
    main()
