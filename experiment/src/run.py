"""Compare reasoning tokens through separate API and ChatGPT Codex sign-ins."""
import argparse
import datetime
import json
import random
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from common import DEFAULT_CODEX, ROOT, file_hash, read_json, write_json, native_codex
from codex_client import CodexClient
from check_answer import solve
from bookstore import grade as grade_bookstore
from capture import Capture, summarize_wire
from identical import payload as identical_payload, PROTOCOL_HEADERS, verify_sent


def make_schedule(settings):
    """Shuffle matched pairs; balance which sign-in goes first."""
    randomizer = random.Random(settings["random_seed"])
    pairs = [(model, effort, repeat)
             for repeat in range(1, settings.get("repeats", 1) + 1)
             for model in settings["models"] for effort in settings["efforts"]]
    randomizer.shuffle(pairs)
    first_sign_ins = ["api"] * (len(pairs) // 2)
    first_sign_ins += ["chatgpt"] * (len(pairs) - len(first_sign_ins))
    randomizer.shuffle(first_sign_ins)
    schedule = []
    for (model, effort, repeat), first in zip(pairs, first_sign_ins):
        second = "chatgpt" if first == "api" else "api"
        for auth in [first, second]:
            schedule.append({"model": model, "effort": effort, "repeat": repeat, "auth": auth})
    return schedule


def check_available(models, settings):
    for name in settings["models"]:
        model = next((model for model in models if model["model"] == name), None)
        efforts = {item["reasoningEffort"] for item in model["supportedReasoningEfforts"]} if model else set()
        if not set(settings["efforts"]) <= efforts:
            raise RuntimeError(f"Requested model/efforts unavailable: {name}")


def preflight(binary, settings, label="preflight"):
    """Read sign-in types and model capabilities. Never start a model turn."""
    accounts = {}
    for auth in ["api", "chatgpt"]:
        private_log = ROOT / ".local" / auth / f"{label}-stderr.txt"
        client = CodexClient(binary, auth, private_log)
        try:
            accounts[auth] = client.check_login(auth)
            catalogue = client.list_models()
            check_available(catalogue, settings)
            accounts[auth]["selected_models"] = [
                model for model in catalogue if model["model"] in settings["models"]]
        finally:
            client.close()
    return accounts


def measure(client, model, effort, prompt, instructions, workspace, timeout):
    """Start a fresh thread; keep its final cumulative token count once."""
    thread = client.request("thread/start", {
        "model": model, "modelProvider": "openai", "allowProviderModelFallback": False,
        "cwd": str(workspace), "ephemeral": True, "sandbox": "read-only",
        "approvalPolicy": "never", "personality": "none", "serviceTier": "default",
        "baseInstructions": instructions, "developerInstructions": "", "dynamicTools": [],
        "config": {"model_reasoning_effort": effort}})
    if thread["model"] != model or thread.get("reasoningEffort") != effort:
        raise RuntimeError("Codex changed the requested model or effort; no turn started")
    if thread.get("instructionSources"):
        raise RuntimeError("Extra instruction files loaded; no turn started")
    thread_id = thread["thread"]["id"]
    client.pending.clear()
    start = time.monotonic()
    turn = client.request("turn/start", {
        "threadId": thread_id, "model": model, "effort": effort,
        "input": [{"type": "text", "text": prompt}], "summary": "none",
        "personality": "none", "serviceTierForTurn": "default"})
    turn_id = turn["turn"]["id"]
    usage, answers, flags = {}, {}, []
    first_text_seconds = None
    while True:
        remaining = timeout - (time.monotonic() - start)
        if remaining <= 0:
            raise TimeoutError("Model turn exceeded its time limit")
        message = client.next_event(remaining)
        method, data = message.get("method"), message.get("params", {})
        if data.get("threadId") not in [None, thread_id] or data.get("turnId") not in [None, turn_id]:
            continue
        if message.get("rejected_server_request"):
            flags.append("unexpected_server_request")
        if method == "item/agentMessage/delta" and data.get("delta") and first_text_seconds is None:
            first_text_seconds = time.monotonic() - start
        if method == "thread/tokenUsage/updated":
            # total is cumulative. Replacing it avoids double-counting repeated events.
            usage = data["tokenUsage"]["total"]
        if method in ["item/started", "item/completed"]:
            item = data["item"]
            if item["type"] not in ["userMessage", "agentMessage", "reasoning"]:
                flags.append(item["type"])
            if method == "item/completed" and item["type"] == "agentMessage":
                if item.get("phase") == "commentary":
                    flags.append("unexpected_commentary")
                else:
                    answers[item["id"]] = item["text"]
        if method in ["error", "model/rerouted", "invalid_json"]:
            flags.append(method)
        if method == "turn/completed" and data["turn"]["id"] == turn_id:
            status = data["turn"]["status"]
            break
    reasoning = usage.get("reasoningOutputTokens")
    if type(reasoning) is not int or reasoning < 0:
        reasoning = None
        flags.append("missing_reasoning_tokens")
    if len(answers) != 1:
        flags.append("missing_or_multiple_answers")
    return {
        "thread_id": thread_id, "turn_id": turn_id,
        "status": status, "seconds": time.monotonic() - start,
        "first_text_seconds": first_text_seconds,
        "reasoning_tokens": reasoning, "input_tokens": usage.get("inputTokens"),
        "cached_input_tokens": usage.get("cachedInputTokens"),
        "cache_write_input_tokens": usage.get("cacheWriteInputTokens"),
        "output_tokens": usage.get("outputTokens"), "total_tokens": usage.get("totalTokens"),
        "answer": "\n".join(answers.values()), "raw_usage": usage,
        "flags": sorted(set(flags)), "eligible": status == "completed" and not flags,
        "configured_settings": {key: thread.get(key) for key in
                               ["model", "reasoningEffort", "serviceTier", "instructionSources"]}}


def is_correct(answer, expected):
    """Compare exact JSON values, including integer types and project order."""
    try:
        return json.dumps(json.loads(answer), sort_keys=True) == json.dumps(expected, sort_keys=True)
    except ValueError:
        return False


def save_source(output, binary, settings, schedule):
    """Store the actual source beside the results, so later edits cannot obscure it."""
    source = output / "source"
    files = [ROOT / name for name in ["README.md", "experiment/config/settings.json",
             "experiment/tasks/portfolio/prompt.txt", "experiment/tasks/portfolio/problem.json",
             "experiment/tasks/portfolio/expected.json", "experiment/config/controlled.toml",
             "experiment/config/base-instructions.txt", "experiment/__init__.py", "experiment/__main__.py"]]
    files += sorted((ROOT / "experiment/src").glob("*.py"))
    files += sorted((ROOT / "tests").glob("*.py"))
    if settings.get("benchmark") == "bookstore":
        files += sorted((ROOT / "experiment/tasks/bookstore").glob("*"))
    if settings.get("capture"):
        files += [ROOT / "experiment/requirements.txt"]
    hashes = {}
    for path in files:
        relative = path.relative_to(ROOT)
        copy = source / relative
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)
        hashes[str(relative)] = file_hash(path)
    executable = Path(shutil.which(binary) or binary).resolve()
    version = subprocess.check_output([binary, "--version"], text=True).strip()
    write_json(output / "manifest.json", {
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "codex_path": str(executable), "codex_version": version, "codex_sha256": file_hash(executable),
        "settings": settings, "schedule": schedule, "source_sha256": hashes,
        "model_revision": None,
        "capture_method": ("frozen identical request through native Codex authentication/routes" if settings.get("identical")
                           else "loopback TLS MITM; native routes and bodies preserved" if settings.get("capture") else None)})


