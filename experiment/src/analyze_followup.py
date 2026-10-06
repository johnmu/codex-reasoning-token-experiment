"""Analyze the fixed follow-up and pooled accuracy without any model calls."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from analyze import analyze
from common import ROOT, file_hash, read_json, write_json, relative_link
from public_audit import verify


def accuracy_distribution(pairs, block_pairs, api_first):
    """Count all valid first/second assignments without listing each one."""
    observed = sum(pair['api']['correct'] - pair['chatgpt']['correct'] for pair in pairs)
    # Track (API-first assignments, correctness difference) and their counts.
    states = {(0, 0): 1}
    for pair in pairs:
        first, second = sorted(pair.values(), key=lambda row: row['number'])
        difference = first['correct'] - second['correct']
        following = defaultdict(int)
        for (selected, score), count in states.items():
            following[selected + 1, score + difference] += count
            following[selected, score - difference] += count
        states = following
    remaining = block_pairs - len(pairs)
    weights = defaultdict(int)
    for (selected, score), count in states.items():
        needed = api_first - selected
        if 0 <= needed <= remaining:
            weights[score] += count * math.comb(remaining, needed)
    assert sum(weights.values()) == math.comb(block_pairs, api_first)
    return observed, dict(weights)


def combined_p_value(blocks, observed):
    """Combine independent batch distributions, then count both tails."""
    combined = {0: 1}
    for block in blocks:
        following = defaultdict(int)
        for left, left_count in combined.items():
            for right, right_count in block.items():
                following[left + right] += left_count * right_count
        combined = following
    extreme = sum(count for score, count in combined.items() if abs(score) >= abs(observed))
    return extreme / sum(combined.values())


def pooled_accuracy(datasets):
    """Keep each collection/task/batch order constraint separate."""
    conditions = defaultdict(list)
    for rows, manifest in datasets:
        for batch in manifest['batches']:
            for task in batch['tasks']:
                schedule = task['schedule']
                block_pairs = len(schedule) // 2
                api_first = sum(job['auth'] == 'api' for job in schedule[::2])
                pairs = defaultdict(lambda: defaultdict(dict))
                for row in rows:
                    if row['batch'] == batch['name'] and row['task'] == task['task']:
                        pairs[row['model'], row['effort']][row['repeat']][row['auth']] = row
                for (model, effort), repeats in pairs.items():
                    paired = list(repeats.values())
                    assert all(set(pair) == {'api', 'chatgpt'} for pair in paired)
                    observed, weights = accuracy_distribution(paired, block_pairs, api_first)
                    conditions[task['task'], model, effort].append({
                        'observed': observed, 'weights': weights, 'pairs': len(paired),
                        'api_correct': sum(pair['api']['correct'] for pair in paired),
                        'chatgpt_correct': sum(pair['chatgpt']['correct'] for pair in paired)})
    results = []
    for (task, model, effort), blocks in sorted(conditions.items()):
        p = combined_p_value([block['weights'] for block in blocks], sum(block['observed'] for block in blocks))
        results.append({'task': task, 'model': model, 'effort': effort,
                        'responses_per_sign_in': sum(block['pairs'] for block in blocks),
                        'api_correct': sum(block['api_correct'] for block in blocks),
                        'chatgpt_correct': sum(block['chatgpt_correct'] for block in blocks),
                        'p': p, 'bonferroni_36_outcomes_3_looks': min(1., p * 36 * 3)})
    return results


def followup(data, output):
    plan = read_json(ROOT / 'studies/followup/plan/schedule.json')
    baseline = verify(ROOT / 'studies/initial/data')
    new = verify(data)
    assert baseline[1]['records_sha256'] == plan['baseline_records_sha256']
    assert new[1]['responses'] == plan['responses']
    assert len(new[1]['batches']) == 1
    for task, expected in zip(new[1]['batches'][0]['tasks'], plan['experiments']):
        assert task['settings'] == expected['settings'] and task['schedule'] == expected['schedule']
        assert task['request_body_sha256'] == expected['request_body_sha256']
        assert task['codex_sha256'] == plan['codex_sha256']
    assert len(new[1]['batches'][0]['tasks']) == len(plan['experiments'])
    failures = read_json(data / 'runtime-errors.json')
    assert file_hash(data / 'runtime-errors.json') == new[1]['runtime_errors_sha256']
    assert failures['failures'] == read_json(ROOT / 'studies/followup/plan/runtime-errors.json')['failures']
    assert failures['completed_responses'] == 480
    assert failures['total_attempts'] == 480 + len(failures['failures'])
    analyze(data, output / 'new-batch', looks=1)
    primary = read_json(output / 'new-batch/significance.json')
    pooled = pooled_accuracy([baseline, new])
    assert len(pooled) == 12 and all(row['responses_per_sign_in'] == 40 for row in pooled)
    write_json(output / 'pooled-accuracy.json', {'scope': 'Exploratory; three collection blocks and three significance looks',
                                               'correction_factor': 108, 'results': pooled})
    plan_link = relative_link(output, ROOT / 'studies/followup/plan/README.md')
    amendment_link = relative_link(output, ROOT / 'studies/followup/plan/amendments.md')
    failure_link = relative_link(output, data / 'runtime-errors.json')
    lines = ['# Results of the fixed 480-response follow-up', '',
             f'[Plan published before collection]({plan_link}). '
             'The original 480 responses are unchanged; this batch adds 480 new responses.', '',
             '## New batch: completed-response comparison', '',
             f"This batch required {failures['total_attempts']} attempts. {len(failures['failures'])} subscription requests "
             'failed with a server-capacity error and were manually repeated after inspection. '
             f'[The runtime amendment]({amendment_link}) and '
             f'[failure evidence]({failure_link}) disclose the interruptions. '
             'These statistics describe completed responses and do not measure availability per attempt. '
             'The deviations limit interpretation as confirmation of the original study.', '',
             'The exact paired tests use only the new answers. Holm correction covers all 36 '
             'task/model/level/outcome comparisons, with one final look.', '',
             '| Outcome | Differences significant at 5% |', '|---|---:|']
    for metric in ['reasoning_tokens', 'correct', 'seconds']:
        count = sum(row[metric]['holm_all_looks'] < .05 for row in primary['results'])
        lines.append(f'| {metric} | {count} |')
    lines += ['', '[New-batch answers, token counts, latency and statistics](new-batch/report.md)', '',
              '## Pooled accuracy: exploratory', '',
              'Each row includes 40 responses per sign-in from all three batches. The exact test '
              'retains each batch’s order constraints. The planned conservative correction is '
              '36 outcomes × 3 significance looks. This pooled analysis is not independent confirmation.', '',
              '| Task | Model | Level | API correct | ChatGPT correct | Raw p | Corrected p |',
              '|---|---|---|---:|---:|---:|---:|']
    for row in pooled:
        lines.append(f"| {row['task']} | {row['model']} | {row['effort']} | {row['api_correct']}/40 | "
                     f"{row['chatgpt_correct']}/40 | {row['p']:.6g} | {row['bonferroni_36_outcomes_3_looks']:.6g} |")
    lines += ['', '[Exact pooled accuracy results](pooled-accuracy.json). These two fixed tasks '
              'do not establish a general capability difference or the cause of any discrepancy.']
    (output / 'report.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'new_accuracy_significant': sum(row['correct']['holm_all_looks'] < .05 for row in primary['results']),
                      'pooled_accuracy_significant': sum(row['bonferroni_36_outcomes_3_looks'] < .05 for row in pooled)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', nargs='?', type=Path, default=ROOT / 'studies/followup/data')
    parser.add_argument('--output', type=Path, default=ROOT / 'output/reports/followup')
    args = parser.parse_args()
    followup(args.data, args.output)
