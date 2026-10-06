"""Audit synthetic wire evidence for both tasks and detect corrupt usage."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit import audit, digest
from common import write_json
from identical import payload, PROTOCOL_HEADERS


def evidence(directory, task, answer):
    source = directory / 'source'
    source.mkdir()
    expected = {'value': 1}
    if task == 'bookstore':
        reference = source / 'benchmarks/bookstore/rubric.json'
        reference.parent.mkdir(parents=True)
        write_json(reference, {'expected_decisions': expected})
    else:
        reference = source / 'expected.json'
        write_json(reference, expected)
    body_file = directory / 'request-gpt-6-luna-medium.json'
    write_json(body_file, payload('task', 'instructions', 'gpt-6-luna', 'medium'))
    write_json(directory / 'request-headers.json', PROTOCOL_HEADERS)
    native_usage = {'inputTokens': 10, 'outputTokens': 5, 'totalTokens': 15,
                    'reasoningOutputTokens': 2, 'cachedInputTokens': 0, 'cacheWriteInputTokens': 0}
    server_usage = {'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15,
                    'output_tokens_details': {'reasoning_tokens': 2},
                    'input_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 0}}
    runs, schedule = [], []
    for number, auth in enumerate(['api', 'chatgpt'], 1):
        job = {'model': 'gpt-6-luna', 'effort': 'medium', 'auth': auth, 'repeat': 1}
        schedule.append(job)
        run = {'number': number, **job, 'thread_id': f'thread-{number}', 'turn_id': f'turn-{number}',
               'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15, 'reasoning_tokens': 2,
               'cached_input_tokens': 0, 'cache_write_input_tokens': 0,
               'seconds': 2, 'first_text_seconds': 1, 'wire_seconds': 2, 'wire_first_text_seconds': 1,
               'answer': answer, 'server_answer': answer, 'correct': answer == '{"value": 1}',
               'score': int(answer == '{"value": 1}'), 'eligible': True, 'flags': [],
               'identical_request_verified': True, 'sent_body_sha256': digest(body_file)}
        runs.append(run)
        response = {'id': f'response-{number}', 'model': job['model'], 'reasoning': {'effort': 'medium'},
                    'status': 'completed', 'error': None, 'usage': server_usage, 'output': [{'type': 'message'}]}
        wire = [{'kind': 'message', 'direction': 'out', 'text': body_file.read_text(),
                 'body': json.loads(body_file.read_text())},
                {'kind': 'controlled_headers', 'headers': PROTOCOL_HEADERS},
                {'kind': 'message', 'direction': 'in', 'body': {'type': 'response.completed', 'response': response}},
                {'kind': 'message', 'direction': 'in', 'body': {'type': 'response.output_text.done', 'text': answer}}]
        (directory / f'{number:02d}-wire.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in wire))
        (directory / f'{number:02d}-events.jsonl').write_text(json.dumps(
            {'method': 'thread/tokenUsage/updated', 'params': {'tokenUsage': {'total': native_usage}}}) + '\n')
    write_json(directory / 'runs.json', runs)
    write_json(directory / 'manifest.json', {'settings': {'benchmark': task}, 'schedule': schedule,
        'codex_path': '/nonexistent-test-codex', 'codex_sha256': 'unavailable-on-this-machine',
        'source_sha256': {str(reference.relative_to(source)): digest(reference)},
        'request_body_sha256': {body_file.name: digest(body_file)},
        'protocol_headers_sha256': digest(directory / 'request-headers.json')})


class AuditTests(unittest.TestCase):
    def test_both_tasks_accept_correct_and_malformed_completed_answers(self):
        for task in ['portfolio', 'bookstore']:
            for answer in ['{"value": 1}', 'malformed answer']:
                with self.subTest(task=task, answer=answer), tempfile.TemporaryDirectory() as name:
                    directory = Path(name)
                    evidence(directory, task, answer)
                    self.assertTrue(audit(directory)['passed'])

    def test_corrupt_server_usage_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            evidence(directory, 'portfolio', '{"value": 1}')
            path = directory / '01-wire.jsonl'
            events = [json.loads(line) for line in path.read_text().splitlines()]
            events[2]['body']['response']['usage']['output_tokens_details']['reasoning_tokens'] = 3
            path.write_text(''.join(json.dumps(e) + '\n' for e in events))
            with self.assertRaises(AssertionError):
                audit(directory)
            self.assertFalse((directory / 'audit.json').exists())
