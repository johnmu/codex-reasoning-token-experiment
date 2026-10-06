"""Two diagnostic responses through ordinary `codex exec`, without the adapter."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from common import DEFAULT_CODEX, ROOT, codex_environment, read_json, write_json
from run import is_correct, make_schedule, save_source


def control(output):
    settings = {**read_json(ROOT / 'settings.json'), 'models': ['gpt-6-luna'],
                'efforts': ['medium'], 'repeats': 1}
    schedule = make_schedule(settings)
    output.mkdir(parents=True, exist_ok=False)
    save_source(output, DEFAULT_CODEX, settings, schedule)
    manifest = read_json(output / 'manifest.json')
    manifest['method'] = 'native codex exec control, using model-default base instructions'
    write_json(output / 'manifest.json', manifest)
    prompt = (ROOT / 'prompt.txt').read_text()
    expected = read_json(ROOT / 'expected.json')
    records = []
    for number, job in enumerate(schedule, 1):
        environment = codex_environment(job['auth'])
        # Traces stay private. They may contain authenticated transport details.
        environment['RUST_LOG'] = 'codex_api=trace,codex_core::client=trace'
        trace = ROOT / '.local' / job['auth'] / f'{output.name}-native-trace.txt'
        command = [DEFAULT_CODEX, 'exec', '--json', '--ephemeral', '--skip-git-repo-check',
                   '--ignore-rules', '--strict-config', '-m', job['model'],
                   '-c', 'model_reasoning_effort="medium"',
                   '-c', 'service_tier="default"', '-c', 'approval_policy="never"',
                   '-s', 'read-only']
        event_path = output / f'{number:02d}-native-events.jsonl'
        # Keep partial evidence even if the process fails or times out.
        with tempfile.TemporaryDirectory(prefix='codex-native-control-') as workspace:
            command += ['-C', workspace, '-']
            with trace.open('w') as stderr, event_path.open('w') as stdout:
                try:
                    result = subprocess.run(command, input=prompt, text=True, stdout=stdout,
                                            stderr=stderr, env=environment,
                                            timeout=settings['timeout_seconds'])
                except Exception as error:
                    records.append({'number': number, **job, 'status': 'error', 'error': str(error)})
                    write_json(output / 'native-runs.json', records)
                    raise
        events = [json.loads(line) for line in event_path.read_text().splitlines()]
        replies = [event['item']['text'] for event in events
                   if event.get('type') == 'item.completed'
                   and event.get('item', {}).get('type') == 'agent_message'
                   and event['item'].get('phase') != 'commentary']
        usage = next((event.get('usage', {}) for event in reversed(events)
                      if event.get('type') == 'turn.completed'), {})
        answer = replies[-1] if replies else ''
        records.append({'number': number, **job, 'exit_code': result.returncode,
                        'answer': answer, 'correct': is_correct(answer, expected),
                        'raw_native_usage': usage,
                        'reasoning_tokens': usage.get('reasoning_output_tokens')})
        write_json(output / 'native-runs.json', records)
        print(job['auth'], 'exit:', result.returncode, 'correct:', records[-1]['correct'])
        if result.returncode:
            raise RuntimeError('Control failed. Evidence retained; no automatic retry.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'results/native-cli-control')
    args = parser.parse_args()
    if args.execute:
        control(args.output.resolve())
    else:
        print('Preview: one Luna Medium response per sign-in (2 total). No model calls.')
