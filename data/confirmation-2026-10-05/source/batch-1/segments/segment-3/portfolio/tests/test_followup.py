"""Check the follow-up accuracy calculation against independent enumeration."""
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from analyze_followup import accuracy_distribution, combined_p_value, pooled_accuracy
from common import ROOT
from paired_statistics import distribution


class FollowupTests(unittest.TestCase):
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
        directory = ROOT / 'data/2026-10-05'
        rows = [json.loads(line) for line in (directory / 'records.jsonl').read_text().splitlines()]
        manifest = json.loads((directory / 'manifest.json').read_text())
        old = json.loads((ROOT / 'reports/2026-10-05/significance.json').read_text())['results']
        expected = {(row['task'], row['model'], row['effort']): row['correct']['p'] for row in old}
        for row in pooled_accuracy([(rows, manifest)]):
            self.assertAlmostEqual(row['p'], expected[row['task'], row['model'], row['effort']])


if __name__ == '__main__':
    unittest.main()
