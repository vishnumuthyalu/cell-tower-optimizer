"""Exact solve via spopt's MCLP (ILP under the hood, solved with PuLP/CBC).

Uses the same haversine distance matrix as the greedy heuristic so both
solvers are compared on identical distances. An earlier version reprojected
to EPSG:3857 and used a flat Euclidean radius there, which silently
distorts real-world distance away from the equator -- at Austin's latitude
that shrank the effective coverage radius enough that the "exact" solver
scored worse than greedy, which is impossible for a correctly-posed MCLP.
"""
import time
import pulp
from spopt.locate import MCLP

from .coverage import haversine_matrix


def solve_mclp_exact(demand_df, candidate_df, radius_km: float, p: int):
    cost_matrix = haversine_matrix(
        demand_df["lat"].values, demand_df["lon"].values,
        candidate_df["lat"].values, candidate_df["lon"].values,
        
    )
    demand_weights = demand_df["population"].values

    model = MCLP.from_cost_matrix(
        cost_matrix,
        demand_weights,
        radius_km,
        p_facilities=p,
        name="tower-mclp",
    )

    start = time.time()
    solver = pulp.PULP_CBC_CMD(msg=False)
    model = model.solve(solver)
    runtime = time.time() - start

    selected = [i for i, v in enumerate(model.fac_vars) if v.value() == 1]
    total_weight = float(demand_df["population"].sum())
    covered_weight = total_weight * (model.perc_cov / 100)

    return {
        "selected_indices": selected,
        "coverage_pct": model.perc_cov,
        "covered_weight": covered_weight,
        "total_weight": total_weight,
        "runtime_sec": runtime,
    }