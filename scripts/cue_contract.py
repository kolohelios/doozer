"""Prospective JSON Schema import using CUE's native definition placement."""

import functools
import json
from pathlib import Path
import subprocess
import tempfile


@functools.lru_cache(maxsize=64)
def compile_schema(encoded):
    schema = json.loads(encoded)
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "schema.json"
        path.write_text(json.dumps(schema, allow_nan=False))
        result = subprocess.run(["cue", "import", "jsonschema", str(path), "-p", "judgment", "-l", "#Report:", "-o", "-"], check=True, capture_output=True, text=True)
    return result.stdout  # Standard-library imports stay at file scope.
