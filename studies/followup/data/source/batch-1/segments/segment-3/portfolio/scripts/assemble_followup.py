"""Copy completed evidence into an audited view; preserve both raw collections."""
import argparse
import shutil
from pathlib import Path

from audit import audit
from common import ROOT, file_hash, read_json, write_json


def assemble(original, continuation, output):
    failure = read_json(ROOT / 'plans/confirmation-capacity-error.json')
    first = original / 'portfolio'
    assert file_hash(first / 'runs.json') == failure['original_runs_sha256']
    assert file_hash(first / 'manifest.json') == failure['original_manifest_sha256']
    for suffix, name in [('wire', 'wire'), ('events', 'native')]:
        assert file_hash(first / f'101-{suffix}.jsonl') == failure['source_log_sha256'][name]
    initial_rows = read_json(first / 'runs.json')
    assert len(initial_rows) == 101 and not initial_rows[-1]['eligible']
    assert all(row['eligible'] for row in initial_rows[:100])
    plans = read_json(original / 'plan.json')
    audit(continuation / 'portfolio')
    audit(continuation / 'bookstore')
    resumed_rows = read_json(continuation / 'portfolio/runs.json')
    assert len(resumed_rows) == 140
    assert len(read_json(continuation / 'bookstore/runs.json')) == 240
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'plan.json', plans)
    destination = output / 'portfolio'
    destination.mkdir()
    manifest = read_json(first / 'manifest.json')
    resumed_manifest = read_json(continuation / 'portfolio/manifest.json')
    assert manifest['settings'] == resumed_manifest['settings']
    assert manifest['schedule'][100:] == resumed_manifest['schedule']
    assert manifest['codex_sha256'] == resumed_manifest['codex_sha256']
    source_hashes = {}
    for folder in [first, continuation / 'portfolio']:
        current = read_json(folder / 'manifest.json')
        for name, expected in current['source_sha256'].items():
            assert file_hash(folder / 'source' / name) == expected
            assert name not in source_hashes or source_hashes[name] == expected
            source_hashes[name] = expected
            target = destination / 'source' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(folder / 'source' / name, target)
    for name in ['request-headers.json', 'sign-ins.json', *manifest['request_body_sha256']]:
        if name != 'sign-ins.json':
            assert (first / name).read_bytes() == (continuation / 'portfolio' / name).read_bytes()
        shutil.copy2(first / name, destination / name)
    combined = []
    for folder, rows, offset in [(first, initial_rows[:100], 0), (continuation / 'portfolio', resumed_rows, 100)]:
        for row in rows:
            number = row['number'] + offset
            for suffix in ['wire', 'events']:
                shutil.copy2(folder / f"{row['number']:02d}-{suffix}.jsonl", destination / f'{number:02d}-{suffix}.jsonl')
            combined.append({**row, 'number': number})
    manifest['source_sha256'] = source_hashes
    manifest['assembly'] = {'completed_prefix': 100, 'continuation_responses': 140, 'failed_attempts_retained_separately': 1,
                            'segment_manifest_sha256': [file_hash(first / 'manifest.json'), file_hash(continuation / 'portfolio/manifest.json')]}
    write_json(destination / 'manifest.json', manifest)
    write_json(destination / 'runs.json', combined)
    shutil.copytree(continuation / 'bookstore', output / 'bookstore')
    for task, planned in zip(['portfolio', 'bookstore'], plans):
        task_manifest = read_json(output / task / 'manifest.json')
        assert task_manifest['settings'] == planned['settings']
        assert task_manifest['schedule'] == planned['schedule']
        audit(output / task)
    all_rows = combined + read_json(output / 'bookstore/runs.json') + [initial_rows[-1]]
    assert len({row['thread_id'] for row in all_rows}) == 481
    assert len({row['turn_id'] for row in all_rows}) == 481
    print('480 completed responses assembled and audited; all 481 attempts have distinct threads and turns. Original captures untouched.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('continuation', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assemble(args.original, args.continuation, args.output)
