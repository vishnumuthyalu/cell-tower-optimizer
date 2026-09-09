"""Compare exact ILP vs greedy heuristic."""
import pandas as pd


def compare_results(exact: dict, greedy: dict) -> pd.DataFrame:
    rows = [
        {"method": "Exact (MCLP/ILP)", **{k: v for k, v in exact.items() if k != "selected_indices"}},
        {"method": "Greedy heuristic", **{k: v for k, v in greedy.items() if k != "selected_indices"}},
    ]
    df = pd.DataFrame(rows)
    df["optimality_gap_pct"] = exact["coverage_pct"] - df["coverage_pct"]
    return df