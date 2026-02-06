# brute-force-transfer

The goal of the *brute-force-transfer (BFT)* project is to provide the benefits of a zip file (packaging a directory structure into a single file) using a single JSON/text file format instead of a binary blob of bytes leveraging existing programmatic runtimes (e.g. Python or Node). This way, you can transmit a JSON file as text instead of a binary blob and turn it into a directory elsewhere.

## Format

Each node is one of the following, and may include an optional `comment` string:

- **Directory**
  - Required: `type: "directory"`, `entries`
  - Optional: `comment`
  - `entries` is a JSON object mapping names to child nodes
- **Text file**
  - Required: `type: "text"`, `content`
  - Optional: `comment`
  - `content` is a UTF-8 string (JSON escaping only)
- **Binary file**
  - Required: `type: "binary"`, `encoding`, `content`
  - Optional: `comment`
  - `encoding` is currently `"base64"`
  - `content` is base64 text

The decoder ignores `comment` when writing to disk.

### Example

```json
{
  "type": "directory",
  "entries": {
    "README.txt": {
      "type": "text",
      "content": "Hello Brute Force Transfer!\n"
    },
    "data.bin": {
      "type": "binary",
      "encoding": "base64",
      "content": "AAECAwQF"
    },
    "notes.txt": {
      "type": "text",
      "content": "Nested file.\n",
      "comment": "This is a note about notes.txt."
    }
  }
}
```

### Expectations

- Inputs must match `brute-force-transfer.schema.json`. Validation happens on both encode and decode.
- The encoder determines text files by UTF-8 decodeability (rejects null bytes).
- Directory entries are ordered by name when encoded.
- Comment fields are preserved in JSON and ignored when writing to disk.


## Python
`bft.py` encodes a directory into a JSON structure and decodes it back. The format is explicit: every node includes a `type` and follows the JSON Schema in `brute-force-transfer.schema.json`.

### Optional: strict schema validation

`bft.py` will validate against the JSON schema if `jsonschema` is installed.

To set up a local virtual environment (not required!):

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

If `jsonschema` is not installed, `bft.py` will warn and skip validation.

To run tests inside the venv:

```bash
. .venv/bin/activate
python -m unittest -v
```


### Bootstrapping `bft.py` from (mostly) Scratch

These steps assume you have a copy of [`bfg.json`](./bft.json) on your system and a "modern" version of Python.

Take the contents of [`inflate_bft_py.py`](./inflate_bfg_py.py) and enter it into a file called `inflate_bfg_py.py` somehow. This file must be in the same directory as your copy of `bfg.json`.

Then, run the command `python inflate_bfg_py.py`. This will find the `bft.py` Python file and extract its contents to `bft.py`. 

Once you have `bft.py` on your system, run `python bft.py decode bft.json bft` and it will recreate this directory on your system in the `bft` subdirectory.


## Packaging `bft.json` for bft transfer

Run [`deflate_bft_py.py](./deflate_bft_py.py). It will take the contents of its directory (minus the files deliberately excluded in its `IGNORE_NAMES` field) and write it to [`bft.json`](./bft.json).
