"""Prepare separate logins without changing the user's normal Codex login."""
import argparse
import getpass
import os
import subprocess

from common import AUTH_TYPES, DEFAULT_CODEX, ROOT, codex_environment


def prepare():
    configuration = (ROOT / "config/controlled.toml").read_bytes()
    for auth in AUTH_TYPES:
        home = ROOT / ".local" / auth
        home.mkdir(parents=True, exist_ok=True)
        os.chmod(home, 0o700)
        destination = home / "config.toml"
        if destination.exists() and destination.read_bytes() != configuration:
            raise RuntimeError(f"Existing configuration differs: {destination}")
        destination.write_bytes(configuration)
        os.chmod(destination, 0o600)
    print("Prepared two isolated homes. No credentials copied or changed.")


def login(binary, auth):
    prepare()
    command = [binary, "login"]
    key = None
    if auth == "api":
        command.append("--with-api-key")
        key = getpass.getpass("API key (hidden): ") + "\n"
    subprocess.run(command, input=key, text=True,
                   env=codex_environment(auth), check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "login"])
    parser.add_argument("auth", nargs="?", choices=list(AUTH_TYPES))
    parser.add_argument("--codex", default=DEFAULT_CODEX)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.auth:
        login(args.codex, args.auth)
    else:
        parser.error("login requires api or chatgpt")
