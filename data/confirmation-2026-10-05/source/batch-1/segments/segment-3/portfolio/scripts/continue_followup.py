"""Manually continue a stopped follow-up; retain every earlier attempt."""
import argparse
from pathlib import Path

from common import DEFAULT_CODEX, ROOT, file_hash, native_codex, read_json, write_json
from run import run


def progress(original, segments):
    """Match immutable segment records to the original schedule, without grading."""
    plans = read_json(original / 'plan.json')
    completed, failures = {}, []
    for experiment in plans:
        task = experiment['settings']['benchmark']
        completed[task] = []
        for segment, root in enumerate([original, *segments], 1):
            folder = root / task
            if not (folder / 'runs.json').exists():
                continue
            manifest = read_json(folder / 'manifest.json')
            rows = read_json(folder / 'runs.json')
            offset = len(completed[task])
            assert manifest['settings'] == experiment['settings']
            assert manifest['schedule'] == experiment['schedule'][offset:]
            assert len(rows) <= len(manifest['schedule'])
            for index, row in enumerate(rows):
                slot = offset + index + 1
                job = experiment['schedule'][slot - 1]
                assert all(row[key] == value for key, value in job.items())
                if row['eligible']:
                    completed[task].append((segment, folder, row))
                else:
                    assert index == len(rows) - 1 and row['status'] == 'failed'
                    assert row['identical_request_verified']
                    wire = read_json_lines(folder / f"{row['number']:02d}-wire.jsonl")
                    error = next(event['body']['response']['error'] for event in wire
                                 if (event.get('body') or {}).get('type') == 'response.failed')
                    assert error['code'] == 'server_is_overloaded'
                    failures.append({'task': task, 'scheduled_number': slot,
                        **{key: row[key] for key in ['model', 'effort', 'repeat', 'auth', 'status']},
                        'server_error': error, 'answer': None, 'reasoning_tokens': None,
                        'sent_body_sha256': row['sent_body_sha256'],
                        'source_log_sha256': {'wire': file_hash(folder / f"{row['number']:02d}-wire.jsonl"),
                                              'native': file_hash(folder / f"{row['number']:02d}-events.jsonl")},
                        'manifest_sha256': file_hash(folder / 'manifest.json'),
                        'runs_sha256': file_hash(folder / 'runs.json')})
    return plans, completed, failures


def read_json_lines(path):
    import json
    return [json.loads(line) for line in path.read_text().splitlines()]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--segment', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    plans, completed, failures = progress(args.original, args.segment)
    assert failures, 'This utility is only for explicitly inspected capacity failures.'
    write_json(ROOT / 'plans/confirmation-runtime-errors.json', {'failures': failures,
               'scope': 'Every failed attempt retained separately; completed-response statistics exclude unavailable answers.'})
    experiments = [{**plan, 'schedule': plan['schedule'][len(completed[plan['settings']['benchmark']]):]}
                   for plan in plans]
    count = sum(len(rows) for rows in completed.values())
    print(f'{count} completed responses retained; {480-count} scheduled responses remain; {len(failures)} failures preserved.', flush=True)
    if args.execute:
        binary = native_codex(DEFAULT_CODEX)
        manifest = read_json(args.original / 'portfolio/manifest.json')
        assert file_hash(Path(binary)) == manifest['codex_sha256']
        args.output.mkdir(parents=True, exist_ok=False)
        write_json(args.output / 'plan.json', experiments)
        write_json(args.output / 'continuation.json', {
            'completed_by_task': {task: len(rows) for task, rows in completed.items()},
            'failures_retained': len(failures),
            'original_manifest_sha256': file_hash(args.original / 'portfolio/manifest.json'),
            'original_runs_sha256': file_hash(args.original / 'portfolio/runs.json')})
        for experiment in experiments:
            if experiment['schedule']:
                run(binary, (args.output / experiment['settings']['benchmark']).resolve(),
                    experiment['settings'], experiment['schedule'])
