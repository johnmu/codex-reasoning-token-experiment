"""Manually continue this follow-up after its documented first-of-pair failure."""
import argparse
from pathlib import Path

from common import DEFAULT_CODEX, file_hash, native_codex, read_json, write_json
from run import run


def continuation(original):
    experiments = read_json(original / 'plan.json')
    rows = read_json(original / 'portfolio/runs.json')
    assert len(rows) == 101 and rows[-1]['status'] == 'failed'
    assert all(row['eligible'] for row in rows[:-1])
    assert rows[-1]['auth'] == 'chatgpt' and rows[-1]['effort'] == 'medium'
    assert all(all(row[key] == value for key, value in job.items())
               for row, job in zip(rows, experiments[0]['schedule']))
    return [{**experiments[0], 'schedule': experiments[0]['schedule'][100:]}, experiments[1]]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    experiments = continuation(args.original)
    print('100 completed responses retained; 380 scheduled responses remain, including one manual retry.', flush=True)
    if args.execute:
        binary = native_codex(DEFAULT_CODEX)
        manifest = read_json(args.original / 'portfolio/manifest.json')
        assert file_hash(Path(binary)) == manifest['codex_sha256']
        args.output.mkdir(parents=True, exist_ok=False)
        write_json(args.output / 'plan.json', experiments)
        write_json(args.output / 'continuation.json', {
            'completed_prefix': 100, 'manual_retry_of_original_number': 101,
            'original_manifest_sha256': file_hash(args.original / 'portfolio/manifest.json'),
            'original_runs_sha256': file_hash(args.original / 'portfolio/runs.json')})
        for experiment in experiments:
            run(binary, (args.output / experiment['settings']['benchmark']).resolve(),
                experiment['settings'], experiment['schedule'])
