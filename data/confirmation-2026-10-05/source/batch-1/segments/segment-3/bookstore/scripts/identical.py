"""Build one neutral, stateless request. Both sign-ins send these exact bytes."""
import hashlib

PROTOCOL_HEADERS = {
    "user-agent": "reasoning-token-experiment/identical-v1",
    "originator": "reasoning_token_experiment",
    "openai-beta": "responses_websockets=2026-02-06"
}


def payload(prompt, instructions, model, effort):
    # Keep this explicit: it is the entire model input, not a native-body merge.
    return {
        "type": "response.create",
        "model": model,
        "instructions": instructions,
        "input": [{
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}]
        }],
        "reasoning": {"effort": effort},
        "text": {"verbosity": "low"},
        "tools": [],
        "tool_choice": "none",
        "parallel_tool_calls": False,
        "include": ["reasoning.encrypted_content"],
        "store": False,
        "service_tier": "default"
    }


def verify_sent(events, expected_bytes, expected_headers):
    sent = [e for e in events if e.get("direction") == "out"]
    headers = [e for e in events if e.get("kind") == "controlled_headers"]
    flags = []
    if len(sent) != 1 or sent[0].get("text", "").encode() != expected_bytes:
        flags.append("sent_body_not_identical_to_frozen_request")
    if len(headers) != 1 or headers[0]["headers"] != expected_headers:
        flags.append("protocol_headers_not_identical_to_frozen_headers")
    if any(e.get("kind") == "blocked_request" for e in events):
        flags.append("unexpected_request_blocked")
    return {"sent_body_sha256": hashlib.sha256(sent[0]["text"].encode()).hexdigest() if len(sent) == 1 else None,
            "identical_request_verified": not flags, "identical_request_flags": flags}
