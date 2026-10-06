"""Exact paired randomization and Holm correction; standard library only."""
import bisect
import itertools
import math
from collections import defaultdict


def distribution(pairs, metric, block_pairs, api_first):
    observed, differences = 0, []
    for pair in pairs:
        observed += pair["api"][metric] - pair["chatgpt"][metric]
        first, second = sorted(pair.values(), key=lambda row: row["number"])
        differences.append(first[metric] - second[metric])
    weights = defaultdict(int)
    remaining = block_pairs - len(pairs)
    for signs in itertools.product([-1, 1], repeat=len(pairs)):
        needed = api_first - signs.count(1)
        if 0 <= needed <= remaining:
            score = sum(sign * difference for sign, difference in zip(signs, differences))
            weights[score] += math.comb(remaining, needed)
    assert sum(weights.values()) == math.comb(block_pairs, api_first)
    return observed, weights


def tail_probability(blocks, observed):
    """Combine one or two independent batch blocks using cumulative weights."""
    assert 1 <= len(blocks) <= 2, "Analyze more than two batches separately."
    if abs(observed) < 1e-10:
        return 1.
    first = blocks[0]
    second = blocks[1] if len(blocks) == 2 else {0: 1}
    scores, cumulative = sorted(second), [0]
    for score in scores:
        cumulative.append(cumulative[-1] + second[score])
    extreme = 0
    for score, weight in first.items():
        lower = bisect.bisect_right(scores, -abs(observed) - score + 1e-10)
        upper = bisect.bisect_left(scores, abs(observed) - score - 1e-10)
        extreme += weight * (cumulative[lower] + cumulative[-1] - cumulative[upper])
    return extreme / (sum(first.values()) * cumulative[-1])


def holm(values):
    adjusted, previous = [0.] * len(values), 0.
    for rank, index in enumerate(sorted(range(len(values)), key=values.__getitem__)):
        previous = max(previous, min(1., (len(values) - rank) * values[index]))
        adjusted[index] = previous
    return adjusted
