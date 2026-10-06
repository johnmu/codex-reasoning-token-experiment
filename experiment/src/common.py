"""Shared paths and small file helpers; no model calls happen here."""
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESKTOP_CODEX = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
DEFAULT_CODEX = os.environ.get("EXPERIMENT_CODEX") or (DESKTOP_CODEX if Path(DESKTOP_CODEX).is_file() else "codex")
AUTH_TYPES = {"api": "apiKey", "chatgpt": "chatgpt"}


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_link(directory, target):
    """Keep generated Markdown links correct for any chosen output folder."""
    return Path(os.path.relpath(target, directory)).as_posix()


def snapshot_file(directory, current, historical):
    """Read both the current layout and the immutable earlier source layout."""
    path = directory / 'source' / current
    return path if path.exists() else directory / 'source' / historical


def native_codex(binary):
    """Pin the actual executable, rather than a shell or npm launcher."""
    path = Path(shutil.which(binary) or binary).resolve()
    with path.open("rb") as file:
        magic = file.read(4)
    if magic not in [b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf",
                     b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"] and not magic.startswith(b"MZ"):
        raise RuntimeError("Select the native Codex executable with --codex or EXPERIMENT_CODEX; shell/npm launchers cannot be pinned by their own hash.")
    return str(path)


def codex_environment(auth):
    """Use one isolated login, with no ambient API-key override."""
    environment = dict(os.environ)
    for name in list(environment):
        if name.startswith(("OPENAI_", "CODEX_")):
            del environment[name]
    environment["CODEX_HOME"] = str(ROOT / ".local" / auth)
    return environment
