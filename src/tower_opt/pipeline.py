"""End-to-end pipeline: load processed data, run both solvers, evaluate, map."""
import json
import pandas as pd

from .config import DATA_PROCESSED, OUTPUTS
from .coverage import build_coverage_matrix
from .optimize_greedy import greedy_mclp
from .optimize_mclp import solve_mclp_exact
from .evaluate import compare_results
from .visualize import build_map


def run(budget: int, radius_km: float):
    demand_df = pd.read_csv(DATA_PROCESSED / "demand_points.csv")
    candidate_df = pd.read_csv(DATA_PROCESSED / "candidate_sites.csv")
    existing_towers_df = pd.read_csv(DATA_PROCESSED / "existing_towers.csv")

    coverage_matrix = build_coverage_matrix(demand_df, candidate_df, radius_km)
    weights = demand_df["population"].values

    greedy_result = greedy_mclp(coverage_matrix, weights, budget)
    exact_result = solve_mclp_exact(demand_df, candidate_df, radius_km, budget)

    comparison = compare_results(exact_result, greedy_result)

    map_path = build_map(
        demand_df, candidate_df, existing_towers_df,
        exact_result["selected_indices"], radius_km,
    )

    results = {
        "budget": budget,
        "radius_km": radius_km,
        "exact": {k: v for k, v in exact_result.items() if k != "selected_indices"},
        "greedy": {k: v for k, v in greedy_result.items() if k != "selected_indices"},
        "selected_sites_exact": candidate_df.iloc[exact_result["selected_indices"]][["site_id", "lat", "lon"]].to_dict("records"),
        "map_path": str(map_path),
    }
    with open(OUTPUTS / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(comparison.to_string(index=False))
    return results


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--budget", type=int, default=5)
    p.add_argument("--radius", type=float, default=3.0)
    args = p.parse_args()
    run(args.budget, args.radius)