def run(binary, output, settings, schedule):
    if settings.get("benchmark") == "bookstore":
        prompt = (ROOT / "experiment/tasks/bookstore/prompt.txt").read_text()
        rubric = read_json(ROOT / "experiment/tasks/bookstore/rubric.json")
    else:
        prompt = (ROOT / "experiment/tasks/portfolio/prompt.txt").read_text()
        problem = read_json(ROOT / "experiment/tasks/portfolio/problem.json")
        instance = json.loads(prompt.rsplit("Here is the complete instance:\n", 1)[1])
        if instance != problem:
            raise RuntimeError("Prompt and reference problem differ")
        expected = read_json(ROOT / "experiment/tasks/portfolio/expected.json")
        reference, _ = solve(problem)
        if not is_correct(json.dumps(reference), expected):
            raise RuntimeError("Reference answer failed local verification")
    output.mkdir(parents=True, exist_ok=False)  # Never replace previous evidence.
    save_source(output, binary, settings, schedule)
    instructions = (ROOT / "experiment/config/base-instructions.txt").read_text()
    frozen_requests, request_hashes = {}, {}
    headers_hash = None
    if settings.get("identical"):
        write_json(output / "request-headers.json", PROTOCOL_HEADERS)
        headers_hash = file_hash(output / "request-headers.json")
        for model in settings["models"]:
            for effort in settings["efforts"]:
                path = output / f"request-{model}-{effort}.json"
                write_json(path, identical_payload(prompt, instructions, model, effort))
                frozen_requests[model, effort] = path
                request_hashes[path.name] = file_hash(path)
        manifest = read_json(output / "manifest.json")
        manifest.update(request_body_sha256=request_hashes, protocol_headers_sha256=headers_hash)
        write_json(output / "manifest.json", manifest)
    records = []
    try:
        accounts = preflight(binary, settings, output.name)
        write_json(output / "sign-ins.json", accounts)
        with tempfile.TemporaryDirectory(prefix="reasoning-test-") as workspace:
            for number, job in enumerate(schedule, 1):
                record = {"number": number, **job}
                client, capture = None, None
                with (output / f"{number:02d}-events.jsonl").open("w") as log:
                    try:
                        # Every response gets a new process and a fresh ephemeral thread.
                        private_log = ROOT / ".local" / job["auth"] / f"{output.name}-{number:02d}-stderr.txt"
                        if settings.get("capture"):
                            frozen = frozen_requests.get((job["model"], job["effort"]))
                            digest = request_hashes[frozen.name] if frozen else None
                            capture = Capture(output / f"{number:02d}-wire.jsonl", frozen, digest, headers_hash)
                        environment = capture.environment() if capture else None
                        client = CodexClient(binary, job["auth"], private_log, environment)
                        client.check_login(job["auth"])
                        client.log = log
                        record.update(measure(client, job["model"], job["effort"], prompt,
                                              instructions, Path(workspace).resolve(), settings["timeout_seconds"]))
                        if capture:
                            record.update(summarize_wire(capture.output, record["raw_usage"]))
                            if settings.get("identical"):
                                events = [json.loads(line) for line in capture.output.read_text().splitlines()]
                                verified = verify_sent(events, frozen.read_bytes(), PROTOCOL_HEADERS)
                                if file_hash(frozen) != digest:
                                    verified["identical_request_flags"].append("frozen_file_changed")
                                    verified["identical_request_verified"] = False
                                record.update(verified)
                                record["wire_flags"] += verified["identical_request_flags"]
                            if record.get("sent_model") != job["model"] or record.get("sent_effort") != job["effort"]:
                                record["wire_flags"].append("sent_model_or_effort_mismatch")
                            if record.get("server_model") != job["model"]:
                                record["wire_flags"].append("server_model_mismatch")
                            if record.get("server_declared_effort") not in [None, job["effort"]]:
                                record["wire_flags"].append("server_declared_effort_mismatch")
                            if record.get("server_answer") != record["answer"]:
                                record["wire_flags"].append("server_native_answer_mismatch")
                            record["flags"] += record["wire_flags"]
                            record["eligible"] = record["eligible"] and not record["wire_flags"]
                        if settings.get("benchmark") == "bookstore":
                            record.update(grade_bookstore(record["answer"], rubric))
                        else:
                            record["correct"] = is_correct(record["answer"], expected)
                    except Exception as error:
                        record.update(status="error", eligible=False, error=str(error))
                    finally:
                        if client:
                            client.log = None
                            client.close()
                        if capture:
                            capture.close()
                records.append(record)
                write_json(output / "runs.json", records)
                print(f"{number:02d}: {job['model']} {job['effort']} {job['auth']}: {record['status']}")
                if not record["eligible"]:
                    raise RuntimeError("Stopped for inspection. Attempt retained; no automatic retry.")
    except Exception as error:
        (output / "error.txt").write_text(str(error) + "\n")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Make the previewed model calls")
    parser.add_argument("--check", action="store_true", help="Check sign-ins and capabilities without model calls")
    parser.add_argument("--smoke", action="store_true", help="Only Luna Low: one response per sign-in")
    parser.add_argument("--model", help="Run only this exact model")
    parser.add_argument("--effort", choices=["low", "medium", "high", "max"])
    parser.add_argument("--benchmark", choices=["portfolio", "bookstore", "both"], default="portfolio")
    parser.add_argument("--capture", action="store_true", help="Record real requests/responses through a local MITM")
    parser.add_argument("--native-requests", action="store_true", help="Observe unmodified Codex requests; not an identical-request experiment")
    parser.add_argument("--repeats", type=int, default=1, help="Responses per model/effort/sign-in")
    parser.add_argument("--seed", type=int, help="Randomize pair order using this saved seed")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--codex", default=DEFAULT_CODEX)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    settings = read_json(ROOT / "experiment/config/settings.json")
    settings["identical"] = not args.native_requests
    settings["capture"] = args.capture or settings["identical"]
    settings["repeats"] = args.repeats
    if args.seed is not None:
        settings["random_seed"] = args.seed
    if args.model:
        settings["models"] = [args.model]
    if args.effort:
        settings["efforts"] = [args.effort]
    if args.smoke:
        settings = {**settings, "models": ["gpt-6-luna"], "efforts": ["low"], "repeats": 1}
    benchmarks = ["portfolio", "bookstore"] if args.benchmark == "both" else [args.benchmark]
    experiments = []
    for benchmark in benchmarks:
        task_settings = {**settings, "benchmark": benchmark}
        experiments.append({"settings": task_settings, "schedule": make_schedule(task_settings)})
    if args.check and args.execute:
        parser.error("--check and --execute are separate actions")
    if args.check or args.execute:
        args.codex = native_codex(args.codex)
    if args.check:
        accounts = preflight(args.codex, settings)
        write_json(ROOT / "output/preflight.json", {"settings": settings, "sign_ins": accounts})
        print("Both sign-ins and all requested model/effort capabilities passed. No model turns started.")
    elif args.execute:
        output = args.output or ROOT / "output/raw" / ("smoke" if args.smoke else "initial")
        if len(experiments) > 1:
            output.mkdir(parents=True, exist_ok=False)
            write_json(output / "plan.json", experiments)
        for experiment in experiments:
            task = experiment["settings"]["benchmark"]
            destination = output / task if len(experiments) > 1 else output
            run(args.codex, destination.resolve(), experiment["settings"], experiment["schedule"])
    else:
        print(json.dumps(experiments, indent=2))
        total = sum(len(experiment["schedule"]) for experiment in experiments)
        print(f"Preview only: {total} responses; no model calls.")
