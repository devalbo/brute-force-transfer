# brute-force-transfer

The goal of the *brute-force-transfer (BFT)* project is to provide the benefits of a zip file (packaging a directory structure into a single file) using a single JSON/text file format instead of a binary blob of bytes leveraging existing programmatic runtimes (e.g. Python or Node).

## Format

Each node is one of the following:

- **Directory**
  - Required: `type: "directory"`, `entries`
  - `entries` is a JSON object mapping names to child nodes
- **Text file**
  - Required: `type: "text"`, `content`
  - `content` is a UTF-8 string (JSON escaping only)
- **Binary file**
  - Required: `type: "binary"`, `encoding`, `content`
  - `encoding` is currently `"base64"`
  - `content` is base64 text
- **Comment wrapper**
  - Required: `type: "comment"`, `content`, `node`
  - `content` is a note about the wrapped item
  - `node` is the real node being commented on
  - The decoder ignores the comment and writes the wrapped `node` to disk

### Example

```json
{
  "type": "directory",
  "entries": {
    "README.txt": {
      "type": "text",
      "content": "Hello JSON64\n"
    },
    "data.bin": {
      "type": "binary",
      "encoding": "base64",
      "content": "AAECAwQF"
    },
    "notes.txt": {
      "type": "comment",
      "content": "This is a note about notes.txt.",
      "node": {
        "type": "text",
        "content": "Nested file.\n"
      }
    }
  }
}
```

### Expectations

- Inputs must match `json64.schema.json`. Validation happens on both encode and decode.
- The encoder determines text files by UTF-8 decodeability (rejects null bytes).
- Directory entries are ordered by name when encoded.
- Comment nodes are preserved in JSON and ignored when writing to disk.


## Python
`bft.py` encodes a directory into a JSON structure and decodes it back. The format is explicit: every node includes a `type` and follows the JSON Schema in `json64.schema.json`.


### Bootstrapping `bft.py` from (mostly) Scratch

These steps assume you have a copy of [`bfg.json`](./bft.json) on your system and a "modern" version of Python.

Take the contents of [`inflate_bft_py.py`](./inflate_bfg_py.py) and enter it into a file called `inflate_bfg_py.py` somehow. This file must be in the same directory as your copy of `bfg.json`.

Then, run the command `python inflate_bfg_py.py`. This will find the `bft.py` Python file and extract its contents to `bft.py`. 

Once you have `bft.py` on your system, run `python bft.py bft.json` and it will recreate this directory on your system.


## Packaging `bft.json` for bft transfer

Run [`deflate_bft_py.py](./deflate_bft_py.py). It will take the contents of its directory (minus the files deliberately excluded in its `IGNORE_NAMES` field) and 

<!-- 

```bash
python json64.py encode path/to/dir -o out.json
python json64.py decode out.json path/to/output_dir
``` -->


