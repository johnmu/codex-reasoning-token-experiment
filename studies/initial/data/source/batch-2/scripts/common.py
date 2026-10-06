"""Shared paths and small file helpers; no model calls happen here."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_CODEX = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
DEFAULT_CODEX = DESKTOP_CODEX if Path(DESKTOP_CODEX).is_file() else "codex"
AUTH_TYPES = {"api": "apiKey", "chatgpt": "chatgpt"}


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def codex_environment(auth):
    """Use one isolated login, with no ambient API-key override."""
    environment = dict(os.environ)
    for name in list(environment):
        if name.startswith(("OPENAI_", "CODEX_")):
            del environment[name]
    environment["CODEX_HOME"] = str(ROOT / ".local" / auth)
    return environment
