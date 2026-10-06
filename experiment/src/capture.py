"""Start a loopback MITM for one response and summarize its recorded events."""
import json
import os
import socket
import subprocess
import time
from pathlib import Path

from common import ROOT


class Capture:
    def __init__(self, output, identical_payload=None, payload_sha256=None, headers_sha256=None):
        executable = ROOT / ".local/capture-venv" / ("Scripts/mitmdump.exe" if os.name == "nt" else "bin/mitmdump")
        if not executable.is_file():
            raise RuntimeError("Install experiment/requirements.txt in .local/capture-venv first")
        self.output = output
        self.process = None
        # Reserve an unused port; no other app's proxy or trust settings change.
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            self.port = probe.getsockname()[1]
        self.certificates = ROOT / ".local/capture-ca"
        self.certificates.mkdir(mode=0o700, exist_ok=True)
        private_log = ROOT / ".local" / (output.parent.name + "-" + output.stem + "-proxy-stderr.txt")
        self.stderr = private_log.open("w")
        environment = dict(os.environ)
        environment["EXPERIMENT_CAPTURE_FILE"] = str(output)
        addon = "capture_addon.py"
        ready = None
        if identical_payload:
            addon = "identical_addon.py"
            ready = private_log.with_suffix(".ready")
            ready.unlink(missing_ok=True)
            environment.update(EXPERIMENT_IDENTICAL_PAYLOAD=str(identical_payload),
                               EXPERIMENT_IDENTICAL_SHA256=payload_sha256,
                               EXPERIMENT_IDENTICAL_HEADERS=str(identical_payload.parent / "request-headers.json"),
                               EXPERIMENT_HEADERS_SHA256=headers_sha256,
                               EXPERIMENT_CAPTURE_READY_FILE=str(ready))
        command = [str(executable), "--listen-host", "127.0.0.1", "--listen-port", str(self.port),
                   "--set", f"confdir={self.certificates}", "--set", "flow_detail=0",
                   "--set", "termlog_verbosity=error", "--set", "connection_strategy=lazy",
                   "-s", str(Path(__file__).with_name(addon))]
        self.process = subprocess.Popen(command, env=environment, stdout=self.stderr, stderr=self.stderr)
        deadline = time.monotonic() + 20
        try:
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError("Capture proxy exited; inspect its private log")
                try:
                    with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                        if (self.certificates / "mitmproxy-ca-cert.pem").is_file() and (ready is None or ready.is_file()):
                            return
                except OSError:
                    pass
                time.sleep(0.1)
            raise TimeoutError("Capture proxy did not start")
        except Exception:
            self.close()
            raise

    def environment(self):
        proxy = f"http://127.0.0.1:{self.port}"
        settings = {name: proxy for name in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                                             "http_proxy", "https_proxy", "all_proxy"]}
        settings.update(NO_PROXY="127.0.0.1,localhost,::1", no_proxy="127.0.0.1,localhost,::1",
                        CODEX_CA_CERTIFICATE=str(self.certificates / "mitmproxy-ca-cert.pem"))
        return settings

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.stderr.close()


def summarize_wire(path, native_usage):
    events = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    outgoing = [e for e in events if e.get("direction") == "out" and isinstance(e.get("body"), dict)]
    requests = [e for e in outgoing if e["body"].get("generate") is not False
                and (e["body"].get("type") == "response.create" or e["transport"] == "http")]
    incoming = [e for e in events if e.get("direction") == "in" and isinstance(e.get("body"), dict)]
    if len(requests) != 1:
        return {"wire_flags": ["missing_or_multiple_generation_requests"]}
    request = requests[0]
    responses = [e for e in incoming if e["time"] >= request["time"]
                 and e["body"].get("type") == "response.completed"]
    if len(responses) != 1:
        return {"wire_flags": ["missing_or_multiple_completed_responses"]}
    completed = responses[0]
    response = completed["body"]["response"]
    usage = response.get("usage", {})
    details = usage.get("output_tokens_details", {})
    input_details = usage.get("input_tokens_details", {})
    expected = {"inputTokens": usage.get("input_tokens"),
                "outputTokens": usage.get("output_tokens"), "totalTokens": usage.get("total_tokens"),
                "reasoningOutputTokens": details.get("reasoning_tokens"),
                "cachedInputTokens": input_details.get("cached_tokens"),
                "cacheWriteInputTokens": input_details.get("cache_write_tokens")}
    flags = []
    if any(value is None for value in expected.values()):
        flags.append("missing_server_tokens")
    if any(native_usage.get(key) != value for key, value in expected.items()):
        flags.append("server_native_token_mismatch")
    text_events = [e for e in incoming if e["time"] >= request["time"]
                   and e["body"].get("type") == "response.output_text.delta" and e["body"].get("delta")]
    first_text = text_events[0]["time"] - request["time"] if text_events else None
    answer_events = [e for e in incoming if e["time"] >= request["time"]
                     and e["body"].get("type") == "response.output_text.done"]
    return {"sent_model": request["body"].get("model"),
            "sent_effort": request["body"].get("reasoning", {}).get("effort"),
            "server_model": response.get("model"),
            "server_declared_effort": response.get("reasoning", {}).get("effort"),
            "server_answer": "".join(e["body"].get("text", "") for e in answer_events),
            "server_usage": usage, "wire_first_text_seconds": first_text,
            "wire_seconds": completed["time"] - request["time"],
            "wire_host": request["host"], "wire_path": request["path"],
            "wire_flags": flags}
