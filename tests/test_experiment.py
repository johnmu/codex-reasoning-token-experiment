"""Offline checks; these tests never call a model or read real credentials."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiment/src"))
from common import ROOT, codex_environment, read_json, write_json
from check_answer import solve
from run import make_schedule, measure, is_correct, check_available, preflight, save_source
from summarize import summarize
from bookstore import grade as grade_bookstore


class FakeClient:
    def __init__(self, events, fallback=False):
        self.events = list(events)
        self.pending = []
        self.methods = []
        self.fallback = fallback

    def request(self, method, params):
        self.methods.append(method)
        if method == "thread/start":
            return {"thread": {"id": "thread"}, "model": "wrong" if self.fallback else params["model"],
                    "reasoningEffort": "high", "instructionSources": []}
        return {"turn": {"id": "turn"}}

    def next_event(self, timeout):
        return self.events.pop(0)


def fake_events(reasoning=900):
    answer = json.dumps(read_json(ROOT / "experiment/tasks/portfolio/expected.json"))
    total = {} if reasoning is None else {"reasoningOutputTokens": reasoning}
    usage = {"method": "thread/tokenUsage/updated", "params": {
        "threadId": "thread", "turnId": "turn",
        "tokenUsage": {"total": total, "last": {"reasoningOutputTokens": 5}}}}
    return [usage, usage, {"method": "item/completed", "params": {"item": {
        "type": "agentMessage", "id": "answer", "phase": "final_answer", "text": answer}}},
        {"method": "turn/completed", "params": {"turn": {"id": "turn", "status": "completed"}}}]


class ExperimentTests(unittest.TestCase):
    def test_new_collections_freeze_the_relocated_inputs_and_code(self):
        settings = {**read_json(ROOT / 'experiment/config/settings.json'), 'benchmark': 'bookstore', 'capture': True}
        with tempfile.TemporaryDirectory() as name:
            output = Path(name)
            save_source(output, sys.executable, settings, make_schedule(settings))
            manifest = read_json(output / 'manifest.json')
            for relative in ['experiment/__main__.py', 'experiment/src/identical.py',
                             'experiment/config/controlled.toml', 'experiment/config/settings.json',
                             'experiment/tasks/portfolio/expected.json', 'experiment/tasks/bookstore/rubric.json']:
                self.assertIn(relative, manifest['source_sha256'])
                self.assertEqual((output / 'source' / relative).read_bytes(), (ROOT / relative).read_bytes())

    def test_bookstore_grading_preserves_partial_credit_without_grading_prose(self):
        rubric = read_json(ROOT / "experiment/tasks/bookstore/rubric.json")
        answer = {**rubric["expected_decisions"], "explanation": "A different phrasing."}
        self.assertEqual(grade_bookstore(json.dumps(answer), rubric)["score"], 4)
        answer["cause"] = "provider_duplicates_delivery"
        result = grade_bookstore(json.dumps(answer), rubric)
        self.assertEqual(result["score"], 3)
        self.assertFalse(result["correct"])
        del answer["test"]
        self.assertEqual(grade_bookstore(json.dumps(answer), rubric)["score"], 2)
        for invalid in ["not JSON", "[]", "null", "42"]:
            self.assertEqual(grade_bookstore(invalid, rubric)["score"], 0)

    def capture(self, client):
        return measure(client, "gpt-6-luna", "high", "test", "test", Path('/private/tmp'), 10)

    def test_reference_and_prompt_match(self):
        problem = read_json(ROOT / "experiment/tasks/portfolio/problem.json")
        prompt_data = json.loads((ROOT / "experiment/tasks/portfolio/prompt.txt").read_text().rsplit("Here is the complete instance:\n", 1)[1])
        self.assertEqual(problem, prompt_data)
        answer, count = solve(problem)
        self.assertEqual(count, 5)
        self.assertTrue(is_correct(json.dumps(answer), read_json(ROOT / "experiment/tasks/portfolio/expected.json")))

    def test_schedule_is_deterministic_balanced_and_paired(self):
        settings = read_json(ROOT / "experiment/config/settings.json")
        schedule = make_schedule(settings)
        self.assertEqual(schedule, make_schedule(settings))
        self.assertEqual(len(schedule), 12)
        self.assertEqual({job['model'] for job in schedule}, {'gpt-6-luna', 'gpt-6.1-sol'})
        self.assertEqual({job['effort'] for job in schedule}, {'low', 'medium', 'high'})
        self.assertEqual(sum(job['auth'] == 'api' for job in schedule[::2]), 3)
        for a, b in zip(schedule[::2], schedule[1::2]):
            self.assertEqual((a['model'], a['effort']), (b['model'], b['effort']))
            self.assertEqual({a['auth'], b['auth']}, {'api', 'chatgpt'})

    def test_cumulative_events_are_not_added(self):
        result = self.capture(FakeClient(fake_events()))
        self.assertEqual(result['reasoning_tokens'], 900)
        self.assertTrue(result['eligible'])

    def test_ten_medium_repeats_make_twenty_balanced_responses(self):
        settings = {**read_json(ROOT / 'experiment/config/settings.json'), 'models': ['gpt-6-luna'],
                    'efforts': ['medium'], 'repeats': 10}
        schedule = make_schedule(settings)
        self.assertEqual(schedule, make_schedule(settings))
        self.assertEqual(len(schedule), 20)
        self.assertEqual(sum(job['auth'] == 'api' for job in schedule), 10)
        self.assertEqual(sum(job['auth'] == 'api' for job in schedule[::2]), 5)
        self.assertEqual({job['repeat'] for job in schedule}, set(range(1, 11)))
        for a, b in zip(schedule[::2], schedule[1::2]):
            self.assertEqual(a['repeat'], b['repeat'])
            self.assertEqual({a['auth'], b['auth']}, {'api', 'chatgpt'})

    def test_both_tasks_cli_preview_covers_the_full_matrix_without_calls(self):
        text = subprocess.check_output([sys.executable, '-B', '-m', 'experiment', 'run',
                                        '--benchmark', 'both', '--repeats', '10'], text=True, cwd=ROOT)
        experiments = json.loads(text.split('\nPreview only:')[0])
        self.assertEqual({e['settings']['benchmark'] for e in experiments}, {'portfolio', 'bookstore'})
        self.assertEqual(sum(len(e['schedule']) for e in experiments), 240)
        for experiment in experiments:
            schedule = experiment['schedule']
            self.assertEqual({r['model'] for r in schedule}, {'gpt-6-luna', 'gpt-6.1-sol'})
            self.assertEqual({r['effort'] for r in schedule}, {'low', 'medium', 'high'})
            self.assertEqual(sum(r['auth'] == 'api' for r in schedule[::2]), 30)

    def test_preflight_closes_both_clients_and_never_starts_a_turn(self):
        settings = read_json(ROOT / 'experiment/config/settings.json')
        clients = [Mock(), Mock()]
        for client in clients:
            client.check_login.return_value = {'type': 'test'}
            client.list_models.return_value = [
                {'model': model, 'supportedReasoningEfforts': [{'reasoningEffort': effort}
                 for effort in settings['efforts']]} for model in settings['models']]
        with patch('run.CodexClient', side_effect=clients):
            preflight('fake-binary', settings)
        for auth, client in zip(['api', 'chatgpt'], clients):
            client.check_login.assert_called_once_with(auth)
            self.assertEqual([c[0] for c in client.mock_calls], ['check_login', 'list_models', 'close'])

    def test_expired_turn_stops_even_if_more_events_are_queued(self):
        client = FakeClient(fake_events())
        with patch('run.time.monotonic', side_effect=[0, 11]), self.assertRaises(TimeoutError):
            self.capture(client)
        self.assertEqual(len(client.events), len(fake_events()))

    def test_summary_keeps_each_repeat_and_uses_all_counts(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            settings = {**read_json(ROOT / 'experiment/config/settings.json'), 'models': ['gpt-6-luna'],
                        'efforts': ['medium'], 'repeats': 2}
            write_json(directory / 'manifest.json', {'codex_version': 'test', 'settings': settings,
                                                     'schedule': make_schedule(settings)})
            runs = []
            for repeat, a, b in [(1, 100, 300), (2, 200, 500)]:
                for auth, tokens in [('api', a), ('chatgpt', b)]:
                    runs.append({'number': len(runs) + 1, 'repeat': repeat, 'model': 'gpt-6-luna',
                                 'effort': 'medium', 'auth': auth, 'reasoning_tokens': tokens,
                                 'eligible': True, 'correct': True})
            write_json(directory / 'runs.json', runs)
            summarize(directory)
            report = (directory / 'report.md').read_text()
            self.assertIn('| 1 | gpt-6-luna | medium | 100 | 300 | 200 |', report)
            self.assertIn('| 2 | gpt-6-luna | medium | 200 | 500 | 300 |', report)
            self.assertIn('| api | 2/2 | 2/2 | 150.0 | 150.0 | 100–200 |', report)
            self.assertIn('| chatgpt | 2/2 | 2/2 | 400.0 | 400.0 | 300–500 |', report)

    def test_missing_is_not_zero(self):
        result = self.capture(FakeClient(fake_events(None)))
        self.assertIsNone(result['reasoning_tokens'])
        self.assertFalse(result['eligible'])
        self.assertEqual(self.capture(FakeClient(fake_events(0)))['reasoning_tokens'], 0)

    def test_fallback_stops_before_a_turn(self):
        client = FakeClient([], fallback=True)
        with self.assertRaises(RuntimeError):
            self.capture(client)
        self.assertEqual(client.methods, ['thread/start'])

    def test_tools_and_rerouting_are_flagged(self):
        for event in [{"method": "item/started", "params": {"item": {"type": "commandExecution"}}},
                      {"method": "model/rerouted", "params": {}}]:
            result = self.capture(FakeClient([event] + fake_events()))
            self.assertFalse(result['eligible'])

    def test_integer_types_and_json_format_are_checked(self):
        self.assertTrue(is_correct('{"value":1}', {'value': 1}))
        for answer in ['{"value":1.0}', '{"value":true}', '```json\n{"value":1}\n```']:
            self.assertFalse(is_correct(answer, {'value': 1}))

    def test_missing_capability_stops_collection(self):
        with self.assertRaises(RuntimeError):
            check_available([], read_json(ROOT / 'experiment/config/settings.json'))

    def test_ambient_keys_are_removed_only_from_the_child(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-value', 'CODEX_API_KEY': 'test-value'}):
            child = codex_environment('chatgpt')
            self.assertNotIn('OPENAI_API_KEY', child)
            self.assertNotIn('CODEX_API_KEY', child)
            self.assertEqual(os.environ['OPENAI_API_KEY'], 'test-value')

    def test_summary_preserves_missing_and_flagged_observations(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            settings = read_json(ROOT / 'experiment/config/settings.json')
            write_json(directory / 'manifest.json', {'codex_version': 'test', 'settings': settings,
                                                     'schedule': make_schedule(settings)})
            write_json(directory / 'runs.json', [
                {'number': 1, 'model': 'gpt-6-luna', 'effort': 'low', 'auth': 'api',
                 'reasoning_tokens': 100, 'eligible': True, 'correct': False},
                {'number': 2, 'model': 'gpt-6-luna', 'effort': 'low', 'auth': 'chatgpt',
                 'reasoning_tokens': 300, 'eligible': True, 'correct': True},
                {'number': 3, 'model': 'gpt-6-luna', 'effort': 'high', 'auth': 'api',
                 'eligible': False, 'status': 'error'}])
            summarize(directory)
            report = (directory / 'report.md').read_text()
            self.assertIn('| 100 | 300 | 200 | False / True |', report)
            self.assertIn('| high | — | — | — |', report)
            self.assertIn('Attempt 3', report)


if __name__ == '__main__':
    unittest.main()
