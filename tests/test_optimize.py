import numpy as np
from src.tower_opt.optimize_greedy import greedy_mclp


def test_greedy_picks_highest_weighted_coverage():
    # candidate 0 covers demand [0,1]; candidate 1 covers demand [2]
    coverage = np.array([
        [True, True, False],
        [False, False, True],
    ])
    weights = np.array([10, 10, 5])
    result = greedy_mclp(coverage, weights, p=1)
    assert result["selected_indices"] == [0]
    assert result["coverage_pct"] == 80.0