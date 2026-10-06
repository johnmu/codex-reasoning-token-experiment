"""Observe HTTP and WebSocket messages without editing their bodies or routes.

Run only inside mitmdump. Save inference bodies and safe header metadata;
authentication, cookies, and all other header values are omitted.
"""
import datetime
import json
import os
import time
from pathlib import Path

SAFE_HEADERS = {"content-type", "content-encoding", "user-agent", "originator",
                "x-codex-beta-features", "x-openai-internal-codex-responses-lite",
                "x-request-id", "openai-processing-ms"}


def safe_headers(headers):
    return {name.lower(): value if name.lower() in SAFE_HEADERS else "[redacted]"
            for name, value in headers.items()}


def inference(flow):
    host = flow.request.host
    return (host in ["api.openai.com", "chatgpt.com"] or host.endswith(".openai.com")) \
        and "/responses" in flow.request.path.split("?", 1)[0]


def record(flow, kind, **fields):
    path = os.environ["EXPERIMENT_CAPTURE_FILE"]
    event = {"kind": kind, "time": time.monotonic(),
             "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "connection": flow.id, "host": flow.request.host,
             "path": flow.request.path.split("?", 1)[0], **fields}
    with Path(path).open("a") as file:
        file.write(json.dumps(event) + "\n")


def message(flow, direction, text, transport):
    try:
        body = json.loads(text)
    except ValueError:
        body = None
    record(flow, "message", direction=direction, transport=transport,
           text=text, body=body)


def request(flow):
    record(flow, "http_request", method=flow.request.method,
           headers=safe_headers(flow.request.headers))
    if inference(flow) and flow.request.raw_content:
        message(flow, "out", flow.request.get_text(strict=False), "http")


def responseheaders(flow):
    record(flow, "http_response", status=flow.response.status_code,
           headers=safe_headers(flow.response.headers))
    if not inference(flow) or flow.response.status_code == 101:
        return
    # Observe streaming chunks and return the exact bytes immediately.
    buffer = bytearray()
    sse = "text/event-stream" in flow.response.headers.get("content-type", "")

    def observe(chunk):
        buffer.extend(chunk)
        if sse:
            while b"\n" in buffer:
                line, remainder = bytes(buffer).split(b"\n", 1)
                buffer[:] = remainder
                if line.startswith(b"data:"):
                    message(flow, "in", line[5:].strip().decode("utf-8"), "sse")
        if not chunk and buffer:
            message(flow, "in", bytes(buffer).decode("utf-8", errors="replace"), "http")
        return chunk

    flow.response.stream = observe


def websocket_message(flow):
    if inference(flow):
        latest = flow.websocket.messages[-1]
        message(flow, "out" if latest.from_client else "in",
                latest.content.decode("utf-8"), "websocket")


def error(flow):
    record(flow, "transport_error")  # Error strings can include private URLs.
