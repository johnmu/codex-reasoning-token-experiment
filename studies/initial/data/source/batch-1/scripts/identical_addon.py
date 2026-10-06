"""Replace Codex's generating message with a frozen neutral request.

No native tool descriptions or session metadata are sent upstream. A local
acknowledgement consumes Codex's optional prewarm without sending it upstream;
the real request starts a new stateless response. Real responses are untouched.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import capture_addon as observe

BODY = b""
HEADERS = {}
SENT = False
AUTH_HEADERS = {"authorization", "cookie", "chatgpt-account-id"}
TRANSPORT_HEADERS = {"host", "connection", "upgrade", "sec-websocket-key", "sec-websocket-version"}


def load(loader):
    global BODY, HEADERS, SENT
    BODY = Path(os.environ["EXPERIMENT_IDENTICAL_PAYLOAD"]).read_bytes()
    assert hashlib.sha256(BODY).hexdigest() == os.environ["EXPERIMENT_IDENTICAL_SHA256"]
    header_bytes = Path(os.environ["EXPERIMENT_IDENTICAL_HEADERS"]).read_bytes()
    assert hashlib.sha256(header_bytes).hexdigest() == os.environ["EXPERIMENT_HEADERS_SHA256"]
    HEADERS = json.loads(header_bytes)
    SENT = False
    Path(os.environ["EXPERIMENT_CAPTURE_READY_FILE"]).write_text("verified\n")


def request(flow):
    if observe.inference(flow):
        if flow.request.headers.get("upgrade", "").lower() != "websocket":
            from mitmproxy import http
            flow.response = http.Response.make(409, b'Identical-request experiment requires WebSocket transport')
            observe.record(flow, "blocked_request", reason="http_fallback")
            return
        for name in list(flow.request.headers):
            if name.lower() not in AUTH_HEADERS | TRANSPORT_HEADERS:
                del flow.request.headers[name]
        flow.request.headers.update(HEADERS)
        observe.record(flow, "controlled_headers", headers={name: flow.request.headers[name] for name in HEADERS})
    observe.request(flow)


def prefix_acknowledgement(flow):
    from mitmproxy import ctx
    model = json.loads(BODY)["model"]
    response = {"id": "resp_local_prefix_ack", "object": "response", "status": "completed",
                "model": model, "output": [], "usage": {"input_tokens": 0, "output_tokens": 0,
                "total_tokens": 0, "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 0}}}
    for kind in ["response.created", "response.completed"]:
        event = json.dumps({"type": kind, "response": response}).encode()
        # The argument is to_client, rather than from_client.
        ctx.master.commands.call("inject.websocket", flow, True, event)


def websocket_message(flow):
    global SENT
    if not observe.inference(flow):
        return
    latest = flow.websocket.messages[-1]
    if latest.injected:
        if latest.from_client:
            latest.drop()
            observe.record(flow, "blocked_request", reason="local_ack_cannot_go_upstream")
            flow.kill()
            return
        observe.record(flow, "local_prefix_ack")
        return
    if not latest.from_client:
        observe.websocket_message(flow)
        return
    original = json.loads(latest.content)
    observe.record(flow, "native_original_message", body=original)
    if original.get("type") != "response.create":
        latest.drop()
        observe.record(flow, "blocked_request", reason="unexpected_message")
        flow.kill()
        return
    if original.get("generate") is False:
        latest.drop()
        prefix_acknowledgement(flow)
        return
    if SENT:
        latest.drop()
        observe.record(flow, "blocked_request", reason="extra_generation")
        flow.kill()
        return
    # The exact immutable bytes loaded before Codex starts are forwarded once.
    latest.content = BODY
    SENT = True
    observe.message(flow, "out", BODY.decode(), "websocket")


responseheaders = observe.responseheaders
error = observe.error
