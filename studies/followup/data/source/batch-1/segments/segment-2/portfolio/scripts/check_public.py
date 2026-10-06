"""Check Git's publishable files for private paths, credentials and forbidden files."""
import argparse
import re
import subprocess
from pathlib import Path

PRIVATE_ROOTS = [".local/", ".history/", "results/", "validation/", "sources/"]
PATTERNS = {
    "API-key-like value": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "JWT-like value": re.compile(rb"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"),
    "literal bearer credential": re.compile(rb"\bBearer\s+[A-Za-z0-9._-]{20,}"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "personal home path": re.compile(rb"/(?:Users|home)/[^/\s\"\\]+"),
    "original workspace path": re.compile(rb"/Volumes/" + rb"Studio extra storage"),
    "email address": re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}


def findings(name, contents, private_key=None):
    results = []
    if any(name.startswith(root) for root in PRIVATE_ROOTS) or Path(name).name == "auth.json" or Path(name).suffix in [".pem", ".key", ".db"]:
        results.append("private file")
    results.extend(label for label, pattern in PATTERNS.items() if pattern.search(contents))
    if private_key and private_key in contents:
        results.append("supplied private key")
    return results


def check(staged=False, key_file=None):
    names = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    if not any(names):
        raise SystemExit("No tracked files to check; stage the intended public files first.")
    private_key = Path(key_file).read_bytes().strip() if key_file else None
    failures = []
    for name in filter(None, names):
        contents = subprocess.check_output(["git", "show", f":{name}"]) if staged else Path(name).read_bytes()
        failures.extend((name, label) for label in findings(name, contents, private_key))
    # Report names and categories only; never show matching credential values.
    for name, label in failures:
        print(f"FAIL {name}: {label}")
    if failures:
        raise SystemExit("Public-file check failed.")
    print(f"Public-file check passed for {sum(bool(name) for name in names)} tracked files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--key-file", help="Optional local key file to check for exact accidental disclosure")
    args = parser.parse_args()
    check(args.staged, args.key_file)
