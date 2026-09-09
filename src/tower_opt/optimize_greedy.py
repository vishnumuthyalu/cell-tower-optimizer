"""Baseline: greedy set-cover-style heuristic for MCLP.
At each step, pick the candidate site that covers the most
currently-uncovered weighted demand. O(p * n_candidates * n_demand)."""
import numpy as np
import time


def greedy_mclp(coverage_matrix: np.ndarray, weights: np.ndarray, p: int):
    n_candidates, n_demand = coverage_matrix.shape
    covered = np.zeros(n_demand, dtype=bool)
    chosen = []
    start = time.time()

    for _ in range(p):
        newly_covered_weight = ((coverage_matrix & ~covered) * weights).sum(axis=1)
        newly_covered_weight[chosen] = -1  # never re-pick
        best = int(np.argmax(newly_covered_weight))
        if newly_covered_weight[best] <= 0:
            break
        chosen.append(best)
        covered |= coverage_matrix[best]

    runtime = time.time() - start
    covered_weight = float(weights[covered].sum())
    total_weight = float(weights.sum())
    return {
        "selected_indices": chosen,
        "coverage_pct": covered_weight / total_weight * 100,
        "covered_weight": covered_weight,
        "total_weight": total_weight,
        "runtime_sec": runtime,
    }