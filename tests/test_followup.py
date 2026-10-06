"""Check the follow-up accuracy calculation against independent enumeration."""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiment/src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'studies/followup/recovery'))
from analyze_followup import accuracy_distribution, combined_p_value, pooled_accuracy
from common import ROOT
from paired_statistics import distribution
from continue_followup import progress


class FollowupTests(unittest.TestCase):
    def make_segments(self, root):
        original, resumed = root / 'original', root / 'resumed'
        jobs = [{'model': 'gpt-6-luna', 'effort': 'low', 'repeat': repeat, 'auth': auth}
                for repeat in [1, 2] for auth in ['api', 'chatgpt']]
        settings = {'benchmark': 'portfolio'}
        original.mkdir()
        (original / 'plan.json').write_text(json.dumps([{'settings': settings, 'schedule': jobs}]))
        for base, schedule in [(original, jobs), (resumed, jobs[3:])]:
            folder = base / 'portfolio'
            folder.mkdir(parents=True)
            (folder / 'manifest.json').write_text(json.dumps({'settings': settings, 'schedule': schedule}))
            rows = [{**job, 'number': number, 'eligible': True, 'status': 'completed', 'correct': False}
                    for number, job in enumerate(schedule, 1)]
            if base == original:
                rows[-1].update(eligible=False, status='failed', identical_request_verified=True, sent_body_sha256='fixture')
                error = {'body': {'type': 'response.failed', 'response': {'error': {'code': 'server_is_overloaded'}}}}
                (folder / '04-wire.jsonl').write_text(json.dumps(error) + '\n')
                (folder / '04-events.jsonl').write_text('{}\n')
            (folder / 'runs.json').write_text(json.dumps(rows))
        return original, resumed

    def test_segment_resume_retains_incorrect_answers_and_partial_pairs(self):
        with tempfile.TemporaryDirectory() as name:
            original, resumed = self.make_segments(Path(name))
            before = (original / 'portfolio/runs.json').read_bytes()
            plans, completed, failures = progress(original, [resumed])
            self.assertEqual(len(completed['portfolio']), 4)
            self.assertTrue(all(not row['correct'] for _, _, row in completed['portfolio']))
            self.assertEqual(failures[0]['scheduled_number'], 4)
            self.assertEqual(failures[0]['reasoning_tokens'], None)
            self.assertEqual(completed['portfolio'][-1][2]['number'], 1)
            self.assertEqual((original / 'portfolio/runs.json').read_bytes(), before)

    def test_reordered_resume_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            original, resumed = self.make_segments(Path(name))
            path = resumed / 'portfolio/manifest.json'
            manifest = json.loads(path.read_text())
            manifest['schedule'][0]['auth'] = 'api'
            path.write_text(json.dumps(manifest))
            with self.assertRaises(AssertionError):
                progress(original, [resumed])

    def test_matches_exhaustive_first_second_assignments(self):
        pairs = [{'api': {'number': 2*i + (1 if i % 2 else 2), 'correct': a},
                  'chatgpt': {'number': 2*i + (2 if i % 2 else 1), 'correct': b}}
                 for i, (a, b) in enumerate([(True, False), (False, True), (True, True), (False, False)])]
        self.assertEqual(accuracy_distribution(pairs, 6, 3), distribution(pairs, 'correct', 6, 3))

    def test_three_independent_blocks_and_ties(self):
        self.assertEqual(combined_p_value([{2: 1, -2: 1}] * 3, 6), 2 / 8)
        self.assertEqual(combined_p_value([{0: 1}] * 3, 0), 1)
        pairs = [{'api': {'number': 2*i + (1 if i % 2 else 2), 'correct': True},
                  'chatgpt': {'number': 2*i + (2 if i % 2 else 1), 'correct': False}} for i in range(20)]
        observed, weights = accuracy_distribution(pairs, 120, 60)
        expected = 2 * math.comb(100, 50) / math.comb(120, 60)
        self.assertAlmostEqual(combined_p_value([weights], observed), expected)

    def test_reproduces_original_accuracy_p_values(self):
        directory = ROOT / 'studies/initial/data'
        rows = [json.loads(line) for line in (directory / 'records.jsonl').read_text().splitlines()]
        manifest = json.loads((directory / 'manifest.json').read_text())
        old = json.loads((ROOT / 'studies/initial/results/significance.json').read_text())['results']
        expected = {(row['task'], row['model'], row['effort']): row['correct']['p'] for row in old}
        for row in pooled_accuracy([(rows, manifest)]):
            self.assertAlmostEqual(row['p'], expected[row['task'], row['model'], row['effort']])


if __name__ == '__main__':
    unittest.main()
