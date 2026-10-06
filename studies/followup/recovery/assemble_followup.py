"""Assemble an audited completed-response view; never change raw segments."""
import argparse
import shutil
from pathlib import Path

from audit import audit
from common import ROOT, file_hash, read_json, write_json
from continue_followup import progress

# These files define the model requests, native collection and reference grades.
CORE = ['prompt.txt', 'problem.json', 'expected.json', 'settings.json',
        'config/controlled.toml', 'config/base-instructions.txt',
        *[f'scripts/{name}.py' for name in ['run', 'common', 'codex_client', 'capture',
          'capture_addon', 'identical', 'identical_addon', 'native_control', 'check_answer', 'bookstore']]]


def assemble(original, segments, output):
    plans, completed, failures = progress(original, segments)
    assert sum(len(rows) for rows in completed.values()) == 480
    assert failures == read_json(ROOT / 'plans/confirmation-runtime-errors.json')['failures']
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'plan.json', plans)
    all_rows = []
    for experiment in plans:
        task = experiment['settings']['benchmark']
        records = completed[task]
        assert len(records) == 240
        destination = output / task
        destination.mkdir()
        first = records[0][1]
        manifest = read_json(first / 'manifest.json')
        source_hashes, source_segments = {}, []
        folders = {(segment, folder) for segment, folder, _ in records}
        for segment, folder in sorted(folders):
            current = read_json(folder / 'manifest.json')
            assert current['codex_sha256'] == manifest['codex_sha256']
            for name in CORE:
                assert current['source_sha256'][name] == manifest['source_sha256'][name]
            for name, expected in current['source_sha256'].items():
                assert file_hash(folder / 'source' / name) == expected
                archived = f'segments/segment-{segment}/{task}/{name}'
                target = destination / 'source' / archived
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(folder / 'source' / name, target)
                source_hashes[archived] = expected
            source_segments.append({'segment': segment, 'manifest_sha256': file_hash(folder / 'manifest.json'),
                                    'runs_sha256': file_hash(folder / 'runs.json')})
        canonical = CORE + (['benchmarks/bookstore/prompt.txt', 'benchmarks/bookstore/rubric.json'] if task == 'bookstore' else [])
        for name in canonical:
            target = destination / 'source' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(first / 'source' / name, target)
            source_hashes[name] = file_hash(target)
        for name in ['request-headers.json', 'sign-ins.json', *manifest['request_body_sha256']]:
            if name != 'sign-ins.json':
                assert all((folder / name).read_bytes() == (first / name).read_bytes() for _, folder in folders)
            shutil.copy2(first / name, destination / name)
        rows, origins = [], []
        for number, (segment, folder, row) in enumerate(records, 1):
            for suffix in ['wire', 'events']:
                shutil.copy2(folder / f"{row['number']:02d}-{suffix}.jsonl", destination / f'{number:02d}-{suffix}.jsonl')
            rows.append({**row, 'number': number})
            origins.append({'number': number, 'segment': segment, 'original_number': row['number']})
        manifest.update(settings=experiment['settings'], schedule=experiment['schedule'], source_sha256=source_hashes,
                        assembly={'segments': source_segments, 'record_origins': origins,
                                  'failed_attempts_retained_separately': len(failures)})
        write_json(destination / 'manifest.json', manifest)
        write_json(destination / 'runs.json', rows)
        audit(destination)
        all_rows.extend(rows)
    failed_rows = []
    for root in [original, *segments]:
        for task in ['portfolio', 'bookstore']:
            path = root / task / 'runs.json'
            if path.exists():
                failed_rows.extend(row for row in read_json(path) if not row['eligible'])
    attempts = all_rows + failed_rows
    assert len({row['thread_id'] for row in attempts}) == len(attempts)
    assert len({row['turn_id'] for row in attempts}) == len(attempts)
    write_json(output / 'failures.json', {'failures': failures, 'completed_responses': 480, 'total_attempts': len(attempts)})
    print(f'480 completed responses assembled and audited; {len(attempts)} distinct attempts. Raw segments untouched.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--segment', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assemble(args.original, args.segment, args.output)
