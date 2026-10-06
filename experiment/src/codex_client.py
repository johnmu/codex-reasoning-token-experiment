"""Small adapter for Codex's JSON-line protocol. Experiment logic lives in run.py."""
import json
import queue
import subprocess
import threading
import time

from common import AUTH_TYPES, ROOT, codex_environment


class CodexClient:
    def __init__(self, binary, auth, stderr_path, environment_overrides=None):
        home = ROOT / ".local" / auth
        if (home / "config.toml").read_bytes() != (ROOT / "experiment/config/controlled.toml").read_bytes():
            raise RuntimeError(f"Configuration differs for {auth}; inspect before running")
        self.stderr = stderr_path.open("w")
        self.log = None
        self.pending = []
        self.messages = queue.Queue()
        self.request_id = 0
        environment = codex_environment(auth)
        environment.update(environment_overrides or {})
        self.process = subprocess.Popen(
            [binary, "app-server", "--strict-config", "--listen", "stdio://"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
            text=True, bufsize=1, env=environment, cwd=home)
        threading.Thread(target=self.read_stdout, daemon=True).start()
        try:
            self.request("initialize", {
                "clientInfo": {"name": "reasoning_token_experiment", "version": "2.0"},
                "capabilities": {"experimentalApi": True}})
            self.send({"method": "initialized", "params": {}})
        except Exception:
            self.close()
            raise

    def read_stdout(self):
        for line in self.process.stdout:
            try:
                self.messages.put(json.loads(line))
            except ValueError:
                self.messages.put({"method": "invalid_json", "params": {"text": line.rstrip()}})
        self.messages.put(None)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def receive(self, timeout=60):
        try:
            message = self.messages.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError("Codex did not send an event before the deadline")
        if message is None:
            raise RuntimeError("Codex exited; inspect its private stderr log")
        if self.log:
            self.log.write(json.dumps(message) + "\n")
            self.log.flush()
        if "method" in message and "id" in message:
            self.send({"id": message["id"], "error": {
                "code": -32601, "message": "Tools and approvals disabled in this test"}})
            message["rejected_server_request"] = True
        return message

    def request(self, method, params):
        self.request_id += 1
        number = self.request_id
        self.send({"id": number, "method": method, "params": params})
        deadline = time.monotonic() + 60
        while True:
            message = self.receive(max(0.001, deadline - time.monotonic()))
            if message.get("id") == number and "method" not in message:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message["result"]
            self.pending.append(message)

    def check_login(self, auth):
        account = self.request("account/read", {"refreshToken": False})["account"]
        if not account or account["type"] != AUTH_TYPES[auth]:
            raise RuntimeError(f"{auth} login is not configured; use python3 -m experiment setup login {auth}")
        # Return only auth type and plan, rather than account identity.
        return {"type": account["type"], "plan": account.get("planType")}

    def list_models(self):
        models, cursor = [], None
        while True:
            response = self.request("model/list", {
                "limit": 100, "includeHidden": True, "cursor": cursor})
            models.extend(response["data"])
            cursor = response.get("nextCursor")
            if not cursor:
                return models

    def next_event(self, timeout):
        return self.pending.pop(0) if self.pending else self.receive(timeout)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        for stream in [self.process.stdin, self.process.stdout, self.stderr]:
            stream.close()
